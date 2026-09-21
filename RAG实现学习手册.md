# RAG 知识库问答系统 · 完整学习手册

> 项目位置：`C:\Users\Azathoth\RAG-project`
> 学完能做到：说清每个文件、每个函数在干什么；白板画出数据流；从零再写一遍；被追问 20 个问题不慌。

---

## 0. 学习路线（照着顺序走）

| 阶段 | 做什么 | 花多久 | 对应章节 |
|------|--------|--------|----------|
| ① 跑起来 | 启动 Ollama、初始化、问 3 个问题 | 15 分钟 | 第二章 |
| ② 看懂骨架 | 读 `examples/minimal_rag.py`（80 行含注释） | 20 分钟 | 第六章 6.3 |
| ③ 读正式代码 | 按「逐模块精讲」顺序读 `rag_core.py` | 60 分钟 | 第四章 |
| ④ 理解取舍 | 记住「为什么这么做」的 12 个决策 | 30 分钟 | 第五章 |
| ⑤ 复述练习 | 用口述稿讲一遍，卡壳的地方回头补 | 30 分钟 | 第七章 |
| ⑥ 自测 | 做第九章的 20 道自测题 | 20 分钟 | 第九章 |

**一条铁律：** 讲不清的模块，就去改它一个参数、重跑一次、观察输出变化。改参数是理解 RAG 最快的方式。

---

## 一、RAG 到底是什么

### 1.1 一句话

**RAG = 让大模型「开卷考试」**：先从你的资料库里检索出相关段落，再把段落和问题一起交给模型，让它照着资料回答。

### 1.2 为什么需要它

大模型有三个天生的毛病：

| 毛病 | 表现 | RAG 怎么解决 |
|------|------|-------------|
| 知识有截止日期 | 问最新的事它不知道 | 资料随时更新，不用重训模型 |
| 会一本正经地编（幻觉） | 问不熟悉的领域它瞎编 | 限定「依据检索到的资料回答」 |
| 不知道你的私有数据 | 问公司内部文档答不上来 | 把私有文档放进知识库即可 |

### 1.3 RAG 和微调的区别（常被问）

| 维度 | RAG（本项目） | 微调（Fine-tuning） |
|------|--------------|-------------------|
| 干什么 | 外挂知识，回答时现查 | 改模型参数，把知识"背进去" |
| 更新知识 | 换文档 + 重建索引，几分钟 | 重新训练，几小时到几天 |
| 成本 | 一台 4060 就能跑 | 需要显存与训练数据 |
| 适合 | 文档问答、知识频繁更新 | 固定风格、固定格式、领域术语 |
| 缺点 | 依赖检索质量 | 容易遗忘旧能力、难以溯源 |

---

## 二、系统全景

### 2.1 三层架构

```
┌─────────────────────────────────────────────────────────────┐
│  界面层   app.py（Streamlit，421 行）                         │
│  模型下拉框 · 回答方式单选 · 知识库状态 · 上传文档 · 来源展示   │
└───────────────────────────┬─────────────────────────────────┘
                            │ 调用
┌───────────────────────────▼─────────────────────────────────┐
│  核心层   rag_core.py（907 行）                               │
│                                                             │
│  入库：load_documents → split_documents → build_vectorstore   │
│  检索：HybridRetriever（向量 top-6 ＋ BM25 top-6 → RRF → top-3）│
│  生成：build_rag_chain（LCEL：检索 → 提示词 → 模型）           │
│  对外：RAGSystem.initialize() / query() / set_model()         │
└──────────┬────────────────────────────────┬─────────────────┘
           │                                │
┌──────────▼───────────┐        ┌───────────▼─────────────────┐
│  存储层               │        │  模型层                      │
│  knowledge_base/*.md  │        │  Ollama（本地 11434 端口）    │
│  data/chroma_db/      │        │   ├ qwen2.5:3b  对话         │
│  （ChromaDB 持久化）   │        │   ├ qwen2.5:7b  对话         │
│  内存中的 BM25 索引    │        │   └ nomic-embed-text 向量化  │
│                      │        │  DeepSeek API（外接，可选）    │
└──────────────────────┘        └─────────────────────────────┘
```

### 2.2 组件清单（含本项目实测版本）

| 组件 | 版本 | 角色 | 不装会怎样 |
|------|------|------|-----------|
| Python | 3.14.7 | 运行环境 | — |
| Ollama | 0.34.0 | 本地模型运行时 | 本地模型全不可用 |
| qwen2.5:3b | ~2GB | 默认对话模型 | 问答不了（可用 DeepSeek 代替） |
| qwen2.5:7b | ~4.7GB | 更强的对话模型 | 只在选它时需要 |
| nomic-embed-text | ~274MB | 向量化模型（768 维） | 建库和检索全失效 |
| LangChain | 1.4.0 | 编排框架 | — |
| langchain-community | 0.4.2 | 文档加载 + Chroma 封装 | — |
| langchain-ollama | 1.1.0 | 对接 Ollama 的对话/嵌入 | — |
| langchain-text-splitters | 1.1.2 | 文本切分 | — |
| ChromaDB | 1.5.9 | 向量数据库（本地持久化） | 每次都要重建索引 |
| rank-bm25 | 0.2.2 | 关键词检索 | 退化为纯向量检索 |
| pypdf | 6.18.1 | 读 PDF | 不能放 PDF |
| openai | 3.13.0 | 调 DeepSeek（OpenAI 兼容接口） | 不能用 DeepSeek |
| Streamlit | 1.63.0 | Web 界面 | 只能用命令行 |

### 2.3 文件清单（每个文件一句话）

```
RAG-project/
├── rag_core.py              核心：入库 + 检索 + 生成 + 多模型 + 相关度（907 行）
├── app.py                   Streamlit 主界面，含模型切换/上传文档/来源展示（421 行）
├── app_simple.py            简化界面，只保留初始化 + 提问（适合演示时少点干扰）
├── knowledge_base/          知识库原文（19 份 .md，约 6 万字）
├── data/chroma_db/          向量库持久化目录（Chroma 的 sqlite + 二进制索引）
├── examples/
│   ├── minimal_rag.py       80 行最小可运行 RAG（学骨架用）
│   └── debug_retrieval.py   检索调试工具：不调模型就能看命中哪几块、分数多少
├── .env.example             DeepSeek Key 等环境变量示例
├── requirements.txt         依赖清单
├── README.md                使用说明（安装、启动、排错）
└── RAG项目完整文档.md        数据流 + 行号索引 + 面试口述稿（本手册的精简版）
```

### 2.4 数据到底存在哪里

| 数据 | 位置 | 什么时候写 | 什么时候读 |
|------|------|-----------|-----------|
| 原始文档 | `knowledge_base/*.md` | 你放进去 | 重建索引时 |
| 向量 + 原文 + 元数据 | `data/chroma_db/` | 重建索引时 | 每次启动（不再重建） |
| BM25 关键词索引 | 内存（Python 对象） | 每次初始化 | 每次提问 |
| 对话历史 | 无（无记忆） | — | — |

> 关键点：**BM25 索引是内存里的，不落盘**。所以每次启动都要从 Chroma 把全部文本块读出来重建 BM25（96 个块只要毫秒级）。

---

## 三、两条主线（最重要的两张图）

### 3.1 入库链路（只在初始化/重建时跑一次）

```
knowledge_base/*.md
      │
      ▼ ① load_documents()            rag_core.py 552-587
   19 份 Document（正文 + 来源路径 metadata）
      │
      ▼ ② split_documents()           rag_core.py 589-601
   RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
   分隔符优先级：["\n\n", "\n", "。", "！", "？", ".", " ", ""]
   → 96 个文本块
      │
      ▼ ③ build_vectorstore()         rag_core.py 603-616
   先 _reset_chroma_collection() 清空旧集合（220-234）
   Chroma.from_documents(embedding=nomic-embed-text)
   → 每个块一个 768 维向量，落到 data/chroma_db/
      │
      ▼ ④ _load_all_documents()       rag_core.py 632-643
   把库里 96 个块读回内存（原文 + metadata）
      │
      ▼ ⑤ HybridRetriever(...)        rag_core.py 686-691
   用这 96 个块建 BM25 索引（内存），并统计每个词的 IDF
      │
      ▼ ⑥ build_rag_chain()           rag_core.py 645-660
   拼出 LCEL 链：{"context": retriever, "question": ...} | prompt | llm
```

对应的真实日志（重建时输出）：

```
📂 正在从 ...\knowledge_base 加载文档...
  📄 加载 0 个 *.txt 文件
  📄 加载 19 个 *.md 文件
✅ 共加载 19 个文档片段
✂️ 正在分割文档...
✅ 分割完成，共 96 个文本块
🔍 正在构建向量索引...
🧹 已清除旧的向量集合
📊 正在加载向量模型: nomic-embed-text
✅ 向量模型加载完成
✅ 向量数据库构建完成
🔍 已启用混合检索（向量 + BM25），共 96 个文本块
🔗 构建 RAG 问答链 (LCEL)，回答模式: 智能问答...
🤖 正在加载对话模型: Qwen2.5-3B（本地 Ollama）
✅ 对话模型加载完成
🎉 RAG 系统初始化完成！
```

### 3.2 问答链路（每次提问都跑）

```
用户提问："Docker 的镜像和容器有什么区别？"
      │
      ▼ ① rag.query(question)              rag_core.py 704-750
      │
      ▼ ② self._rag_chain.invoke(question) rag_core.py 712
      │   LCEL 自动做四件事：
      │   （a）调用 retriever → 触发 ③
      │   （b）把 3 个块拼成 {context}
      │   （c）按回答模式选模板，填 {context} 和 {question}
      │   （d）交给 llm 生成 → 返回 AIMessage
      │
      ▼ ③ HybridRetriever._rank_documents()  rag_core.py 330-375
      │   1) 向量检索 top-6        （similarity_search_with_score）
      │   2) BM25 关键词检索 top-6  （get_scores + 排序）
      │   3) RRF 融合：每块得分 += 1/(60+排名)
      │   4) 覆盖度：问题实词在块里的 IDF 加权覆盖率
      │       标题/文件名命中算满分，正文命中算 0.65
      │   5) 排序：先比覆盖度，再比 RRF 分 → 取前 3
      │
      ▼ ④ answer = response.content        rag_core.py 713
      │
      ▼ ⑤ retrieve_with_scores(question)   rag_core.py 719（再检索一次，拿分数给界面）
      │
      ▼ ⑥ 算相关度 score = 0.85×覆盖度 + 0.15×(1/向量排名)   385-390
      │   高 ≥0.5，中 ≥0.3，其余低                           393-399
      │
      ▼ ⑦ 判断是否真用了知识库                               736-740
      │   回答以「【通用知识】」或「未找到相关答案」开头 → 没用知识库
      │
      ▼ 返回 dict：question / model / mode / answer /
                  used_knowledge_base / sources / source_count
      │
      ▼ app.py render_sources()：高/中 片段列成「来源 1/2/3」，低 折叠
```

### 3.3 一次真实提问的时间线（RTX 4060 + qwen2.5:3b 实测）

| 环节 | 耗时 | 说明 |
|------|------|------|
| 检索（向量 + BM25 + 排序） | 0.1~0.3 秒 | 96 个块的规模，可忽略 |
| 提示词拼装 | < 10 毫秒 | 3 个块约 2000 字 |
| 模型推理 | 1~9 秒 | 取决于回答长度；3B 模型约 20~40 字/秒 |
| 界面渲染 | < 0.1 秒 | Streamlit 重跑 |

> 也就是说：**响应时间几乎等于模型推理时间**。想更快就换更小的模型或减少 `RETRIEVAL_K`（少塞上下文）。

---
## 四、逐模块精讲（对着代码看）

> 阅读顺序建议：4.1 配置 → 4.2 多模型 → 4.4 加载 → 4.5 切分 → 4.6 向量库 → 4.7 分词 → 4.8 混合检索 → 4.9 相关度 → 4.10 提示词 → 4.11 LCEL → 4.13 界面。

### 4.1 配置区（rag_core.py 44-82）

```python
KNOWLEDGE_BASE_DIR = Path(__file__).parent / "knowledge_base"   # 知识库目录
CHROMA_PERSIST_DIR = Path(__file__).parent / "data" / "chroma_db"  # 向量库目录

EMBEDDING_MODEL = "nomic-embed-text"    # 向量模型（768 维）
CHROMA_COLLECTION_NAME = "langchain"    # 集合名，重建时按这个名字删旧数据
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

CHUNK_SIZE = 800        # 文本块大小
CHUNK_OVERLAP = 100     # 相邻块重叠字符数

RETRIEVAL_K = 3          # 最终交给模型的块数
RETRIEVAL_VECTOR_K = 6   # 向量检索候选数
RETRIEVAL_BM25_K = 6     # 关键词检索候选数
RRF_K = 60               # RRF 融合参数
BODY_MATCH_CREDIT = 0.65 # 关键词只出现在正文时的折扣
```

**要点：** 所有"可调旋钮"都集中在这里。别人问你"想调整什么怎么改"，答案永远指向这一段。

| 想调什么 | 改哪个 | 影响 |
|---------|--------|------|
| 回答更完整 | `RETRIEVAL_K` 3→4/5 | 上下文更长，速度稍慢 |
| 检索更全 | `RETRIEVAL_VECTOR_K` / `RETRIEVAL_BM25_K` | 候选更多，噪声也可能更多 |
| 块更大/更小 | `CHUNK_SIZE` | 见 5.1 的取舍 |
| 换向量模型 | `EMBEDDING_MODEL` | 必须重建索引 |

### 4.2 多模型是怎么实现的（116-168）

```python
@dataclass(frozen=True)
class ModelSpec:
    key: str          # 唯一标识，如 "qwen2.5:3b"
    label: str        # 界面显示名，如 "Qwen2.5-3B（本地 Ollama）"
    provider: str     # "ollama" 或 "deepseek"
    model: str        # 传给后端的真实模型名
    description: str  # 一句话说明
```

```python
MODEL_REGISTRY: Dict[str, ModelSpec] = {
    "qwen2.5:3b":    ModelSpec(..., provider="ollama",   model="qwen2.5:3b"),
    "qwen2.5:7b":    ModelSpec(..., provider="ollama",   model="qwen2.5:7b"),
    "deepseek-chat": ModelSpec(..., provider="deepseek", model="deepseek-chat"),
}
```

**设计要点（面试常问）：**

1. **注册表模式**：新增模型 = 加一个字典条目，不改任何逻辑代码。
2. **界面只认 key**：界面下拉框拿到的是 key，切换时只把 key 交给 `set_model()`。
3. **`resolve_model()` 兜底**：key 不在表里（比如用户手写 `llama3:8b`）就按"本地 Ollama 模型"处理，不会报错。
4. **provider 决定走哪条路**：`ollama` → `ChatOllama`；`deepseek` → `ChatOpenAI` 或内置适配器。

### 4.3 创建模型实例（453-478）与 DeepSeek 适配器（402-450）

```python
def create_llm(model_key=None, api_key=None, temperature=0.1, num_ctx=4096):
    spec = resolve_model(model_key)
    if spec.provider == "deepseek":
        key = api_key or DEEPSEEK_API_KEY
        if not key:
            raise ValueError("使用 DeepSeek 需要提供 API Key...")
        try:
            from langchain_openai import ChatOpenAI        # 装了就用官方封装
        except ImportError:
            return DeepSeekChat(model=spec.model, api_key=key, temperature=temperature)
        return ChatOpenAI(model=spec.model, api_key=key, base_url=DEEPSEEK_BASE_URL, temperature=temperature)
    return ChatOllama(model=spec.model, temperature=temperature, num_ctx=num_ctx)
```

**为什么要有 `DeepSeekChat`？** DeepSeek 提供的是 OpenAI 兼容接口，但项目环境里没有 `langchain-openai`。于是写了一个 40 行的适配器，只做两件事：

```python
class DeepSeekChat(Runnable):                     # 继承 Runnable 才能进 LCEL 链
    def invoke(self, input, config=None, **kwargs) -> AIMessage:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=self._to_chat_messages(input),   # LangChain 消息 → OpenAI 格式
            temperature=self.temperature,
        )
        return AIMessage(content=response.choices[0].message.content or "")

    @staticmethod
    def _to_chat_messages(input):                 # str / 消息列表 都能转
        if isinstance(input, str):
            return [{"role": "user", "content": input}]
        ...
```

**关键概念：LCEL 里的任何一环只要满足 `Runnable` 契约（有 `invoke`），就能替换模型**。这就是"多模型热插拔"的底层机制。

- `temperature=0.1`：问答要忠实于资料，不要发挥创意。
- `num_ctx=4096`：本地模型的上下文窗口，太小会截断检索到的资料。

### 4.4 文档加载（552-587）

```python
for ext in ["*.txt", "*.md"]:                  # 文本类：一个 glob 批量读
    loader = DirectoryLoader(str(self.knowledge_base_dir), glob=ext,
                             loader_cls=TextLoader,
                             loader_kwargs={"encoding": "utf-8"})   # ← 必须指定 utf-8
    docs = loader.load()

for pdf_path in self.knowledge_base_dir.glob("*.pdf"):              # PDF 单独处理
    loader = PyPDFLoader(str(pdf_path))
    docs = loader.load()                                            # 一页一个 Document
```

**知识点：**

1. 每个 `Document` = `page_content`（正文）+ `metadata`（来源路径等），来源信息就是靠 metadata 传给界面的。
2. `encoding="utf-8"` 是中文项目的必备项；漏了会乱码或直接报解码错误。
3. PDF 按页切分，所以 PDF 的检索粒度天然比 Markdown 粗。
4. 加载失败用 try/except 包住：**一份坏文件不该让整个知识库起不来**。

### 4.5 文本切分（589-601）

```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,          # 800
    chunk_overlap=CHUNK_OVERLAP,    # 100
    separators=["\n\n", "\n", "。", "！", "？", ".", " ", ""],
)
chunks = text_splitter.split_documents(documents)
```

**递归切分的含义：** 先按段落（`\n\n`）切，一段超长就按换行切，还超长就按句子切（`。！？`），最后才硬切字符。这样能尽量保住语义边界。

**为什么是 800？** 实测教训：最初用 500，`## 4. 文件操作` 这种小标题和它下面的代码被拆到两个块里，模型拿不到完整信息 → 回答「未找到相关答案」。改成 800 后一个 800 字以内的小节基本能完整落在一个块里。

**为什么要 overlap=100？** 防止答案正好落在切分边界。代价是索引里会有少量重复文本。

### 4.6 向量库与「重建前清空」（603-629 + 220-234）

```python
def build_vectorstore(self, chunks):
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    _reset_chroma_collection()                     # ← 关键：先清空旧集合
    return Chroma.from_documents(
        documents=chunks,
        embedding=self.embeddings,                 # ← 参数名是 embedding，不是 embedding_function
        persist_directory=str(CHROMA_PERSIST_DIR),
    )
```

```python
def _reset_chroma_collection(collection_name=CHROMA_COLLECTION_NAME):
    client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
    names = [item.name if hasattr(item, "name") else str(item)
             for item in client.list_collections()]
    if collection_name in names:
        client.delete_collection(collection_name)   # 删掉再重建，避免重复累积
```

**两个必须记住的点：**

1. **参数名踩坑**：`Chroma.from_documents()` 用 `embedding=`，而 `Chroma()` 构造函数用 `embedding_function=`。写错会报 `got multiple values for keyword argument 'embedding_function'`。
2. **不清空会重复累积**：Chroma 是"追加"语义。同一份文档重建两次就会有两份向量，检索时出现重复片段、结果变脏。所以重建前必须删集合。

```python
def load_vectorstore(self):        # 启动时优先复用已有索引（快）
    if CHROMA_PERSIST_DIR.exists() and any(CHROMA_PERSIST_DIR.iterdir()):
        return Chroma(collection_name=CHROMA_COLLECTION_NAME,
                      persist_directory=str(CHROMA_PERSIST_DIR),
                      embedding_function=self.embeddings)
    return None
```

### 4.7 中文分词（248-266）—— 没有分词库也能做

```python
def tokenize_for_bm25(text: str) -> List[str]:
    tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())      # 英文/数字：整词
    for run in re.findall(r"[\u4e00-\u9fff]+", text):        # 中文：按"二元组"切
        if len(run) == 1:
            tokens.append(run)
        else:
            tokens.extend(run[i:i+2] for i in range(len(run) - 1))
    return tokens
```

例：`"什么是列表推导式"` → `["什么", "么是", "是列", "列表", "表推", "推导", "导式"]`

**为什么要二元切分？** 中文没有空格，`re.findall(r"\w+")` 会把整句当一个词，BM25 完全失效。二元切分（bigram）是个"零依赖"的近似方案：`列表`、`推导` 这些真正的词会作为子串出现在里面，所以能被命中。

**代价**：会产生 `么是`、`表推` 这种垃圾词。正式版用两道保险处理：
- 计算"相关度"时，只统计**知识库里真实出现过的词**（`_term_weight()` 里 `df <= 0` 直接返回 0）；
- 另有一份 `QUESTION_STOPWORDS`（238-243）过滤"什么/怎么/区别/一下"等疑问词。

```python
def extract_query_terms(text: str) -> List[str]:
    terms = []
    for token in tokenize_for_bm25(text):
        if len(token) < 2 or token in QUESTION_STOPWORDS or token in terms:
            continue           # 去单字、去疑问词、去重复
        terms.append(token)
    return terms
```

### 4.8 混合检索器 HybridRetriever（269-382）—— 全项目的心脏

#### 4.8.1 它解决什么问题

实测发现：**nomic-embed-text 对中文的区分度很差**。问「如何处理文件读写？」，真正含文件操作代码的块被排到最后一名；问「什么是列表推导式？」，排第一的永远是文档开头块（因为开头块有标题，跟任何问题都"有点像"）。

→ 于是加第二路：**BM25 关键词检索**。两路结果用 RRF 融合。
→ 再用**关键词覆盖度**排序，避免"只命中一个通用词"的块被顶上来。

你可以用 `examples/minimal_rag.py`（纯向量，答不出「列表推导式」）和 `examples/debug_retrieval.py`（正式版，直接命中）对比，一眼看出差别。

#### 4.8.2 数据结构：候选池

```python
def _rank_documents(self, query):
    found: Dict[str, Document] = {}                      # 块正文 → Document
    info:  Dict[str, Dict[str, float]] = {}              # 块正文 → 各项分数

    def slot(doc):                                       # 取出（或新建）某块的记录
        key = doc.page_content                           # 用正文当唯一键
        found.setdefault(key, doc)
        return info.setdefault(key, {"rrf": 0.0, "coverage": 0.0,
                                     "vector_rank": 0.0, "keyword_rank": 0.0})

    def add(docs, kind):                                 # 把一路检索结果并入候选池
        for rank, doc in enumerate(docs, start=1):
            item = slot(doc)
            item["rrf"] += 1.0 / (RRF_K + rank)          # ← RRF 核心公式
            if not item[f"{kind}_rank"]:
                item[f"{kind}_rank"] = rank
```

`RRF_K = 60` 是常数（原论文取值）。**同一块被两路都命中，分就会叠加**——这是"混合检索比单路更稳"的原因。

#### 4.8.3 第一路：向量检索

```python
try:
    vector_docs = [doc for doc, _ in self.vectorstore.similarity_search_with_score(query, k=self.vector_k)]
except Exception:
    vector_docs = self.vectorstore.similarity_search(query, k=self.vector_k)
add(vector_docs, "vector")
```
- 取 6 个候选（`RETRIEVAL_VECTOR_K`）。
- `with_score` 版本返回 (文档, 距离)，这里只要文档，但保留它方便以后做排序；失败则退化为普通检索。
- 这一步会把问题也用 nomic-embed-text 转向量，**所以问答延迟里有一小部分是嵌入耗时**。

#### 4.8.4 第二路：BM25 关键词检索

```python
bm25 = self._ensure_bm25()                 # 懒加载：第一次用到时才建索引
if bm25 is not None:
    keyword_scores = bm25.get_scores(tokenize_for_bm25(query))
    order = sorted(range(len(keyword_scores)), key=lambda i: -keyword_scores[i])
    hits = [i for i in order[: self.keyword_k] if keyword_scores[i] > 0]
    add([self.documents[i] for i in hits], "keyword")
```

```python
def _ensure_bm25(self):                      # 286-295
    if self._bm25 is None and BM25Okapi is not None and self.documents:
        corpus = [tokenize_for_bm25(doc.page_content) for doc in self.documents]
        self._bm25 = BM25Okapi(corpus)
        df = {}                              # 顺便统计文档频率，供 IDF 用
        for tokens in corpus:
            for token in set(tokens):
                df[token] = df.get(token, 0) + 1
        self._df = df
    return self._bm25
```
- BM25 索引建在**内存**里（不落盘），所以每次启动都要重建一次。
- 只有分数 > 0 的才进候选池，避免"一个词都没命中"的块混进来。

#### 4.8.5 第三路信号：关键词覆盖度（本项目自研的核心）

先算每个词的权重（越冷门越重要）：

```python
def _term_weight(self, term):                       # 297-302
    df = self._df.get(term, 0)
    if df <= 0 or not self.documents:
        return 0.0                                  # 知识库里没有这个词 → 不参与
    return max(math.log((len(self.documents) + 1) / (df + 1)), 1e-6)   # IDF
```

再算某块覆盖了多少（标题/文件名命中权重最高）：

```python
def _coverage(self, terms, doc):                    # 304-328
    body_tokens = set(tokenize_for_bm25(doc.page_content))
    heading_tokens = set()
    for line in doc.page_content.splitlines():
        if HEADING_PATTERN.match(line):             # 形如 "## 3. 网络排查"
            heading_tokens.update(tokenize_for_bm25(line))
    heading_tokens.update(tokenize_for_bm25(Path(doc.metadata["source"]).stem))  # 文件名

    total = hit = 0.0
    for term in terms:
        weight = self._term_weight(term)
        if weight <= 0:
            continue
        total += weight
        if term in heading_tokens:
            hit += weight                            # 标题命中：满分
        elif term in body_tokens:
            hit += weight * BODY_MATCH_CREDIT        # 正文命中：0.65
    return hit / total if total else 0.0
```

**为什么标题加权？** 因为知识库是有结构的：`## 9. Docker 基础` 里出现 "Docker"，比某段正文里随便提到一次 "Docker" 更能说明"这一块就是在讲 Docker"。文件名同理（`Rust语言基础.md` 里出现 rust）。

#### 4.8.6 排序与输出

```python
ranked = sorted(info.items(),
                key=lambda item: (-round(item[1]["coverage"], 2),   # 主排序：覆盖度
                                  -item[1]["rrf"]))                 # 次排序：融合分
return [(found[key], item) for key, item in ranked[: self.k]]       # 只取前 3
```

**为什么不直接用 RRF 排序？** 因为 RRF 只懂"排名"，不懂"内容"。一个块可能因为命中了「架构」「什么」这种通用词而排在前面（我们实测过：问「什么是 Transformer 架构」，讲"总体架构"的软件工程文档被排到第一）。加上覆盖度后，真正讲 Transformer 的块才能排到第一。

对外暴露两个方法：

```python
def retrieve_with_scores(self, query):      # 377-379  给界面用（要分数）
    return self._rank_documents(query)

def _get_relevant_documents(self, query, *, run_manager=None):   # 381-382  LangChain 规定要实现的
    return [doc for doc, _ in self._rank_documents(query)]
```

> `BaseRetriever` 要求子类实现 `_get_relevant_documents`，这样它就能像普通检索器一样被塞进 LCEL 链。

### 4.9 相关度分数与标签（385-399）

```python
def source_relevance(info):
    coverage = float(info.get("coverage", info.get("keyword", 0.0)) or 0.0)
    vector_rank = int(info.get("vector_rank", 0) or 0)
    vector_part = 1.0 / vector_rank if vector_rank > 0 else 0.0
    return round(min(0.85 * coverage + 0.15 * vector_part, 1.0), 3)

def relevance_label(score):
    if score >= 0.5: return "高"
    if score >= 0.3: return "中"
    return "低"
```

- 覆盖度是主力（0.85），向量排名只做微调（第 1 名 +0.15，第 2 名 +0.075……）。
- 之所以不直接用向量距离：nomic-embed-text 的中文区分度太差，距离值几乎没有区分度。
- 界面的处理（app.py 274-297）：只把「高/中」列成来源并按分数排序，「低」折叠进「其他检索到的片段」；如果这次回答根本没用知识库，就直接提示「未使用知识库内容」。

### 4.10 提示词与两种回答模式（91-113）

```python
PROMPT_TEMPLATES = {
    "smart": """你是知识库问答助手，请优先依据下面的"知识库内容"回答用户问题。

规则：
1. 如果知识库内容与问题相关，请依据它回答，不要编造知识库中没有的信息；
2. 如果知识库内容与问题无关或不足以回答，请直接用你自己的知识回答，并在回答开头注明"【通用知识】"；
3. 始终用中文回答，简洁准确。

知识库内容：
{context}

问题：{question}

回答：""",

    "kb_only": """根据以下上下文回答问题。如果上下文没有相关信息，请说"未找到相关答案"。

上下文：
{context}

问题：{question}

回答：""",
}
```

**设计要点：**

- 模板用 `{context}` 和 `{question}` 两个占位符，正好对应 LCEL 链里那个字典的两个键。
- 智能模式要求模型"标注【通用知识】"，这是**给程序看的信号**：`query()` 靠这个前缀判断 `used_knowledge_base`，界面靠它决定要不要提示"本次回答未使用知识库"。
- 严格模式适合答辩/演示，保证每句话都有出处。

### 4.11 LCEL 链（645-660）—— 一行代码拆开讲

```python
prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATES[self.answer_mode])

self._rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | self.llm
)
```

这段等价于：

```
输入 question
  ├── "context"  → retriever.invoke(question)        → 3 个 Document → 拼成字符串
  └── "question" → RunnablePassthrough() 原样传下去
        ↓ 合成 dict {"context": "...", "question": "..."}
      prompt.invoke(dict)     → 填好模板的 PromptValue
      llm.invoke(PromptValue) → AIMessage
```

**为什么用 LCEL 而不是 `RetrievalQA`？** LangChain 1.x 已移除旧的 `RetrievalQA`，LCEL 是官方推荐写法；而且管道里每一环都能替换、能加、能调试（比如中间插一个 `| StrOutputParser()`）。

**`RunnablePassthrough()` 是什么？** 一个"原样返回输入"的组件。在这里的作用是把用户问题原封不动放进字典的 `question` 键。

### 4.12 RAGSystem 的生命周期（481-750）

```python
rag = RAGSystem(model_key="qwen2.5:3b")      # 1. 构造：只记配置，什么都不加载
rag.initialize()                             # 2. 初始化：加载/复用向量库 + 建 BM25 + 建链
rag.query("什么是列表推导式？")                # 3. 提问：返回 dict
rag.set_model("deepseek-chat")               # 4. 换模型：只换模型，不重建索引
rag.set_answer_mode("kb_only")               # 5. 换回答模式：只重建链，不重建索引
rag.initialize(force_rebuild=True)           # 6. 重建：重新加载文档 → 切分 → 覆盖向量库
```

**懒加载设计（重要）：**

```python
@property
def llm(self):
    if self._llm is None:                     # 第一次真正用到才创建
        self._llm = create_llm(self.model_key, api_key=self._api_key)
    return self._llm
```
向量模型 `embeddings`、检索器 `_retriever`、问答链 `_rag_chain` 同理。好处：**只改配置不启动服务时，不会白白加载几个 GB 的模型**。

**切换模型为什么不重建向量库？**

```python
def set_model(self, model_key, api_key=None):
    spec = resolve_model(model_key)
    self.model_key = spec.key
    self._llm = None                          # 丢弃旧的对话模型
    if self._retriever is not None:
        self.build_rag_chain(self._retriever)  # 用同一个检索器重新拼链
    return spec
```
因为**对话模型和向量模型是两码事**：向量库是用 nomic-embed-text 建的，换 qwen2.5:7b 回答不影响它。只有换 embedding 模型才必须重建索引。

### 4.13 界面层 app.py（421 行）

结构是"一个 main + 若干 render 小函数"：

| 函数 | 行号 | 职责 |
|------|------|------|
| `get_rag_system()` | 53-56 | `@st.cache_resource` 全局单例，保证模型只加载一次 |
| `ollama_model_ready()` | 59-62 | `@st.cache_data(ttl=10)` 查本地模型是否已下载 |
| `render_model_selector()` | 65-128 | 下拉框选模型、DeepSeek Key 输入、一键下载本地模型 |
| `render_answer_mode()` | 131-161 | 智能问答 / 严格知识库 单选 |
| `knowledge_base_files()` | 167-176 | 列出知识库里的 .md/.txt/.pdf |
| `render_knowledge_base_status()` | 178-189 | 显示文档数量与前 5 个文件名 |
| `save_uploaded_files()` | 192-203 | 把网页上传的文件写进 `knowledge_base/`（同名跳过） |
| `render_operations()` | 206-245 | 上传文档 + 重建知识库 + 创建示例文档 |
| `render_system_info()` | 247-264 | 侧边栏信息面板 |
| `source_file_name()` | 267-272 | 从 metadata 取文件名 |
| `render_sources()` | 274-297 | 按相关度展示来源，低相关折叠 |
| `main()` | 299-416 | 页面布局：侧边栏 + 左问答区 + 右来源区 |

**必须理解的 Streamlit 机制：**

1. **脚本是"重跑式"的**：任何交互（点按钮、改下拉框）都会把整个脚本从头执行一遍。所以状态必须放 `st.session_state`（如 `initialized`、`last_result`、`model_key`）。
2. **`@st.cache_resource` 用于"重量级单例"**：RAGSystem（含模型、向量库）必须缓存，否则每次重跑都会重新加载模型。
3. **`@st.cache_data` 用于"可序列化的查询结果"**：比如"本地某个模型是否已下载"。
4. **`st.rerun()`**：初始化完成后手动触发一次重跑，切到问答界面。

**回答区的小设计（389-408）：**

```python
if answer.lstrip().startswith(GENERAL_KNOWLEDGE_TAG):        # 模型自答
    st.info("💡 知识库中没有找到相关内容，以下为模型自身知识的回答（非知识库内容）")
    answer = answer.lstrip()[len(GENERAL_KNOWLEDGE_TAG):].lstrip()   # 剥掉标记再展示
```
把给程序看的 `【通用知识】` 标记转成人能看懂的提示条，这就是"标记"设计的价值。

### 4.14 命令行入口（876-907）

```python
if __name__ == "__main__":
    if not any(KNOWLEDGE_BASE_DIR.iterdir()):     # 知识库空目录 → 自动生成示例文档
        create_sample_knowledge()
    specs = available_models()
    for index, spec in enumerate(specs, 1):       # 打印菜单
        print(f"  {index}. {spec.label} — {spec.description}")
    choice = input("请选择对话模型: ").strip()     # 选模型
    ...
    rag = RAGSystem(model_key=model_key)
    if rag.initialize():
        while True:                               # 循环问答，quit 退出
            question = input("❓ 请输入问题: ").strip()
            ...
            result = rag.query(question)
            print(f"📖 回答（{result['model']}）:\n{result['answer']}")
```

这一段说明：**核心逻辑和界面完全解耦**。同一个 `RAGSystem`，命令行能用、Streamlit 能用、将来接 FastAPI 或钉钉机器人也能用。

---
## 五、为什么这么设计（答辩/面试必问）

> 用法：记住"问题 → 做法 → 原因 → 代价"这四段式，任何技术追问都能答。

### 5.1 为什么 chunk_size 是 800，不是 500 或 1000？

- **做法**：800 字符，重叠 100。
- **原因**：500 会把 `## 4. 文件操作` 这种标题和它下面的代码拆到两个块，检索到标题却拿不到代码，模型答"未找到"；1000 以上又会让一个块混进两三个主题，检索精度下降。
- **代价**：块越大，上下文越长，模型推理越慢，且容易被无关内容干扰。

### 5.2 为什么要做混合检索，而不是只用向量检索？

- **做法**：向量 top-6 + BM25 top-6，RRF 融合，最后取 top-3。
- **原因**：实测 nomic-embed-text 对中文区分度很差——问「什么是列表推导式」，排第一的永远是文档开头块。BM25 靠关键词命中，能精准抓住「列表推导式」这种中文专有说法。
- **代价**：多一份内存索引、多一次分词计算（毫秒级，可忽略）。

### 5.3 中文为什么用"二元切分"而不是装分词库（jieba）？

- **做法**：`re.findall(r"[\u4e00-\u9fff]+", text)` 后按 2 字滑窗切。
- **原因**：零依赖、零配置，效果对检索足够（"列表""推导"都会作为子串出现）。
- **代价**：产生"么是""表推"等垃圾词 → 用 `QUESTION_STOPWORDS` + "知识库里没有的词不计分"两道过滤兜住。
- **如果重做**：可以换 jieba 分词，或用 bge-m3 这种中文更强的 embedding 模型，双管齐下。

### 5.4 为什么用 RRF 融合而不是加权求和？

- **做法**：`score += 1 / (60 + rank)`。
- **原因**：向量距离和 BM25 分数**量纲完全不同**，直接加权需要反复调参且不稳定。RRF 只看"排名"，天然无需归一化。
- **代价**：丢掉了"分差"信息（第 1 名和第 2 名差多少不重要了）。

### 5.5 为什么还要在 RRF 之上再算"覆盖度"？

- **做法**：先按覆盖度排序，再按 RRF 排序。
- **原因**：RRF 不懂内容。实测问「什么是 Transformer 架构」，讲"总体架构"的软件工程文档因为命中「架构」而被排到第一，真正讲 Transformer 的块反而靠后 → 来源看起来和回答无关。
- **代价**：多一次全库分词统计（96 个块，毫秒级）。

### 5.6 相关度为什么不用向量距离，而用"覆盖率 + 排名"？

- **做法**：`0.85 × 覆盖度 + 0.15 × (1/向量排名)`。
- **原因**：nomic-embed-text 的中文向量距离几乎无区分度（不同块的距离值很接近），拿它当"相关度"会给出误导性的分数。
- **代价**：覆盖度对"换个说法提问"不敏感（用词不同就命中不到）——这是关键词法的固有短板。

### 5.7 为什么加"智能问答 / 严格知识库"两种模式？

- **做法**：两套提示词模板，界面一键切换（不需要重建索引）。
- **原因**：答辩/演示要"每句有出处"→ 严格模式；日常使用要"想问什么问什么"→ 智能模式。
- **代价**：智能模式下模型可能用自身知识回答，需要界面明确标注【通用知识】避免误解。

### 5.8 切换模型为什么能秒切、还不重建向量库？

- **做法**：`set_model()` 只把 `self._llm` 置空并重建链。
- **原因**：对话模型和向量模型是两条独立的链路；索引是用 nomic-embed-text 建的，跟谁来读它无关。
- **唯一的例外**：换掉 `EMBEDDING_MODEL` 必须重建，因为向量空间变了。

### 5.9 为什么要自己写 DeepSeek 适配器？

- **做法**：`DeepSeekChat(Runnable)`，只用 openai SDK。
- **原因**：DeepSeek 是 OpenAI 兼容接口，但环境里没有 `langchain-openai`；继承 `Runnable` 后就能像官方组件一样进 LCEL 链，不破坏架构。
- **代价**：只实现 `invoke`（非流式），没有流式输出。

### 5.10 重建知识库为什么要先清空集合？

- **做法**：`_reset_chroma_collection()` 删掉同名集合再 `from_documents`。
- **原因**：Chroma 是追加语义，不清空就会累积重复向量，检索结果出现大量重复片段。
- **踩过的坑**：`from_documents(embedding=...)` 与 `Chroma(embedding_function=...)` 参数名不同，写错直接抛异常。

### 5.11 为什么温度设 0.1？

- **原因**：问答要忠实于检索到的资料，不要发挥想象；0.1 接近确定性但保留极小的表达变化。
- **对照**：写文案、头脑风暴时才用 0.7~1.0。

### 5.12 为什么核心逻辑和界面要分成两个文件？

- **做法**：`rag_core.py` 不含任何 Streamlit 代码；`app.py` 只负责展示与交互。
- **原因**：同一套核心既能跑命令行、又能跑网页，将来接 API/微信机器人也不用改核心；便于单独测试检索质量。
- **证据**：`examples/debug_retrieval.py` 只 import 核心，就能脱离模型直接调检索。

---

## 六、从零复现（两条路线）

### 6.0 复现总览

| 步骤 | 目标 | 验收标准 |
|------|------|---------|
| 1 | 环境就绪 | `ollama list` 能看到 qwen2.5:3b 与 nomic-embed-text |
| 2 | 最小 RAG 跑通（`examples/minimal_rag.py`，80 行） | 问「Docker 的镜像和容器有什么区别」能答对 |
| 3 | 加持久化 | 第二次启动不再重新嵌入（秒级） |
| 4 | 加 BM25 混合检索 | 「什么是列表推导式」能答对（纯向量答不出） |
| 5 | 加多模型 | 侧边栏能切 3B/7B/DeepSeek，切换不重建索引 |
| 6 | 加相关度与两种模式 | 来源随问题变化、标出高/中/低 |
| 7 | 加界面 | 浏览器能上传文档、提问、看来源 |
| 8 | 加健壮性 | 重建不重复累积、坏文件不炸库、中文不乱码 |

### 6.1 环境准备

```bash
# ① Python 3.12+（本项目实测 3.14.7），建议用 uv 或 venv 建虚拟环境
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # Linux/macOS

# ② 安装依赖
pip install langchain langchain-community langchain-ollama langchain-text-splitters \
            chromadb pypdf rank-bm25 streamlit openai python-dotenv

# ③ 安装 Ollama（https://ollama.com/download），然后拉模型
ollama pull qwen2.5:3b            # 对话模型，约 2GB
ollama pull nomic-embed-text      # 向量模型，约 274MB
# 可选：ollama pull qwen2.5:7b     # 约 4.7GB

# ④ 验证 Ollama 服务
ollama list
```

> 4060 显卡建议：Ollama 会自动用 GPU；显存不足时它会把模型部分放到内存，速度会明显下降。

### 6.2 目录与依赖

```
RAG-project/
├── knowledge_base/          # 放你的 .md/.txt/.pdf
├── data/                    # 向量库落盘位置（自动创建）
├── rag_core.py
├── app.py
└── .env                     # DEEPSEEK_API_KEY=（可选）
```

### 6.3 第一步：最小可运行 RAG（先跑通再优化）

完整可运行版本在 `examples/minimal_rag.py`，核心就 5 步：

```python
# ① 加载
documents = DirectoryLoader(str(KB_DIR), glob="*.md", loader_cls=TextLoader,
                            loader_kwargs={"encoding": "utf-8"}).load()

# ② 切分
chunks = RecursiveCharacterTextSplitter(
    chunk_size=800, chunk_overlap=100,
    separators=["\n\n", "\n", "。", "！", "？", ".", " ", ""],
).split_documents(documents)

# ③ 向量化 + 存储
vectorstore = Chroma.from_documents(
    chunks, embedding=OllamaEmbeddings(model="nomic-embed-text"),
    persist_directory=str(DB_DIR))

# ④ 检索
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# ⑤ 生成
prompt = ChatPromptTemplate.from_template(
    "根据下面的资料回答问题；资料里没有就说不知道。\n\n资料：\n{context}\n\n问题：{question}\n\n回答：")
chain = ({"context": retriever, "question": RunnablePassthrough()}
         | prompt | ChatOllama(model="qwen2.5:3b", temperature=0.1) | StrOutputParser())
print(chain.invoke("Docker 的镜像和容器有什么区别？"))
```

**跑一下你会看到**：Docker 那题答对了，但问「什么是列表推导式」会答"资料里没有"——**这不是你写错了，这是纯向量检索对中文的真实水平**。记住这个现象，第五章 5.2 就是在解决它。

### 6.4 第二步：让索引落盘（别每次都重算）

```python
# 已存在就直接加载，否则构建
if DB_DIR.exists() and any(DB_DIR.iterdir()):
    vectorstore = Chroma(collection_name="langchain",
                         persist_directory=str(DB_DIR),
                         embedding_function=OllamaEmbeddings(model="nomic-embed-text"))
else:
    vectorstore = Chroma.from_documents(chunks, embedding=embeddings,
                                        persist_directory=str(DB_DIR))
```

**验收**：第二次运行不再打印"正在构建向量索引"，启动时间从 ~2 秒降到毫秒级。

### 6.5 第三步：加 BM25 混合检索（本项目最关键的升级）

按顺序做四件小事：

1. 写 `tokenize_for_bm25()`（英文整词 + 中文二元切分，见 4.7）。
2. 用全部文本块建 BM25 索引，并统计 `df`（文档频率）。
3. 写 `HybridRetriever(BaseRetriever)`：向量 top-6 + BM25 top-6，用 `1/(60+rank)` 融合。
4. 写 `_coverage()` 并按它排序。

**为什么必须继承 `BaseRetriever`？** 因为要把它直接塞进 LCEL 链（`{"context": retriever, ...}`），LangChain 要求这一环是 Retriever 类型。

**验收**：`python examples/debug_retrieval.py "什么是列表推导式？"` 第一条应该是 `Python入门指南.md`、覆盖度 1.00、标"高"。

### 6.6 第四步：加多模型支持

1. 定义 `ModelSpec`（dataclass）+ `MODEL_REGISTRY` 字典。
2. 写 `create_llm()`，按 `provider` 分支返回 `ChatOllama` / `ChatOpenAI` / 自研适配器。
3. `RAGSystem` 增加 `set_model()`：换 key、丢缓存、重建链（不碰向量库）。

**验收**：侧边栏切换模型后立刻提问，回答风格/速度变化，但不用重新初始化。

### 6.7 第五步：加相关度与两种回答模式

1. `source_relevance()` + `relevance_label()`：把检索信息换算成 0~1 分与高/中/低。
2. `PROMPT_TEMPLATES` 两套模板 + `set_answer_mode()`。
3. `query()` 根据回答开头是否是「【通用知识】/未找到相关答案」判断 `used_knowledge_base`。

**验收**：问知识库内的问题 → 来源标"高"；问「明天天气」→ 回答带【通用知识】前缀、来源区提示"未使用知识库内容"。

### 6.8 第六步：加 Streamlit 界面

```bash
streamlit run app.py      # 浏览器打开 http://localhost:8501
```

四个必须记住的点：

1. `@st.cache_resource` 缓存 RAGSystem（否则每次点击都重载模型）。
2. 状态放 `st.session_state`（`initialized` / `last_result` / `model_key`）。
3. 交互会重跑整个脚本 —— 这是 Streamlit 的核心心智模型。
4. 用 `st.status()` / `st.spinner()` 给长任务（初始化、提问）加载反馈。

### 6.9 第七步：健壮性完善（容易被忽略但很关键）

| 问题 | 解法 | 代码位置 |
|------|------|---------|
| 重建后片段重复 | 重建前删集合 | `_reset_chroma_collection()` 220-234 |
| 中文乱码 | 所有文件读写指定 utf-8 | 552-587 / app.py 上传 |
| 一份坏文档导致建库失败 | 每个文件 try/except | 569-584 |
| DeepSeek 没 Key 直接崩 | 入口处校验并给中文提示 | 418-419、464-465 |
| 用户传了错文件 | 同名跳过 + 格式白名单 | app.py 192-203 |
| 7B 未下载就选它 | 启动前检查 + 一键下载 | app.py 107-128 |
| 清空集合失败 | 捕获异常继续（可忽略） | 233-234 |
| 命令行中文乱码 | 输出前设 `PYTHONIOENCODING=utf-8` | 运行环境变量 |

### 6.10 复现路上的 8 个坑（都是本项目真实踩过的）

| # | 现象 | 原因 | 解法 |
|---|------|------|------|
| 1 | `Chroma() got multiple values for keyword argument 'embedding_function'` | `from_documents` 的参数名是 `embedding`，构造函数的才是 `embedding_function` | 分开写 |
| 2 | 重建后检索出现重复片段 | Chroma 追加语义，旧集合没删 | 重建前 `delete_collection` |
| 3 | 回答总是「未找到相关答案」 | ①块切太小（500）把标题和代码拆开 ②纯向量对中文排序差 | 改 800 + 加 BM25 |
| 4 | 来源和回答无关、每次都一样 | BM25 分按"本次最高分"归一化 → 任何问题都有一个满分来源 | 改用 IDF 覆盖度排序 |
| 5 | 切到 7B 提问没反应 | 模型没下载，Ollama 在后台拉取 | `ollama pull qwen2.5:7b` |
| 6 | DeepSeek 报 401/连接失败 | Key 没填 / 环境变量没生效 / 无外网 | 界面填 Key 或写 `.env` |
| 7 | 中文文件名读进来是乱码 | 加载时没指定 `encoding="utf-8"` | `loader_kwargs={"encoding": "utf-8"}` |
| 8 | Windows 控制台打印中文报 GBK 错误 | 终端默认编码不是 UTF-8 | `set PYTHONIOENCODING=utf-8` |

---
## 七、口述稿（可直接背）

> 口述的原则：**先说是什么 → 再说怎么做 → 最后说为什么这么做**。数字要具体（800 字、96 块、top-6、top-3），细节要能落地（提到具体函数名）。

### 7.1 30 秒版（电梯陈述 / 开场）

> 这是一个基于 RAG 的知识库问答系统，用 Python 写的，核心是 LangChain + ChromaDB + Ollama。
> 它把 19 份技术文档切成 96 个文本块，用 nomic-embed-text 转成向量存进 Chroma；
> 提问时先用「向量检索 + BM25 关键词检索」两路召回、用 RRF 融合，再按关键词覆盖度排序选出最相关的 3 块，
> 连同问题一起交给本地 Qwen2.5 模型生成回答，并给出带相关度的参考来源。
> 支持本地 3B/7B 模型和外接 DeepSeek API 随时切换，也支持智能问答与严格知识库两种回答模式。

### 7.2 2 分钟版（面试 / 答辩主体）

> 我做的是一套离线可用的 RAG 知识库问答系统，解决的问题是：大模型不知道我的私有文档，而且容易瞎编。
>
> 整个系统分两条链路。**第一条是入库链路**：把知识库里的 Markdown、TXT、PDF 读成 Document，用递归字符切分器切成 800 字、重叠 100 字的文本块——这里 800 是实测调出来的，最早用 500 会把小节标题和代码拆散，导致模型答"未找到"；然后用 nomic-embed-text 把每个块转成 768 维向量存进 ChromaDB，并且重建前会先清空旧集合，避免重复累积。
>
> **第二条是问答链路**，这是重点。用户提问后，我先做混合检索：一路向量检索取 top-6，一路 BM25 关键词检索取 top-6，用 RRF 公式「1/(60+排名)」把两路结果融合；然后再算一个"关键词覆盖度"，也就是问题里的实词有多少出现在这个块里，冷门词权重高、出现在标题或文件名里算满分，最后先按覆盖度、再按 RRF 分排序取 top-3。之所以要加后面这一步，是因为纯 RRF 不懂内容——实测问"什么是 Transformer 架构"，命中"架构"两个字的软件工程文档会被排到第一，真正讲 Transformer 的块反而靠后，来源看起来就和回答无关。
>
> 检索到的 3 个块填进提示词模板，通过 LCEL 管道「retriever | prompt | llm」交给模型生成回答。回答完之后，我再算一次相关度，公式是 0.85 乘覆盖度加 0.15 乘向量排名得分，≥0.5 标"高"、≥0.3 标"中"，界面只把高和中列成参考来源，低的折叠起来；如果模型回答的是知识库以外的内容，回答会带【通用知识】前缀，界面就提示"本次未使用知识库内容"。
>
> 工程上还有几个设计：模型用注册表管理，本地 3B/7B 和 DeepSeek 可以秒切，因为对话模型和向量模型解耦，切换不需要重建索引；回答模式有两套提示词，严格模式保证每句话有出处，智能模式允许模型用自身知识兜底。整个响应时间 1 到 9 秒，几乎全是模型推理时间，检索部分不到 0.3 秒。

### 7.3 5 分钟版（深挖技术细节）

在 2 分钟版的基础上，按下面顺序展开（每点 30~60 秒）：

1. **技术选型理由**：为什么 Ollama（本地、免费、隐私）而不是 OpenAI API；为什么 ChromaDB（轻量、嵌入式、持久化到本地 SQLite）而不是 Milvus/FAISS；为什么 LangChain（组件化、LCEL 可组合）。
2. **切分策略**：RecursiveCharacterTextSplitter 的分隔符优先级 `["\n\n", "\n", "。", "！", "？", ".", " ", ""]`，以及 800/100 的由来。
3. **中文检索的三个层次**：① 分词层——中文二元切分（不引第三方分词库）；② 召回层——向量 + BM25 双路；③ 排序层——RRF + IDF 覆盖度。
4. **RRF 公式讲清楚**：`score += 1/(k+rank)`，k=60；为什么它不需要归一化（向量距离和 BM25 分量纲不同）；同一块被两路命中会叠加分数。
5. **覆盖度的两个细节**：IDF 权重（`log((N+1)/(df+1))`）与标题/文件名加权（标题命中记满分、正文记 0.65）；知识库里不存在的词直接不计分（否则垃圾二元词会稀释权重）。
6. **LCEL 管道**：`{"context": retriever, "question": RunnablePassthrough()} | prompt | llm`，字典的两个键正好对应模板的两个占位符。
7. **工程健壮性**：重建先删集合、每份文档独立 try/except、UTF-8 全线指定、懒加载模型、`@st.cache_resource` 单例。
8. **实测数据**：19 份文档 → 96 个块；重建 2.3 秒；提问 1~9 秒；知识库外问题正确降级为通用知识模式。
9. **不足之处**（主动说，显得诚实）：没有 rerank 模型、没有对话记忆、向量库不能增量更新、用的是已标记弃用的 `langchain_community.Chroma`、DeepSeek 适配器不支持流式输出。

### 7.4 现场演示脚本（边点边说，约 3 分钟）

| 步骤 | 操作 | 你要说的话 |
|------|------|-----------|
| 1 | 打开网页，指侧边栏 | "左边是模型选择，本地 3B/7B 和外接 DeepSeek 可以随时切，切换不会重建索引，因为向量库和对话模型是解耦的。" |
| 2 | 指"回答方式" | "这里两种模式：智能问答允许模型用自身知识兜底并标注【通用知识】；严格知识库保证每句话都来自知识库。" |
| 3 | 点「初始化 RAG 系统」 | "初始化做三件事：加载文档切块、构建向量索引、加载模型。第二次启动会复用已有索引，秒级完成。" |
| 4 | 问「Docker 的镜像和容器有什么区别？」 | "这是一个跨领域问题，能看出知识库确实扩到了运维方向。" |
| 5 | 指右侧来源 | "右边是参考来源，带相关度评分和文件名，第一条会自动展开。分数是关键词覆盖度为主、向量排名为辅算出来的。" |
| 6 | 问「什么是列表推导式？」 | "这个问题纯向量检索答不出来——嵌入模型对中文区分度差，所以我加了 BM25 关键词检索做第二路召回。" |
| 7 | 问「明天天气怎么样？」 | "知识库里没有的内容，智能模式会用模型自身知识回答，并标注"未使用知识库内容"；切到严格模式它会说未找到相关答案。" |
| 8 | 展开「添加自己的文档」 | "扩充知识库不用改代码：上传 md/txt/pdf，点重建就行。" |

### 7.5 白板画图口述法（最容易被加分的环节）

边画边说，顺序固定为「一条横线 + 两条支路」：

1. 左边画一个文档图标，写 `knowledge_base/*.md`
2. 向右画箭头，标注 **①加载 → ②切分(800/100) → ③向量化(nomic-embed-text) → ④存 Chroma**
3. 在 Chroma 下面再画一个小方框写 **BM25 内存索引**，指向同一个箭头
4. 右边画用户图标，写 `提问`，向左画箭头，标注 **⑤双路召回(各 top-6)**，两条线汇到一个圆圈写 **RRF 融合**
5. 圆圈再连一个小方框写 **覆盖度排序 → top-3**
6. 最后连到 **提示词模板 → Qwen2.5 → 回答 + 带相关度的来源**

画完这张图，整条链路就讲清了；被追问细节时，手指点着对应的方框展开即可。

---

## 八、问答库（被问到就这样答）

### A 组：原理类

**Q1：RAG 和微调有什么区别？**
RAG 是外挂知识、回答时现查，换文档重建索引即可；微调是把知识训进参数里，成本高、更新慢、还容易遗忘旧能力。文档问答、知识频繁更新的场景优先 RAG。

**Q2：为什么一定要检索？直接把整份文档塞给模型不行吗？**
三个原因：① 上下文窗口有限（本项目本地模型 4096 token）；② 塞得越多越贵越慢；③ 无关内容会干扰模型，反而更容易答错（"lost in the middle"现象）。

**Q3：什么是向量？为什么能表示语义？**
嵌入模型把文本映射到高维空间中的点（本项目 768 维），语义相近的文本在空间里距离更近。这样"查资料"就变成了"找最近的邻居"。

**Q4：余弦相似度和欧氏距离有什么区别？**
余弦只看方向、忽略长度，适合比较文本语义；欧氏距离受向量长度影响。多数文本检索用余弦或内积。

**Q5：BM25 是什么？**
一种经典的关键词检索算法，综合考虑"词在本文出现次数（TF）""词在全库多常见（IDF）"和"文档长度归一化"。它不懂语义，但对专有名词、型号、代码符号这类精确匹配非常强。

**Q6：RRF 为什么有效？**
它只依赖排名而不依赖分数，避免了不同检索器的量纲差异；多路都被命中的文档得分自然叠加，相当于"投票"。

### B 组：实现类（针对本项目代码）

**Q7：一次提问，代码里依次发生了什么？**
`app.py` 的「提问」按钮 → `rag.query(question)` → `_rag_chain.invoke()` → 触发 `HybridRetriever._rank_documents()`（向量 top-6 + BM25 top-6 → RRF → 覆盖度排序 → top-3）→ 填模板 → `ChatOllama` 推理 → 返回 `AIMessage` → `query()` 再算一次相关度并判断是否用了知识库 → 界面 `render_sources()` 展示。

**Q8：为什么检索要做两次？**
一次在链里给模型当上下文（只取 top-3），一次在 `query()` 里取带分数和排名的结果给界面展示。两者调用同一个 `_rank_documents()`，结果一致。

**Q9：向量库存在哪？怎么做到第二次启动很快？**
存在 `data/chroma_db/`（Chroma 的 SQLite + 索引文件）。`initialize()` 会先尝试 `load_vectorstore()`，命中就直接复用，只重建内存里的 BM25。

**Q10：BM25 索引为什么不落盘？**
96 个块建索引只要毫秒级，落盘反而增加复杂度；规模上到几万块时再考虑缓存。

**Q11：怎么保证重建不会重复累积？**
`build_vectorstore()` 里先调 `_reset_chroma_collection()` 删掉同名集合，再 `from_documents()`。

**Q12：`RunnablePassthrough()` 在链里干什么？**
把用户问题原样放进字典的 `question` 键，与检索器填的 `context` 键合成一个 dict 传给提示词模板。

**Q13：切换模型为什么不用重建向量库？**
索引是用 nomic-embed-text 建的，和"谁来读它"无关。`set_model()` 只把 `self._llm` 清空并重建链。只有更换嵌入模型才必须重建。

**Q14：怎么判断这次回答有没有用知识库？**
提示词要求模型在"用自身知识"时以【通用知识】开头；`query()` 检查回答开头，界面据此提示"未使用知识库内容"，避免拿无关来源凑数。

**Q15：相关度分数怎么算的？为什么这么算？**
`0.85 × 关键词覆盖度 + 0.15 × (1/向量排名)`。覆盖度是主信号（对中文灵敏），向量排名只做微调。不用向量距离是因为 nomic-embed-text 的中文距离没有区分度。

**Q16：上传文档后做了什么？**
`save_uploaded_files()` 把文件写入 `knowledge_base/`（同名跳过），然后用户点「重建知识库」触发 `initialize(force_rebuild=True)`。

**Q17：如果知识库扩到几万块会怎样？**
BM25 内存索引会变大（可接受），主要瓶颈变成向量库检索与内存占用；那时应考虑分片集合、加 rerank 模型、或换更强的向量模型。

**Q18：为什么 `temperature=0.1`？**
问答要忠实资料、避免发挥；写作类任务才用高温。

### C 组：挑战类（对方在挑刺时）

**Q19：你的检索效果怎么证明有效？**
用 `examples/debug_retrieval.py` 直接看命中块和分数：问「列表推导式」命中覆盖度 1.00 的正确块；而纯向量版本（`examples/minimal_rag.py`）对同一个问题答不出——这是一组可复现的对照实验。

**Q20：大模型答错了，是检索的问题还是模型的问题？**
先用调试工具看 top-3 里有没有正确内容：没有 → 检索问题（调 chunk_size、加关键词、换嵌入模型）；有但答错 → 模型问题（换大模型、调提示词、降温度）。

**Q21：为什么不用 LangChain 内置的 EnsembleRetriever？**
新版本 LangChain 已移除/改动它，而且我需要自己控制融合与排序逻辑（加覆盖度），所以自研了 `HybridRetriever`，只依赖 `BaseRetriever` 契约。

**Q22：项目有什么不足？**
没有 rerank 重排、没有对话记忆（多轮会丢失上下文）、向量库不支持增量更新、`langchain_community.Chroma` 已被标记弃用（应迁移 `langchain-chroma`）、DeepSeek 适配器不支持流式输出。

**Q23：如果让你优化，第一步做什么？**
加 rerank：先召回 20~30 个候选，再用交叉编码器（如 bge-reranker）精排取 3~5 个，能把"命中但不相关"的块挡掉。第二步加多轮对话记忆，第三步换更强的中文嵌入模型。

**Q24：数据隐私怎么保证？**
默认全本地：文档、向量、模型推理都在本机（Ollama + 本地 Chroma）；只有主动选 DeepSeek 时才会把检索到的片段发到云端，这一点在界面上是可选的。

**Q25：这套系统能换成别的领域吗？**
可以，核心逻辑与领域无关。换掉 `knowledge_base/` 里的文档重建即可；如果领域术语特殊（医疗、法律），建议换更强的中文嵌入模型并考虑加 rerank。

---

## 九、自测清单（能答上 18 题以上就算学会）

1. 项目里有哪两条链路？各自的输入输出是什么？
2. `chunk_size` 和 `chunk_overlap` 分别是多少？为什么是这两个数？
3. 切分器的分隔符顺序是什么？为什么"先段落再句子"很重要？
4. 向量维度是多少？哪个模型产生的？
5. `Chroma.from_documents()` 的参数名是什么？和 `Chroma()` 构造函数的区别在哪？
6. 重建索引前为什么要删集合？删集合的函数叫什么？
7. 中文为什么用二元切分？它有什么副作用、怎么弥补？
8. 混合检索的两路各取多少候选？最终给模型几个块？
9. RRF 的公式是什么？为什么不用加权求和？
10. 覆盖度是怎么算的？标题命中和正文命中分别记多少分？
11. 相关度公式是什么？高/中/低的分界线在哪？
12. 界面为什么不显示"低"相关的片段？
13. AI 回答里出现【通用知识】前缀意味着什么？程序怎么利用它？
14. 切换 3B 到 7B 需要重建向量库吗？为什么？
15. 换嵌入模型需要重建吗？为什么？
16. `@st.cache_resource` 和 `@st.cache_data` 分别用在哪、为什么？
17. 一次提问的耗时主要花在哪里？检索占多少？
18. 如果模型答"未找到相关答案"，你怎么排查是哪一环出的问题？
19. 上传文档后要做什么操作才生效？
20. 说出三个本项目已知的不足。

**参考答案要点**（自测后对照）：

1. 入库链路（文档→96 个块→向量库）与问答链路（问题→top-3→回答+来源）。
2. 800 / 100；500 会把标题与代码拆开，太大会混主题。
3. `["\n\n", "\n", "。", "！", "？", ".", " ", ""]`；保证优先在语义边界切。
4. 768 维；nomic-embed-text（Ollama）。
5. `embedding=`；构造函数用 `embedding_function=`，写错会抛参数冲突异常。
6. 因为 Chroma 是追加语义，不清空会重复累积；`_reset_chroma_collection()`。
7. 中文无空格，整句当一个词 BM25 会失效；副作用是产生垃圾二元词，用"知识库里没有的词不计分"+疑问词停用表弥补。
8. 各 6 个；最终 3 个（`RETRIEVAL_VECTOR_K/RETRIEVAL_BM25_K=6`，`RETRIEVAL_K=3`）。
9. `score += 1/(60+rank)`；各路分数纲不同，RRF 只看排名无需归一化。
10. 用 IDF 加权的关键词覆盖率：标题或文件名命中记满分（1.0），正文命中记 0.65，库里没有的词不参与。
11. `0.85×覆盖度 + 0.15×(1/向量排名)`；≥0.5 高、≥0.3 中、其余低。
12. 因为低相关片段会给用户"来源和回答无关"的错觉，折叠起来既保留可查性又不干扰。
13. 模型用的是自身知识、没依据知识库；`query()` 据此设置 `used_knowledge_base=False`，界面提示"未使用知识库内容"。
14. 不需要；对话模型与向量库解耦。
15. 需要；嵌入模型决定向量空间，换模型等于换坐标系。
16. `cache_resource` 缓存 RAGSystem（含模型/向量库，不可序列化的重量级对象）；`cache_data` 缓存"模型是否已下载"这类轻量查询结果（10 秒过期）。
17. 主要花在模型推理（1~9 秒）；检索（向量+BM25+排序）约 0.1~0.3 秒。
18. 先用 `examples/debug_retrieval.py` 看 top-3 有没有正确内容：没有→检索/知识库问题；有→模型或提示词问题。
19. 点「🔄 重建知识库」，让新文档进入向量库（BM25 索引也随之更新）。
20. 无 rerank、无对话记忆、不支持增量更新、`langchain_community.Chroma` 已弃用、DeepSeek 不支持流式。

---

## 十、下一步可以做什么（被问"还能怎么优化"）

| 优先级 | 改进 | 收益 | 代价 |
|--------|------|------|------|
| ★★★ | 加 rerank（bge-reranker / 交叉编码器） | 精排 top-30 → 3，显著减少"命中但无关" | 多一个模型，延迟 +100~300ms |
| ★★★ | 换更强的中文嵌入（bge-m3、Qwen3-Embedding） | 从源头改善中文召回 | 需重建索引，显存/内存占用上升 |
| ★★☆ | 多轮对话记忆 | 支持"它呢？""再详细点" | 要管理上下文长度与历史裁剪 |
| ★★☆ | 增量更新索引 | 加文档不用全量重建 | 要处理去重与更新删除 |
| ★★☆ | 迁移到 `langchain-chroma` | 消除弃用警告，跟上官方 | 改几行导入 |
| ★☆☆ | 流式输出（streaming） | 首字延迟从数秒降到 <1 秒 | 改 LCEL 链与界面渲染方式 |
| ★☆☆ | 引用定位（页码/段落锚点） | 来源可点击跳转 | 需在切分时保留位置信息 |
| ★☆☆ | 评测集与自动化回归 | 量化检索/回答质量 | 要人工标注问题与答案 |

---

## 附录 A：一张纸速查

```
参数：CHUNK_SIZE=800  CHUNK_OVERLAP=100  K=3  VEC_K=6  BM25_K=6  RRF_K=60  BODY=0.65
相关度：0.85×覆盖度 + 0.15×(1/向量排名)   →  ≥0.5 高，≥0.3 中，其余低
覆盖度：Σ(IDF×命中权重) / Σ(IDF)          命中权重：标题/文件名=1.0，正文=0.65
IDF：log((N+1)/(df+1))                     N=96 个块
RRF：score += 1/(60+rank)                  两路都命中则分数叠加
模型：qwen2.5:3b / qwen2.5:7b / deepseek-chat      向量：nomic-embed-text（768 维）
关键函数：load_documents→split_documents→build_vectorstore→HybridRetriever→build_rag_chain→query
文件：rag_core.py(907) app.py(421) examples/minimal_rag.py(80) examples/debug_retrieval.py(27)
```

## 附录 B：三个"一分钟能跑"的验证命令

```bash
# ① 看检索（不调模型，秒级）：确认某个问题命中哪些块、分数多少
python examples/debug_retrieval.py "什么是列表推导式？"

# ② 看骨架（会重建一个独立的小向量库，约 25 秒）：对比纯向量 vs 混合检索的差距
python examples/minimal_rag.py

# ③ 命令行问答（不进网页）：先选模型，再连续提问，quit 退出
python rag_core.py
```

> 学习建议：把 ① 当成你的"实验台"。改 `rag_core.py` 里的任何一个参数（比如把 `BODY_MATCH_CREDIT` 改成 0.3、把 `RETRIEVAL_K` 改成 5），都先跑一次 ①，观察命中块与分数的变化——这是理解 RAG 最快的方式。