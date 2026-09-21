# RAG 知识库问答系统 — 完整实现文档

---

## 一、项目文件清单

```
C:\Users\Azathoth\RAG-project\
├── rag_core.py              # RAG 核心逻辑：文档加载、切分、向量化、检索、问答链、多模型切换
├── app.py                   # Streamlit 完整界面：模型选择、一键下载、来源展示
├── app_simple.py            # Streamlit 简化界面：初始化按钮、提问框、回答展示
├── knowledge_base/          # 知识库原文目录，放 .md/.txt/.pdf 文档
│   ├── 人工智能与大模型基础.md      # 内置 19 份文档，约 6 万字（切分后 96 个文本块）：
│   ├── 机器学习与深度学习实践.md    #   AI/大模型、11 种编程语言、前端、软件工程、
│   ├── Rust语言基础.md              #   Linux/网络、容器与云原生部署、数据结构与算法
│   └── ...（共 19 份）
├── data/
│   └── chroma_db/           # ChromaDB 持久化存储（向量+原文，自动生成）
├── .env.example             # 环境变量示例（DeepSeek API Key，可复制为 .env）
├── .venv/                   # Python 虚拟环境（uv 创建，Python 3.14.7）
└── requirements.txt         # 依赖清单（仅供参考，实际用 uv 安装）
```

---

## 二、完整数据流

### 阶段 1：文档入库（初始化时执行一次）

```
knowledge_base/*.md/*.txt/*.pdf
        │
        ▼
  ① load_documents()          rag_core.py 第 552-587 行
  │  用 DirectoryLoader + TextLoader 读 .md/.txt
  │  用 PyPDFLoader 读 .pdf
  │  返回 List[Document]
  │
  ▼
  ② split_documents()         rag_core.py 第 589-601 行
  │  用 RecursiveCharacterTextSplitter
  │  chunk_size=800, chunk_overlap=100
  │  分隔符: ["\n\n", "\n", "。", "！", "？", ".", " ", ""]
  │  返回 List[Document]（切块后）
  │
  ▼
  ③ build_vectorstore()       rag_core.py 第 603-629 行（重建前会清空旧集合）
  │  调用 OllamaEmbeddings(model="nomic-embed-text")
  │  → 每个文本块发到 localhost:11434 生成 768 维向量
  │  用 Chroma.from_documents() 存入
  │  persist_directory = data/chroma_db/
  │  （ChromaDB 自动持久化到磁盘）
  │
  ▼
  ④ 创建混合检索器            rag_core.py 第 686-697 行
  │  向量检索 top-6 + BM25 关键词检索 top-6
  │  用 RRF（倒数排名融合）合并两路结果，再按"问题关键词覆盖度"排序取 top-3
  │  ← HybridRetriever，rag_core.py 第 269-383 行
  │
  ▼
  ⑤ build_rag_chain()        rag_core.py 第 645-660 行
     构建 LCEL 管道：
     {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | self.llm  ← 当前选择的模型（本地 Qwen2.5-3B/7B 或 DeepSeek API）
     存入 self._rag_chain
```

**触发方式：** 在 `app.py` 或 `app_simple.py` 中点击「🚀 初始化 RAG 系统」按钮 → 调用 `rag.initialize()`

### 阶段 2：问答（每次提问执行）

```
用户在网页输入问题
        │
        ▼
  界面调用: rag.query(question)
        │
        ▼
  ① self._rag_chain.invoke(question)    rag_core.py 第 712 行
  │
  │  LCEL 管道自动执行以下步骤：
  │
  │  1) question 字符串传入管道
  │  2) retriever 自动用 OllamaEmbeddings 把 question 转成 768 维向量
  │  3) 向量检索 + BM25 关键词检索各取 top-6，RRF 融合并按关键词覆盖度排序取 top-3
  │  4) 把 3 个文档块拼接成 {context} 字符串
  │  5) 按回答模式选模板填充（rag_core.py 第 650 行，模板定义在第 91-113 行）：
  │
  │     智能问答："优先依据知识库内容回答；知识库无关就用你自己的知识回答，并标注【通用知识】"
  │     严格知识库："根据以下上下文回答问题。如果上下文没有相关信息，请说未找到相关答案"
  │      上下文：{拼接的文档块}
  │      问题：{用户问题}
  │
  │
  │  6) 当前选择的对话模型接收完整 prompt
  │     → 本地模型：发到 localhost:11434 的 Ollama 服务，在 GPU 上推理
  │     → DeepSeek：通过 HTTPS 调用 api.deepseek.com（需要 API Key）
  │     → 返回 AIMessage 对象
  │
  ▼
  ② response.content           rag_core.py 第 713 行
  │  提取模型生成的文本
  │
  ▼
  ③ self._retriever.retrieve_with_scores(question)  rag_core.py 第 719 行（带相关度信息的混合检索）
  │  单独再检索一次，获取参考来源文档（用于展示给用户）
  │
  ▼
  ④ 返回 dict                  rag_core.py 第 744-750 行
  │  {
  │    "question": "用户问题",
  │    "model": "回答所用模型（如 Qwen2.5-3B）",
  │    "mode": "smart / kb_only",
  │    "answer": "AI 回答",
  │    "used_knowledge_base": True,   # 回答是否真的用了知识库
  │    "sources": [{content, metadata, score, relevance}, ...],  # top-3 来源 + 相关度
  │    "source_count": 3
  │  }
  │
  ▼
  app.py / app_simple.py
  st.markdown(result["answer"])      ← 显示回答（【通用知识】前缀会换成提示条）
  render_sources(result)             ← 按相关度显示来源：高/中 列为「来源 1/2/3」，
                                        低 相关折叠进「其他检索到的片段」，
                                        未用知识库时提示「未使用知识库内容」
```

---

## 三、每个工具的具体角色

| 工具 | 角色 | 具体职责 |
|------|------|---------|
| **Ollama** | 本地模型运行时 | 在 localhost:11434 提供模型推理服务。管理 qwen2.5:3b / qwen2.5:7b、nomic-embed-text 等模型的加载、GPU 调度、推理响应 |
| **Qwen2.5-3B / 7B** | 本地对话模型 | 接收"上下文+问题"的 prompt，生成自然语言回答。3B（约 2GB）速度快，7B（约 4.7GB）回答质量更高，可在界面中随时切换 |
| **DeepSeek API** | 外接对话模型 | 通过 HTTPS 调用 api.deepseek.com 的 deepseek-chat（V3），能力最强，需要 API Key 和网络。实现见 `DeepSeekChat` 适配器（rag_core.py 第 402-450 行） |
| **nomic-embed-text** | Embedding 模型 | 把文本（文档块 / 用户问题）转成 768 维浮点向量。137M 参数，用于相似度计算。注意它对中文排序能力偏弱，所以需要 BM25 关键词检索兜底 |
| **BM25（rank-bm25）** | 关键词检索 | 第二路召回：用中英混合分词（中文二元切分）计算关键词相关度，再用 RRF 与向量结果融合，弥补中文纯向量检索的短板。同时统计每个词的 IDF 权重，用来计算「片段覆盖了问题的多少关键内容」。实现见 `HybridRetriever`（rag_core.py 第 269-383 行） |
| **LangChain** | 编排框架 | 提供 DocumentLoader（读文件）、TextSplitter（切块）、LCEL 管道（串联检索→提示词→模型）、PromptTemplate（模板）等组件，把上述工具串成完整流程 |
| **ChromaDB** | 向量数据库 | 存储文档块的向量 + 原文 + 元数据。支持持久化到磁盘（data/chroma_db/），提供相似度检索接口。初始化时建库，问答时检索 |
| **回答模式** | 问答策略 | 智能问答（默认）：知识库相关就跟知识库答、无关就用模型自身知识答（标注【通用知识】）；严格知识库：只依据知识库，没有就说"未找到相关答案"。定义见 `PROMPT_TEMPLATES`（rag_core.py 第 91-113 行） |
| **Streamlit** | Web 界面 | 提供 Python Web 应用，用户在浏览器点击初始化、输入问题、查看回答。管理 session_state 保持 RAG 对象存活 |

**调用关系图：**
```
Streamlit (app_simple.py)
    │ 调用
    ▼
RAGSystem (rag_core.py)
    │ 使用
    ▼
LangChain LCEL 管道
    ├──→ OllamaEmbeddings ──→ Ollama ──→ nomic-embed-text（向量化）
    ├──→ ChromaDB（存储 + 检索向量）
    └──→ 对话模型（界面可切换）
           ├── ChatOllama ──→ Ollama ──→ qwen2.5:3b / 7b（本地生成回答）
           └── DeepSeekChat ──→ api.deepseek.com ──→ deepseek-chat（外接 API 回答）
```

> ⚠️ **纠正：** 你提到的 "bge-m3" 实际上**没有用到**。当前项目用的 Embedding 模型是 **nomic-embed-text**，不是 bge-m3。bge-m3 是另一个流行的中文 Embedding 模型，但本项目中并未安装或使用。

---

## 四、关键代码位置

以下所有位置均基于 `rag_core.py`，行号与当前文件一致：

| 逻辑环节 | 文件 | 行号 | 函数/变量 |
|---------|------|------|----------|
| 文档加载 | rag_core.py | 552-587 | `load_documents()` — DirectoryLoader 读 .md/.txt，PyPDFLoader 读 .pdf |
| 文本切分 | rag_core.py | 589-601 | `split_documents()` — RecursiveCharacterTextSplitter，chunk_size=800，overlap=100 |
| 向量化 | rag_core.py | 545-551 | `embeddings` 属性 — `OllamaEmbeddings(model="nomic-embed-text")` |
| 存入 Chroma | rag_core.py | 609-625 | `Chroma.from_documents(embedding=..., persist_directory=...)` — 向量+原文写入磁盘 |
| 中文分词 | rag_core.py | 248-258 | `tokenize_for_bm25()` — 英文单词 + 中文二元切分（无需分词库） |
| 问题实词提取 | rag_core.py | 259-268 | `extract_query_terms()` — 去掉"什么/怎么/区别"等疑问词并去重 |
| 关键词权重 | rag_core.py | 297-303 | `_term_weight()` — IDF 权重：越冷门的词越能说明主题，库里没有的词忽略 |
| 片段覆盖度 | rag_core.py | 304-328 | `_coverage()` — 标题/文件名命中算满分，正文命中打 0.65 折 |
| 检索（混合） | rag_core.py | 269-383 | `HybridRetriever` — 向量 top-6 + BM25 top-6，RRF 融合后按覆盖度排序取 top-3 |
| 检索排序 | rag_core.py | 330-375 | `_rank_documents()` — 先按覆盖度、再按 RRF 分数排序 |
| 创建检索器 | rag_core.py | 686-697 | `initialize()` 中构造 `HybridRetriever(vectorstore=..., documents=...)` |
| 拼提示词 | rag_core.py | 645-650 | 按 `answer_mode` 从 `PROMPT_TEMPLATES`（第 91-113 行）选模板 → `ChatPromptTemplate.from_template()` |
| 调用对话模型 | rag_core.py | 653-657 | LCEL 管道 `{"context": retriever, "question": RunnablePassthrough()} \| prompt \| self.llm` |
|  | rag_core.py | 510-516 | `llm` 属性 — 按当前模型懒加载（`create_llm()`） |
| 模型选择/切换 | rag_core.py | 505-531 | `model_spec` / `set_model()` — 切换模型不重建向量库 |
| 回答方式切换 | rag_core.py | 533-543 | `set_answer_mode()` — 智能问答 / 严格知识库，只重建问答链 |
| 模型清单 | rag_core.py | 127-149 | `MODEL_REGISTRY` — Qwen2.5-3B / 7B / DeepSeek 三个可选模型 |
| 返回回答 | rag_core.py | 712-713 | `response = self._rag_chain.invoke(question)` → `answer = response.content` |
|  | rag_core.py | 744-750 | 返回 `{"answer": answer, "model": ..., "mode": ..., "used_knowledge_base": ..., "sources": [...], "source_count": ...}` |
| 来源相关度 | rag_core.py | 385-397 | `source_relevance()` / `relevance_label()` — 0.85×覆盖度 + 0.15×向量排名 → 高 / 中 / 低 |

---

## 五、重点理解的 5 个核心问题

### Q1: chunk_size 为什么设成 800？

**答：** 现在用 800 字符（`chunk_overlap=100`）。最初设 500 时实测发现一个致命问题：`## 4. 文件操作` 这样的**小节标题会和它下面的代码被拆到两个块里**，检索时「文件」关键词落在标题块、代码落在另一个块，模型拿不到完整信息就会回答「未找到相关答案」。改成 800 字符后，一个 800 字以内的小节基本能完整落在一个块里；同时保留 100 字符重叠，确保边界处的信息不丢。太大（如 2000）会让一个块混入多个主题、降低检索精度，太小（如 200）则语义不完整。

### Q2: top_k 设成 2 会怎么影响结果？

**答：** 现在 `k=3`，而且是**混合检索**：先用向量检索召回 6 个候选、再用 BM25 关键词检索召回 6 个候选，两路结果用 RRF（倒数排名融合）合并后取前 3 个交给模型。之所以不能只靠向量：实测 nomic-embed-text 对中文排序很弱——问「如何处理文件读写？」时，真正含文件操作代码的块被排到了最后一名，模型自然答「未找到」。加入 BM25 后，中文关键词（文件、异常、列表推导式）能被准确命中，实测这三类问题都能正确回答。k 值可在 `rag_core.py` 的 `RETRIEVAL_K` 调整，知识库越大可以适当调大。

### Q3: 为什么用 nomic-embed-text 而不是 OpenAI Embeddings？

**答：** 三个原因：① **完全免费**，跑在本地 GPU 上，不花一分钱；② **隐私安全**，文档内容不离开你的电脑；③ **离线可用**，断网也能跑。代价是质量略低于 OpenAI text-embedding-3-large，但对于个人知识库完全够用。nomic-embed-text 输出 768 维向量，支持 8192 token 上下文，是开源 Embedding 模型里的优秀选择。

### Q4: temperature=0.1 意味着什么？为什么这么低？

**答：** temperature 控制模型输出的随机性。0 = 最确定性（几乎总输出相同答案），1 = 最随机（更有创意但可能跑题）。RAG 问答系统要求**忠实于知识库内容**，不希望模型"发挥创意"编造答案，所以设 0.1（接近确定性，但保留极小变化空间避免死板）。如果是写诗或聊天，可以设 0.7-1.0。

### Q5: LCEL 管道 `{"context": retriever, "question": RunnablePassthrough()} | prompt | llm` 具体在做什么？

**答：** 这是 LangChain 的链式表达式（LCEL），用 `|` 管道符串联组件，类似 Unix 管道：
1. 左边的 dict `{"context": retriever, "question": RunnablePassthrough()}` — 接收用户输入的 question 字符串，`retriever` 自动检索并填入 `context`，`RunnablePassthrough()` 把原始 question 原样传入 `question` 字段
2. `| prompt` — 把 context 和 question 填入提示词模板的 `{context}` 和 `{question}` 占位符
3. `| llm` — 把填好的完整 prompt 发给 ChatOllama 模型，生成回答

等价于传统写法的：先检索 → 手动拼 prompt → 调用模型，但 LCEL 用一行代码就搞定了，且支持异步、流式、批量。

### Q6: 「智能问答」和「严格知识库」两种回答方式有什么区别？

**答：** 区别在提示词模板（`PROMPT_TEMPLATES`，rag_core.py 第 91-113 行）：
- **智能问答（默认）**：告诉模型"知识库内容相关就依据它回答；无关就用你自己的知识回答，并在开头标注【通用知识】"。这样既能用知识库答疑，也能像普通聊天一样问天气、问常识、让模型写文案。
- **严格知识库**：告诉模型"上下文没有相关信息就回答未找到相关答案"。适合答辩/演示场景——保证每句话都有知识库依据，不会自己发挥。

两者在界面上随时切换（`set_answer_mode()`），只重建问答链、不重建向量库，切换是秒级的。界面还会把【通用知识】标注换成一条提示，明确区分"来自知识库"和"来自模型自身知识"。

### Q7: 参考来源的「相关度」是怎么算的？

**答：** 分三步算：① **提实词**——把问题切成中英混合词（英文按单词、中文按二元切分），去掉「什么 / 怎么 / 区别 / 介绍」这类疑问词与客套词，剩下的才是真正的关键词；② **算权重**——每个词按 IDF 给权重，越冷门的词越能说明主题（问「Transformer 架构」时 transformer 的权重远高于「架构」），知识库里从没出现过的词直接不参与计算；③ **算覆盖**——看片段覆盖了多少这些关键词：出现在**小标题或文件名**里算满分，只出现在正文里打 0.65 折。

最终 相关度 = 0.85 × 覆盖度 + 0.15 × 向量排名得分（向量第 1 名得 1.0、第 2 名 0.5……），≥0.5 标「高」、≥0.3 标「中」、其余「低」。检索排序用的是同一套覆盖度（先按覆盖度、再按 RRF 排名），保证交给模型的 3 个片段最贴题。

界面只把「高 / 中」的片段作为参考来源展示（按相关度排序），「低」的片段折叠到「其他检索到的片段」里。之所以不用「BM25 得分 ÷ 本次最高分」这种简单归一化：那样任何问题都会有一个"满分"片段，哪怕它命中的只是「架构」「什么」这类通用词，于是就会出现「来源和回答无关、而且每次都不变」的假象。之所以不直接用向量距离：本项目用的 nomic-embed-text 对中文区分度很差（实测问"文件读写"时相关片段甚至排最后），关键词覆盖度对中文问题灵敏得多。另外，智能问答模式下如果模型回答的是知识库以外的内容，界面会直接提示「未使用知识库内容」，不再拿无关片段充当来源。

---

## 六、面试模拟口述稿（约 2 分钟）

> 我做了一个基于本地部署的 RAG 知识库问答系统。简单来说，你把文档丢进去，它就能基于这些文档回答你的问题，而不是凭空编。
>
> 技术栈是 LangChain + Ollama + ChromaDB + Streamlit。
>
> 整个流程分两步。
>
> **第一步是文档入库。** 我把 markdown、txt、pdf 文档放在 knowledge_base 目录里，系统会用 LangChain 的 DirectoryLoader 把它们读进来，然后用 RecursiveCharacterTextSplitter 切成 800 字符的小块，每块之间有 100 字符重叠防止信息断裂。切好之后，每个文本块会通过 Ollama 调用 nomic-embed-text 模型转成一个 768 维的向量，最后存到 ChromaDB 这个本地向量数据库里。这一步只在初始化时做一次，之后会持久化在磁盘上。
>
> **第二步是问答。** 用户在 Streamlit 网页上输入一个问题，系统会先用同样的 nomic-embed-text 把问题也转成向量，然后在 ChromaDB 里做向量相似度检索，同时用 BM25 做关键词检索，两路结果用 RRF 融合，再按关键词覆盖度排序找出最相关的 3 个文档块。这 3 个块和用户的问题一起拼成一个提示词，发给本地的 qwen2.5 3B 模型来生成回答。模型只看检索到的上下文来回答，如果知识库里没有就说不找到，不会编造。
>
> 整个系统的特点是本地运行为主，不需要联网，不花 API 费用，文档数据也不离开我的电脑。模型跑在我的 RTX 4060 上，回答速度几秒钟。系统还支持在界面上切换对话模型：可以选本地 Qwen2.5-3B 或 7B，也可以接入 DeepSeek API 做外接推理，在速度和回答质量之间灵活取舍。

---

## 附：当前实现的不完整之处

| 问题 | 说明 |
|------|------|
| ✅ 混合检索 + 覆盖度排序 | 自研 `HybridRetriever`（不依赖被移除的 EnsembleRetriever）：向量 top-6 + BM25 top-6，RRF 融合后按「IDF 加权关键词覆盖度」排序取 top-3，既提升中文命中率，也避免通用词把无关片段顶上来 |
| ✅ 知识库覆盖 AI + 多语言 | 内置 19 份文档（约 6 万字 / 96 个文本块）：人工智能与大模型、机器学习与深度学习实践、Python/Java/JavaScript/TypeScript/Go/C++/C#/Rust/PHP/Kotlin/Swift/SQL、HTML/CSS/React/Vue、软件工程与开发流程、Linux、网络与 HTTP、Docker/K8s 容器部署、数据结构与算法 |
| ❌ 没有 rerank | 检索到的 top-3 文档没有经过重排序（rerank），排序质量依赖向量相似度 + BM25 融合结果 |
| ✅ 参考来源按相关度展示 | 只把与问题相关的片段（高 / 中）列为来源并排序，无关片段折叠；模型用自身知识回答时明确提示「未使用知识库内容」 |
| ✅ 两种回答模式 | 「智能问答」（知识库优先，其他问题用模型知识回答并标注【通用知识】）与「严格知识库」（只说知识库内容）可在界面切换，切换不需要重建向量库 |
| ✅ 多模型可切换 | 已支持本地 Qwen2.5-3B/7B 与外接 DeepSeek API，在界面中实时切换（`MODEL_REGISTRY` + `set_model()`），切换模型不需要重建向量库 |
内部| ❌ 没有对话记忆 | 当前每次提问都是独立的，不会记住上一轮的对话内容 |
| ❌ 向量库没有增量更新 | 每次添加新文档需要清除缓存重新初始化，不能增量追加 |
| ⚠️ Chroma 用的是社区版 | 代码用的是 `langchain_community.vectorstores.Chroma`（已标记弃用），应该迁移到 `langchain_chroma.Chroma` |
