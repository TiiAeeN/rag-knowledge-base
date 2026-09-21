# RAG 知识库问答系统

基于 **LangChain + Ollama + ChromaDB** 的 RAG（检索增强生成）知识库问答系统，支持本地 Qwen2.5（3B / 7B）与外接 DeepSeek API 两种推理方式。

## ✨ 特性

- 🔀 **多模型可选**：本地 Qwen2.5-3B / 7B，或外接 DeepSeek API，界面上实时切换
- 🧠 **两种回答方式**：智能问答（知识库优先，知识库以外的问题也能答）/ 严格知识库（只依据知识库回答）
- 📑 **参考来源带相关度**：只列出与问题真正相关的片段（高 / 中）并按相关度排序，无关片段自动折叠
- 🤖 **本地优先**：默认完全本地运行，无需联网，数据隐私安全
- ⚡ **GPU 加速**：支持 NVIDIA CUDA 加速推理
- 📚 **内置 19 份知识文档**：AI 与大模型、11 种编程语言、前端、软件工程、Linux/网络、容器部署、算法
- 📥 **网页直接上传文档**：侧边栏「添加自己的文档」选好文件保存后点重建，知识库立刻扩充
- 📚 **多格式支持**：TXT、Markdown、PDF
- 🔍 **混合检索**：ChromaDB 向量相似度 + BM25 关键词检索（RRF 融合，对中文更友好）
- 🎯 **智能回答**：基于知识库内容生成准确答案
- 💻 **Web 界面**：Streamlit 构建的友好界面

## 🖥️ 系统要求

- Python 3.10+
- NVIDIA GPU（推荐，可选 CPU 运行）
- 8GB+ 内存
- 10GB+ 磁盘空间（用于模型）

## 📦 快速开始

### 1. 安装依赖

```bash
# 激活虚拟环境
cd RAG-project
.venv\Scripts\activate  # Windows

# 安装依赖（已预装）
pip install -r requirements.txt
```

### 2. 安装并启动 Ollama

```bash
# 安装 Ollama（如果还没装）
# 访问 https://ollama.com/download 下载安装

# 拉取模型
ollama pull qwen2.5:3b           # 对话模型 (~2GB，默认)
ollama pull qwen2.5:7b           # 可选：更强的对话模型 (~4.7GB)
ollama pull nomic-embed-text     # 向量模型 (~274MB，必需)

# 提示：7B 也可以在网页侧边栏点击「⬇️ 一键下载该模型」自动下载
```

### 3. 准备知识库文档

项目已内置 **19 份中文知识文档**（放在 `knowledge_base/`，共约 6 万字，切分后约 96 个文本块），启动即可提问：

| 分类 | 内置文档 |
|------|----------|
| AI 与大模型 | `人工智能与大模型基础.md`（机器学习/Transformer/RAG/提示词/Agent）、`机器学习与深度学习实践.md`（数据清洗、sklearn、PyTorch 训练循环、过拟合与部署） |
| 编程语言 | `Python入门指南.md`、`Python进阶指南.md`、`Java基础指南.md`、`JavaScript与TypeScript基础.md`、`Go语言基础.md`、`C++基础要点.md`、`C#与.NET基础.md`、`Rust语言基础.md`、`PHP与Web后端基础.md`、`Kotlin与Swift移动开发基础.md`、`SQL与数据库基础.md` |
| 前端 | `HTMLCSS与前端框架.md`（HTML/CSS 布局、DOM、React、Vue、前后端交互） |
| 软件工程 | `软件工程与开发流程.md`（需求/设计/Git/评审/测试/CI-CD）、`数据结构与算法要点.md` |
| 运维与网络 | `Linux命令与运维基础.md`、`网络与HTTP基础.md`（TCP、状态码、REST、HTTPS、排查）、`容器与云原生部署.md`（Docker/Compose/K8s/Nginx/上线回滚） |

想继续扩充知识面，只要把新文档丢进目录再重建索引即可：

```
RAG-project/
├── knowledge_base/                 # ← 把文档放这里
│   ├── Python入门指南.md            # 内置
│   ├── 你的新文档.md                # 自行添加
│   ├── 参考手册.pdf
│   └── ...
```

添加方式有两种：

1. **网页上传（最省事）**：侧边栏展开「➕ 添加自己的文档」→ 选择 .md / .txt / .pdf（可多选）→ 点「📥 保存到知识库」→ 点「🔄 重建知识库」，新内容立刻生效。
2. **直接拷文件**：把文档复制进 `knowledge_base/` 目录，再点「🔄 重建知识库」。

重建会先清空旧向量集合再重新写入，不会重复累积。

**支持的格式：**
- `.txt` - 纯文本
- `.md` - Markdown（推荐，`##` 小标题结构能显著提升检索命中率）
- `.pdf` - PDF 文档

**写文档的小建议：** 一节控制在 200~600 字、代码块标注语言、把关键词写进标题，检索效果最好。

### 4. 启动系统

#### 方式 A：Web 界面（推荐）

```bash
streamlit run app.py
```

然后浏览器打开 `http://localhost:8501`

#### 方式 B：命令行

```bash
python rag_core.py
```

#### 方式 C：双击启动（Windows）

双击项目目录里的 `启动.bat`，会自动用虚拟环境启动界面（无需手动激活环境）。

## 🏗️ 项目结构

```
RAG-project/
├── app.py              # Streamlit Web 界面（推荐）
├── app_simple.py       # Streamlit 简化界面
├── rag_core.py         # RAG 核心逻辑（含多模型注册与切换）
├── knowledge_base/     # 知识库文档目录
├── data/               # 数据存储（向量数据库）
│   └── chroma_db/      # ChromaDB 持久化数据
├── .env.example        # 环境变量示例（DeepSeek API Key）
├── .venv/              # Python 虚拟环境
├── examples/           # 可运行的学习示例
│   ├── check_env.py         # 环境自检：版本/依赖/模型/文档/向量库
│   ├── minimal_rag.py       # 80 行最小 RAG（看懂骨架）
│   └── debug_retrieval.py   # 检索调试：不调模型就能看命中块与分数
├── 启动.bat            # 双击启动（Windows）
├── requirements.txt    # 依赖列表
├── RAG实现步骤与配置清单.md  # 工具 + 配置 + 23 步实现 + 速查 + 复现命令
├── RAG实现学习手册.md   # 学习+复现+口述稿（想讲明白就看这份）
├── RAG项目完整文档.md   # 数据流 + 行号索引 + 2 分钟口述稿
└── README.md           # 本文件
```

## 🔧 配置说明

### 模型配置（rag_core.py）

```python
DEFAULT_MODEL = "qwen2.5:3b"          # 默认对话模型（界面中可随时切换）
EMBEDDING_MODEL = "nomic-embed-text"  # 向量化模型（固定用本地 Ollama）
```

可选的对话模型登记在 `MODEL_REGISTRY` 中：

| key | 说明 |
|-----|------|
| `qwen2.5:3b` | 本地 Ollama，轻量快速（默认） |
| `qwen2.5:7b` | 本地 Ollama，回答质量更高 |
| `deepseek-chat` | 外接 DeepSeek API，需要 API Key |

切换模型只替换对话模型，**不需要重建向量库**；也可以在注册表中自行添加其他 Ollama 模型。

### DeepSeek API 配置

复制 `.env.example` 为 `.env` 并填入密钥：

```ini
DEEPSEEK_API_KEY=sk-你的密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

也可以直接在网页侧边栏填写 API Key，或设置同名环境变量（优先级：界面输入 > 环境变量 > 代码默认值）。

### 分块与检索配置

```python
CHUNK_SIZE = 800          # 文本块大小（字符数，太小会把标题和正文拆散）
CHUNK_OVERLAP = 100       # 相邻块重叠字符数

RETRIEVAL_K = 3           # 最终交给模型的文本块数量
RETRIEVAL_VECTOR_K = 6    # 向量检索候选数
RETRIEVAL_BM25_K = 6      # BM25 关键词检索候选数
USE_HYBRID_RETRIEVAL = True  # 向量 + BM25 混合检索
```

> 换用更大的对话模型（如 7B / DeepSeek）时，可以适当调大 `RETRIEVAL_K`（比如 4~5）获得更完整的上下文。

**参考来源的相关度是怎么算的？**

1. 先从问题里提取「实词」（去掉「什么 / 怎么 / 区别」这类疑问词，用中英混合分词），并给每个词算 IDF 权重——越冷门的词越能说明主题。
2. 再看每个片段覆盖了多少这些词：出现在**标题或文件名**里算满分，只出现在正文里打 0.65 折，知识库里根本不存在的词不参与计算。
3. 相关度 = 0.85 × 关键词覆盖度 + 0.15 × 向量排名得分；排序时以覆盖度为主、向量/BM25 融合排名为辅。

这样问「Transformer 架构」时，含 Transformer 内容的片段会排在前面，而只命中「架构」两字的无关片段会被压到「其他检索到的片段」里折叠起来。相关度 ≥0.5 标「高」、≥0.3 标「中」、其余标「低」，界面只把「高 / 中」当作参考来源展示。

### 回答方式配置

```python
ANSWER_MODE_SMART = "smart"       # 智能问答（默认）：知识库优先，知识库没有的内容用模型自身知识回答
ANSWER_MODE_KB_ONLY = "kb_only"   # 严格知识库：只依据知识库回答
DEFAULT_ANSWER_MODE = ANSWER_MODE_SMART
```

> 智能问答适合日常使用（问答范围不受知识库限制）；严格知识库适合演示/答辩，保证每句回答都有知识库依据。切换是即时的，不需要重建向量库。

### 可选模型

| 模型 | 大小 | 用途 | 4060 推荐 |
|------|------|------|-----------|
| `qwen2.5:3b` | ~2GB | 本地对话，平衡之选 | ✅ **推荐** |
| `qwen2.5:7b` | ~4.7GB | 本地对话，更强能力 | ✅ 可用 |
| `deepseek-chat` | 云端 | 外接 API 对话，能力最强 | ✅ 需要联网 |
| `nomic-embed-text` | ~274MB | 向量嵌入 | ✅ 必需 |

## 📖 学习资料（想搞懂原理看这几份）

| 资料 | 内容 | 适合 |
|------|------|------|
| `RAG实现步骤与配置清单.md` | 用了什么工具、代码写在哪、怎么配置、23 步实现清单、符号行号速查、从零复现命令 | 照着做一遍 / 查配置 |
| `RAG实现学习手册.md` | 逐模块代码精讲、12 个设计决策、从零复现 8 步、口述稿（30 秒/2 分钟/5 分钟）、25 问问答库、20 题自测 | 系统学习 + 答辩准备 |
| `RAG项目完整文档.md` | 数据流图、行号索引、面试口述稿 | 快速回顾实现细节 |
| `examples/` | `check_env.py`（环境自检）、`minimal_rag.py`（80 行最小版）、`debug_retrieval.py`（检索调试） | 动手验证 |

```bash
# 环境自检：一眼看出哪一环没配好
python examples/check_env.py

# 看检索效果（不调用大模型，秒级出结果）
python examples/debug_retrieval.py "什么是列表推导式？"

# 跑最小版，对比纯向量检索和混合检索的差距
python examples/minimal_rag.py
```

## 🎯 使用示例

### Web 界面使用

1. 在左侧「🤖 对话模型」中选择模型（Qwen2.5-3B / Qwen2.5-7B / DeepSeek-V3）
2. 在「💡 回答方式」中选择：智能问答（默认，想问什么问什么）或严格知识库（只答知识库内容）
3. （可选）在「➕ 添加自己的文档」里上传自己的资料，保存后点「🔄 重建知识库」
4. 点击「🚀 初始化 RAG 系统」
5. 在输入框输入问题
6. 点击「🔍 提问」查看结果
7. 右侧显示参考来源：只列出与问题相关的片段并标注相关度（高 / 中），无关片段折叠在下方；回答下方会标注所用模型

> 智能问答模式下，知识库以外的回答会在界面顶部标明「来自模型自身知识」，参考来源区也会提示「未使用知识库内容」；严格知识库模式下这类问题会回答「未找到相关答案」。

### 示例问题

```
Python 中如何定义函数？
什么是列表推导式？
如何处理文件读写？
异常处理的语法是什么？
```

## 🛠️ 故障排查

### 问题：Ollama 连接失败

```bash
# 检查 Ollama 是否运行
ollama --version

# 检查模型是否下载
ollama list
```

### 问题：切换到 Qwen2.5-7B 后提问没有响应

7B 模型约 4.7GB，需要先下载（首次使用会自动下载，耗时取决于网速）：

```bash
ollama pull qwen2.5:7b
```

或在网页侧边栏点击「⬇️ 一键下载该模型」。

### 问题：DeepSeek API 报错

- 检查 API Key 是否正确、账户是否有余额
- 确认网络可以访问 `https://api.deepseek.com`
- 在侧边栏「DeepSeek API Key」输入框中重新填写，或在 `.env` 中配置

### 问题：回答总是「未找到相关答案」

- 如果问的是**知识库以外**的内容（天气、常识、写作等）：把侧边栏「💡 回答方式」切到「智能问答」，系统就会用模型自身知识回答；在「严格知识库」模式下这类问题一律回答「未找到相关答案」，这是设计如此，不是故障
- 如果问的是**知识库里的内容**也答不出来：
  1. 点侧边栏「🔄 重建知识库」——改过 `CHUNK_SIZE` 或换过向量模型后必须重建
  2. 确认文档已放进 `knowledge_base/`，且格式为 .md / .txt / .pdf
  3. 知识库很大或问题偏专有名词时，可调大 `rag_core.py` 中的 `RETRIEVAL_K`（默认 3）

### 问题：CUDA/GPU 不工作

确保安装了支持 CUDA 的 PyTorch：
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu124
```

### 问题：向量数据库报错

删除并重建：
```bash
rm -rf data/chroma_db/
# 然后重新初始化
```

## 📊 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| LLM 框架 | LangChain | RAG 流程编排 |
| 对话模型 | Ollama + Qwen2.5-3B/7B 或 DeepSeek API | 回答生成（可切换） |
| 向量模型 | nomic-embed-text | 文本向量化 |
| 向量数据库 | ChromaDB | 相似度检索 |
| 关键词检索 | rank-bm25 | BM25 算法 |
| Web 界面 | Streamlit | 用户界面 |

## 📄 License

MIT License

---

*Built with ❤️ using local AI*
