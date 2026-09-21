- # RAG 系统 · 实现步骤与配置清单

> 用途：① 复现时当施工图；② 被问"你具体做了什么"时按步骤讲；③ 想改配置时查表。
> 配套：`RAG实现学习手册.md`（讲原理）、`RAG项目完整文档.md`（讲数据流）、本文件（讲**工具、位置、配置**）。

**三种用法：**

| 你想干什么 | 看哪一部分 |
|-----------|-----------|
| 知道每一步用了什么工具、代码写在哪个文件哪一行 | 第三部分（23 步清单） |
| 想改参数/换模型/换知识库 | 第二部分（配置总览）+ 第四部分（速查表） |
| 从零跑通一遍 | 第五部分（命令序列） |

---

# 第一部分　用了什么工具

## 1.1 运行环境与外部服务

| 工具 | 版本 | 作用 | 安装方式 | 本项目里的痕迹 |
|------|------|------|---------|---------------|
| Windows | 10/11 | 运行平台 | — | 路径 `C:\Users\Azathoth\RAG-project` |
| Python | 3.14.7 | 运行语言 | 由 uv 自动下载管理（**不在系统 PATH**） | `%APPDATA%\uv\python\cpython-3.14-windows-x86_64-none` |
| uv | 0.12.13 | 下 Python + 建虚拟环境 + 装依赖 | 本机在 `%LOCALAPPDATA%\hermes\bin\uv.exe` | `.venv\pyvenv.cfg` 里的 `uv = 0.12.13` |
| venv | uv 创建 | 虚拟环境 | `uv venv --python 3.14 .venv` | `.venv\Scripts\python.exe` |

> ⚠️ **本机实测的两个前提**，照抄任何教程的命令前先看这里：
> 1. 系统 PATH 里的 `python` 是 **3.10.10**（`%LOCALAPPDATA%\Programs\Python\Python310\`），**不是** `.venv` 用的 3.14.7。所以 `python -m venv .venv` 会建出 3.10 环境，和现有 `.venv` 不是一回事。
> 2. PowerShell 执行策略全部为 `Undefined`（等价 `Restricted`），`.venv\Scripts\activate` **会被拒绝执行**，报「因为在此系统上禁止运行脚本」。绕法见第 1 步。
> 3. `.venv\Scripts\` 里**没有 `pip.exe`**（uv 建 venv 的默认行为），所以 `pip install` 会装到全局 3.10。必须用 `python -m pip`，见第 2 步。
| Ollama | 0.34.0 | 本地模型运行时（HTTP 服务，默认 11434 端口） | https://ollama.com/download | `rag_core.py:50` 的 `OLLAMA_HOST` |
| DeepSeek API | 云端（可选） | 外接对话模型 | 申请 API Key | `rag_core.py:56-58` |

## 1.2 模型清单

| 模型 | 大小 | 类型 | 谁在用 | 配置位置 |
|------|------|------|--------|---------|
| `qwen2.5:3b` | ~2GB | 对话（默认） | 回答生成 | `rag_core.py:53` `DEFAULT_MODEL` |
| `qwen2.5:7b` | ~4.7GB | 对话（可选，**本项目未下载**） | 回答生成 | `rag_core.py:135-141` |
| `deepseek-chat` | 云端 | 对话（可选） | 回答生成 | `rag_core.py:142-148` |
| `nomic-embed-text` | ~274MB | 向量化（768 维） | 建索引 + 检索 | `rag_core.py:48` `EMBEDDING_MODEL` |

## 1.3 Python 依赖包（13 个）

| 库 | 实测版本 | 干什么 | 声明处 | 代码里 import 的位置 |
|----|---------|--------|--------|-------------------|
| `langchain` | 1.4.0 | 编排框架（顶层包） | requirements.txt | 间接使用 |
| `langchain-core` | 1.6.3 | LCEL、Runnable、Document、Prompt | 随 langchain 安装 | `rag_core.py:25-29` |
| `langchain-community` | 0.4.2 | 文档加载器 + Chroma 封装 | requirements.txt | `rag_core.py:20-22` |
| `langchain-ollama` | 1.1.0 | 对接 Ollama（对话 + 向量） | requirements.txt | `rag_core.py:23-24` |
| `langchain-text-splitters` | 1.1.2 | 递归字符切分 | 随 langchain 安装 | `rag_core.py:19` |
| `chromadb` | 1.5.9 | 向量数据库（本地持久化） | requirements.txt | `rag_core.py:223`（清空集合时用） |
| `rank-bm25` | 0.2.2 | BM25 关键词检索 | requirements.txt | `rag_core.py:33`（未装则退化为纯向量） |
| `pypdf` | 6.18.1 | 读取 PDF | requirements.txt | `rag_core.py:21` |
| `streamlit` | 1.63.0 | Web 界面 | requirements.txt | `app.py:10` |
| `openai` | 3.13.0 | 调用 DeepSeek（OpenAI 兼容接口） | requirements.txt | `rag_core.py:416` |
| `python-dotenv` | 1.2.3 | 读取 `.env` 环境变量 | requirements.txt | `rag_core.py:38-40` |
| `numpy` | 2.5.3 | 向量运算（Chroma 依赖） | 自动带入 | 间接使用 |
| `pydantic` | 2.13.5 | 数据校验（Retriever 基类依赖） | 自动带入 | `rag_core.py:30` `PrivateAttr` |

> `requirements.txt` 里还写了 `sentence-transformers` / `torch` / `transformers`（早期备选方案），实际项目走的是 Ollama，这三个不是必需；`langchain-openai` 被注释掉了——没装它时系统会自动用内置的 `DeepSeekChat` 适配器。

**一键检查这些是否都装好：**

```bash
python examples/check_env.py
```

输出全 ✅ 才算环境就绪（它会检查 Python 版本、10 个必需包、Ollama 服务与模型、知识库文档数、向量库块数）。

---

# 第二部分　如何配置（配置总览）

## 2.1 环境变量（`.env`）

复制 `.env.example` 为 `.env`，放在项目根目录：

```ini
# 外接 DeepSeek API 配置（使用 DeepSeek 模型时填写）
DEEPSEEK_API_KEY=sk-你的DeepSeek密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 本地 Ollama 服务地址（默认 http://127.0.0.1:11434，一般无需修改）
# OLLAMA_HOST=http://127.0.0.1:11434
```

| 变量 | 读取位置 | 不填会怎样 |
|------|---------|-----------|
| `DEEPSEEK_API_KEY` | `rag_core.py:57` | 选 DeepSeek 时报错（有硬编码兜底值，见 2.5 安全提醒） |
| `DEEPSEEK_BASE_URL` | `rag_core.py:58` | 用默认 `https://api.deepseek.com/v1` |
| `OLLAMA_HOST` | `rag_core.py:50` | 用默认 `http://127.0.0.1:11434` |

优先级：**界面输入 > 环境变量 > 代码里的默认值**。

Windows PowerShell 里临时设置（不写文件）：

```powershell
$env:DEEPSEEK_API_KEY="sk-xxxx"      # 只在当前窗口生效
$env:PYTHONIOENCODING="utf-8"        # 解决控制台中文乱码
```

## 2.2 核心配置常量（`rag_core.py:44-82`）——最重要的一张表

```python
# 路径
KNOWLEDGE_BASE_DIR = Path(__file__).parent / "knowledge_base"     # 第 45 行
CHROMA_PERSIST_DIR = Path(__file__).parent / "data" / "chroma_db" # 第 46 行

# 模型
EMBEDDING_MODEL = "nomic-embed-text"        # 第 48 行  向量模型
CHROMA_COLLECTION_NAME = "langchain"        # 第 49 行  集合名（重建时按它删）
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")  # 第 50 行
DEFAULT_MODEL = "qwen2.5:3b"                # 第 53 行  默认对话模型

# 切分
CHUNK_SIZE = 800        # 第 61 行
CHUNK_OVERLAP = 100     # 第 62 行

# 检索
RETRIEVAL_K = 3          # 第 65 行  最终交给模型几块
RETRIEVAL_VECTOR_K = 6   # 第 66 行  向量候选数
RETRIEVAL_BM25_K = 6     # 第 67 行  关键词候选数
RRF_K = 60               # 第 68 行  RRF 参数
USE_HYBRID_RETRIEVAL = True   # 第 69 行  是否启用混合检索
BODY_MATCH_CREDIT = 0.65      # 第 70 行  正文命中的相关度折扣

# 回答模式
ANSWER_MODE_SMART = "smart"        # 第 73 行
ANSWER_MODE_KB_ONLY = "kb_only"    # 第 74 行
DEFAULT_ANSWER_MODE = ANSWER_MODE_SMART   # 第 79 行
```

| 配置项 | 现在 | 调大的效果 | 调小的效果 | 改完要重建吗 |
|--------|------|-----------|-----------|-------------|
| `CHUNK_SIZE` | 800 | 上下文更完整，但一块混多主题 | 检索更精准，但可能拆散代码块 | **要** |
| `CHUNK_OVERLAP` | 100 | 边界更安全，索引体积变大 | 可能丢边界信息 | **要** |
| `RETRIEVAL_K` | 3 | 模型看到更多资料，变慢、可能引入噪声 | 更快，但可能缺信息 | 不要 |
| `RETRIEVAL_VECTOR_K` | 6 | 向量召回更多候选 | 可能漏掉正确块 | 不要 |
| `RETRIEVAL_BM25_K` | 6 | 关键词召回更多候选 | 同上 | 不要 |
| `RRF_K` | 60 | 各路排名的影响更平均 | 头部结果权重更集中 | 不要 |
| `BODY_MATCH_CREDIT` | 0.65 | 正文命中更被认可（来源标注更宽松） | 更强调标题命中（来源更严格） | 不要 |
| `EMBEDDING_MODEL` | nomic-embed-text | — | — | **要**（换模型等于换坐标系） |
| `DEFAULT_MODEL` | qwen2.5:3b | — | — | 不要 |
| `KNOWLEDGE_BASE_DIR` | knowledge_base | — | — | **要** |

## 2.3 界面层配置（`app.py`）

| 配置 | 位置 | 说明 |
|------|------|------|
| 页面标题/图标/布局 | `app.py:30-35` | `st.set_page_config(...)`，改标题、图标、侧边栏默认展开 |
| 顶部渐变标题样式 | `app.py:38-50` | 一段 CSS，改颜色改这里 |
| RAG 全局单例缓存 | `app.py:53-56` | `@st.cache_resource`——保证模型只加载一次 |
| Ollama 检查缓存 10 秒 | `app.py:59-62` | `@st.cache_data(ttl=10)` |
| 上传文件格式白名单 | `app.py:164` | `KNOWLEDGE_FILE_SUFFIXES = (".md", ".txt", ".pdf")` |
| 侧边栏布局顺序 | `app.py:305-315` | 模型 → 回答方式 → 知识库状态 → 操作 → 系统信息 |
| 主区左右分栏比例 | `app.py:318` | `st.columns([3, 2])`，左边问答、右边来源 |

## 2.4 改配置后的"要不要重建"判定

| 改动类型 | 例子 | 是否重建索引 | 原因 |
|---------|------|-------------|------|
| 换对话模型 | 3B → 7B → DeepSeek | ❌ 不用 | 索引是用向量模型建的，和谁读它无关 |
| 换回答模式 | 智能 → 严格 | ❌ 不用 | 只换提示词模板 |
| 调检索参数 | K 值、RRF_K | ❌ 不用 | 检索时才生效 |
| 改知识库文档 | 增删改 .md | ✅ **要** | 文档变了，块和向量都得重算 |
| 换向量模型 | nomic → bge-m3 | ✅ **要** | 向量空间变了，旧向量不可比 |
| 改切分参数 | chunk_size/overlap | ✅ **要** | 块变了，向量得重算 |

## 2.5 安全提醒

`rag_core.py:57` 有一行硬编码兜底 Key：

```python
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-25f0d8...")   # ← 建议删掉默认值
```

建议改成 `os.getenv("DEEPSEEK_API_KEY", "")`，只用 `.env` 或界面输入提供 Key；另外 `.env` 不要提交到公开仓库。

---
# 第三部分　分步实现清单（23 步）

> 每一步都按同一格式：**用了什么工具 → 代码写在哪 → 关键代码 → 怎么配置 → 怎么验证**。
> 想边看边做，就按顺序往下走；只想查位置，直接看"代码位置"那行。

### 第 1 步：建虚拟环境

> ✅ **本项目这一步已经做完了**，`.venv\` 已存在且是 Python 3.14.7。下面记录的是原理和「万一要重建」的做法 —— 日常直接用「方式 A」那一小节即可，不用重做。

- **工具**：`uv` 0.12.13（本机路径 `%LOCALAPPDATA%\hermes\bin\uv.exe`）
- **位置**：`C:\Users\Azathoth\RAG-project\.venv\`
- **命令（PowerShell）**：

```powershell
cd C:\Users\Azathoth\RAG-project

# 建虚拟环境（uv 会自动找/下载 Python 3.14，并生成 pyvenv.cfg）
uv venv --python 3.14 .venv
```

- **配置**：`pyvenv.cfg` 记录「这份环境是用哪个 Python 建的」，无需手动改
- **验证**：`.venv\Scripts\python.exe -V` 输出 `Python 3.14.7`

#### 关于「激活」—— 本机必须注意

`activate` 做的事只是把 `.venv\Scripts` 插到 PATH 最前面，**并不是必须的**。本机 PowerShell 执行策略为 `Restricted`（`Get-ExecutionPolicy -List` 全部 `Undefined`），直接激活会报「因为在此系统上禁止运行脚本」。三种处理方式：

```powershell
# 方式 A（最省事，推荐）：不激活，直接用 venv 里的 exe —— 启动.bat 就是这么写的
.venv\Scripts\python.exe 脚本.py
.venv\Scripts\streamlit.exe run app.py

# 方式 B：只放行当前用户的脚本，之后 activate 就能正常用（一次性设置）
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.venv\Scripts\Activate.ps1
# 激活成功的标志：命令行前面出现 (.venv)

# 方式 C：不改系统设置，本次绕过
.venv\Scripts\Activate.ps1 -ExecutionPolicy Bypass
```

> ⚠️ **不要用 `python -m venv .venv` 重建**：本机 PATH 里的 `python` 是 3.10.10，会建出 3.10 环境，与现有 `.venv`（3.14.7）不一致，而且会清掉已经装好的依赖。

### 第 2 步：声明并安装依赖

- **工具**：`pip`（用 `python -m pip` 调用）+ `requirements.txt`
- **位置**：`requirements.txt`（共 31 行，按用途分组：LangChain 核心 / 向量数据库 / 文档加载 / Web 界面 / 混合检索 / 外接 API / .env）
- **关键内容**：

```text
langchain-community>=0.3.0      # 文档加载器 + Chroma 封装
langchain-ollama>=0.2.0         # 对接 Ollama 的对话与嵌入
chromadb>=0.5.0                 # 向量数据库
pypdf>=4.0.0                    # 读 PDF
streamlit>=1.30.0               # Web 界面
rank-bm25>=0.2.2                # 关键词检索
openai>=1.0.0                   # 外接 DeepSeek
python-dotenv>=1.0.0            # 读 .env
```

- **配置**（本项目已完成，实测版本见第一部分 1.3）：

```powershell
# ⚠️ 不要直接写 pip install —— 原因见下方说明
python -m pip install -r requirements.txt

# 或者完全不激活：
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 或者用 uv（在项目根目录执行，会自动找到 .venv）：
uv pip install -r requirements.txt
```

> ⚠️ **本机为什么不能直接写 `pip install`**：`.venv\Scripts\` 里只有 `pip3.exe` / `pip3.14.exe`，**没有 `pip.exe`**（uv 建 venv 的默认行为）。所以即使激活成功，PATH 里也找不到 venv 的 `pip.exe`，会继续往下命中全局 `Python310\Scripts\pip.exe` —— **依赖会被装进全局 Python 3.10 而不是 `.venv`**，项目照样跑不起来，还污染了系统环境。模拟激活后的实测对比：
>
> | 命令 | 实际指向 | 结论 |
> |------|---------|------|
> | `python -V` | Python 3.14.7 | ✅ venv 的 |
> | `python -m pip -V` | `.venv\Lib\site-packages\pip`（python 3.14） | ✅ venv 的 |
> | `pip -V` | `Python310\lib\site-packages\pip`（python 3.10） | ❌ 全局的 |
>
> `-m` 是 python 自己的参数，意思是「用这个 python 去加载 pip 模块」，跳过了「沿 PATH 找 `pip.exe`」这一步，从源头保证装对地方。**记这一条就够了。**

- **验证**：`.venv\Scripts\python.exe examples\check_env.py` → 依赖段落全 ✅
  （若直接写 `python examples\check_env.py`，会用全局 3.10 去跑，依赖段落会**全 ❌** —— 那是查错对象了，不代表环境有问题）

### 第 3 步：安装 Ollama 并拉取模型

- **工具**：Ollama 0.34.0（提供本地 HTTP 推理服务）
- **位置**：模型存在 Ollama 自己的目录；项目只通过 `OLLAMA_HOST` 访问
- **命令**：

```bash
# 装好 Ollama 后（桌面版或命令行）
ollama pull qwen2.5:3b            # 对话模型，约 2GB
ollama pull nomic-embed-text      # 向量模型，约 274MB
ollama pull qwen2.5:7b            # 可选，约 4.7GB
ollama list                       # 查看已下载的模型
```

                         
- **验证**：`ollama list` 能看到两个模型；`examples/check_env.py` 的 Ollama 段落全 ✅
- **界面里也能下**：`app.py:107-128` 提供了「⬇️ 一键下载该模型」，走 `pull_ollama_model()`（`rag_core.py:187-217`）

### 第 4 步：准备知识库文档

- **工具**：无（纯文件）
- **位置**：`knowledge_base/`（当前 19 份 `.md`，约 6 万字）
- **配置**：支持 `.md` / `.txt` / `.pdf`；文件名用中文主题名最好（检索时文件名会加权，见第 13 步）
- **验证**：`examples/check_env.py` → 「知识库文档」段落显示 19 个文档

### 第 5 步：写配置常量

- **工具**：标准库 `pathlib` / `os`
- **位置**：`rag_core.py:44-82`（配置区）
- **关键代码**：

```python
KNOWLEDGE_BASE_DIR = Path(__file__).parent / "knowledge_base"
CHROMA_PERSIST_DIR = Path(__file__).parent / "data" / "chroma_db"
EMBEDDING_MODEL = "nomic-embed-text"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
RETRIEVAL_K = 3
RRF_K = 60
```
- **配置**：逐项含义与调参影响见本文第二部分 2.2
- **验证**：`python -c "import rag_core; print(rag_core.CHUNK_SIZE, rag_core.RETRIEVAL_K)"`

### 第 6 步：定义模型注册表（多模型的地基）

- **工具**：标准库 `dataclasses`
- **位置**：
  - `ModelSpec` 数据类：`rag_core.py:116-124`
  - `MODEL_REGISTRY` 注册表：`rag_core.py:127-149`
  - `available_models()`：`rag_core.py:152-154`
  - `resolve_model()`：`rag_core.py:157-168`
- **关键代码**：

```python
@dataclass(frozen=True)
class ModelSpec:
    key: str        # 唯一标识
    label: str      # 界面显示名
    provider: str   # "ollama" 或 "deepseek"
    model: str      # 后端真实模型名
    description: str

MODEL_REGISTRY = {
    "qwen2.5:3b":    ModelSpec(..., provider="ollama",   model="qwen2.5:3b"),
    "qwen2.5:7b":    ModelSpec(..., provider="ollama",   model="qwen2.5:7b"),
    "deepseek-chat": ModelSpec(..., provider="deepseek", model="deepseek-chat"),
}
```

- **配置**：**新增一个模型 = 在字典里加一条**，不用改任何逻辑；`resolve_model()` 对未登记的 key 会兜底成"本地 Ollama 模型"
- **验证**：`python -c "from rag_core import available_models; [print(s.key, s.label) for s in available_models()]"`

### 第 7 步：创建对话模型（本地 / 外接两条路）

- **工具**：`langchain-ollama.ChatOllama`、`langchain-openai.ChatOpenAI`（可选）、`openai` SDK（兜底）
- **位置**：
  - `create_llm()`：`rag_core.py:453-478`（按 provider 分支）
  - `DeepSeekChat` 适配器：`rag_core.py:402-450`（未装 langchain-openai 时使用）
- **关键代码**：

```python
def create_llm(model_key=None, api_key=None, temperature=0.1, num_ctx=4096):
    spec = resolve_model(model_key)
    if spec.provider == "deepseek":
        key = api_key or DEEPSEEK_API_KEY
        if not key:
            raise ValueError("使用 DeepSeek 需要提供 API Key...")
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            return DeepSeekChat(model=spec.model, api_key=key, temperature=temperature)
        return ChatOpenAI(model=spec.model, api_key=key, base_url=DEEPSEEK_BASE_URL, temperature=temperature)
    return ChatOllama(model=spec.model, temperature=temperature, num_ctx=num_ctx)
```

- **配置**：
  - `temperature=0.1`：问答要忠实资料（改大更"有创意"，不适合问答）
  - `num_ctx=4096`：本地模型上下文窗口，太小会截断检索到的资料
  - DeepSeek Key 优先级：界面输入 > `DEEPSEEK_API_KEY` 环境变量 > 代码默认值
- **验证**：`python -c "from rag_core import create_llm; print(create_llm('qwen2.5:3b'))"`（会打印 ChatOllama 实例）
- **注意**：DeepSeek 是外网调用，本项目开发环境**没有实测过真实 API**，只验证了代码链路——你本地填好 Key 后自测一次即可

### 第 8 步：封装 Ollama 服务能力（列表 / 检查 / 一键下载）

- **工具**：标准库 `urllib.request` + `json`（不额外装包）
- **位置**：
  - `list_ollama_models()`：`rag_core.py:171-178`（GET `/api/tags`）
  - `is_ollama_model_ready()`：`rag_core.py:181-184`
  - `pull_ollama_model()`：`rag_core.py:187-217`（POST `/api/pull`，流式读进度）
- **配置**：服务地址来自 `OLLAMA_HOST`；超时 5 秒（列表）/ 3600 秒（下载）
- **验证**：`python -c "from rag_core import list_ollama_models; print(list_ollama_models())"`

### 第 9 步：文档加载

- **工具**：`langchain-community` 的 `DirectoryLoader`、`TextLoader`、`PyPDFLoader`
- **位置**：`rag_core.py:552-587` `RAGSystem.load_documents()`
- **关键代码**：

```python
for ext in ["*.txt", "*.md"]:
    loader = DirectoryLoader(str(self.knowledge_base_dir), glob=ext,
                             loader_cls=TextLoader,
                             loader_kwargs={"encoding": "utf-8"})   # ← 中文必须
    documents.extend(loader.load())

for pdf_path in self.knowledge_base_dir.glob("*.pdf"):
    documents.extend(PyPDFLoader(str(pdf_path)).load())              # PDF 单独处理
```

- **配置**：`KNOWLEDGE_BASE_DIR`（`rag_core.py:45`）；每份文件独立 try/except，坏文件不影响整库
- **验证**：重建时看日志 `✅ 共加载 19 个文档片段`

### 第 10 步：文本切分

- **工具**：`langchain-text-splitters` 的 `RecursiveCharacterTextSplitter`
- **位置**：`rag_core.py:589-601` `split_documents()`
- **关键代码**：

```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,         # 800
    chunk_overlap=CHUNK_OVERLAP,   # 100
    separators=["\n\n", "\n", "。", "！", "？", ".", " ", ""],
)
chunks = text_splitter.split_documents(documents)
```

- **配置**：`CHUNK_SIZE` / `CHUNK_OVERLAP`（`rag_core.py:61-62`）；改这两个必须重建索引
- **验证**：日志 `✅ 分割完成，共 96 个文本块`

### 第 11 步：向量化与入库（含"重建前清空"）

- **工具**：`langchain-ollama.OllamaEmbeddings` + `langchain-community.Chroma` + `chromadb`
- **位置**：
  - 清空旧集合：`rag_core.py:220-234` `_reset_chroma_collection()`
  - 建库：`rag_core.py:603-616` `build_vectorstore()`
  - 复用已有库：`rag_core.py:618-629` `load_vectorstore()`
- **关键代码**：

```python
def build_vectorstore(self, chunks):
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    _reset_chroma_collection()                       # 先删旧集合，避免重复累积
    return Chroma.from_documents(
        documents=chunks,
        embedding=self.embeddings,                   # ← 参数名是 embedding
        persist_directory=str(CHROMA_PERSIST_DIR),
    )
```

- **配置**：`EMBEDDING_MODEL` / `CHROMA_PERSIST_DIR` / `CHROMA_COLLECTION_NAME`（`rag_core.py:46-49`）
- **验证**：`data/chroma_db/` 出现 `chroma.sqlite3`；`examples/check_env.py` 显示「集合 langchain：96 个文本块」
- **易踩的坑**：`Chroma.from_documents()` 用 `embedding=`，而 `Chroma()` 构造函数用 `embedding_function=`，写错会报 `got multiple values for keyword argument 'embedding_function'`

### 第 12 步：中文分词（不装分词库）

- **工具**：标准库 `re`
- **位置**：
  - `tokenize_for_bm25()`：`rag_core.py:248-256`
  - `extract_query_terms()`：`rag_core.py:259-266`
  - 疑问词停用表：`rag_core.py:238-243`；标题正则：`rag_core.py:245`
- **关键代码**：

```python
def tokenize_for_bm25(text):
    tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())        # 英文整词
    for run in re.findall(r"[\u4e00-\u9fff]+", text):          # 中文二元切分
        tokens.extend(run[i:i+2] for i in range(len(run) - 1))
    return tokens
```

- **配置**：想过滤更多疑问词，就往 `QUESTION_STOPWORDS` 里加
- **验证**：`python -c "from rag_core import tokenize_for_bm25; print(tokenize_for_bm25('什么是列表推导式'))"`

### 第 13 步：混合检索器 HybridRetriever（核心，可拆成 6 小步）

- **工具**：`langchain-core` 的 `BaseRetriever` + `pydantic.PrivateAttr` + `rank-bm25`
- **位置**：`rag_core.py:269-382`，内部结构：

| 小步 | 干什么 | 行号 |
|------|--------|------|
| 13a | 定义字段（vectorstore/documents/k…）与私有属性（_bm25/_df） | 277-284 |
| 13b | 建 BM25 索引 + 统计文档频率 df | 286-295 |
| 13c | 算 IDF 权重（越冷门越重要） | 297-302 |
| 13d | 算片段覆盖度（标题/文件名满分，正文 0.65） | 304-328 |
| 13e | 两路召回（向量 top-6、BM25 top-6）→ RRF 融合 → 排序取 top-3 | 330-375 |
| 13f | 对外接口（`retrieve_with_scores` / `_get_relevant_documents`） | 377-382 |

- **关键代码（RRF 融合）**：

```python
def add(docs, kind):
    for rank, doc in enumerate(docs, start=1):
        item = slot(doc)
        item["rrf"] += 1.0 / (RRF_K + rank)      # 两路都命中 → 分数叠加
        if not item[f"{kind}_rank"]:
            item[f"{kind}_rank"] = rank
```

- **关键代码（覆盖度）**：

```python
def _coverage(self, terms, doc):
    body_tokens = set(tokenize_for_bm25(doc.page_content))
    heading_tokens = {...标题行 + 文件名...}
    for term in terms:
        weight = self._term_weight(term)         # IDF，库里没有的词=0
        if weight <= 0: continue
        total += weight
        hit += weight if term in heading_tokens else weight * BODY_MATCH_CREDIT
    return hit / total
```

- **配置**：`RETRIEVAL_VECTOR_K` / `RETRIEVAL_BM25_K` / `RETRIEVAL_K` / `RRF_K` / `BODY_MATCH_CREDIT`（`rag_core.py:65-70`）；`USE_HYBRID_RETRIEVAL=False` 可退回纯向量
- **验证**：`python examples/debug_retrieval.py "什么是列表推导式？"` → 第一条应为 `Python入门指南.md`、覆盖度 1.00、标「高」

### 第 14 步：相关度分数与标签

- **工具**：标准库（纯计算）
- **位置**：`source_relevance()` `rag_core.py:385-390`；`relevance_label()` `rag_core.py:393-399`
- **关键代码**：

```python
def source_relevance(info):
    coverage = float(info.get("coverage", 0.0) or 0.0)
    vector_rank = int(info.get("vector_rank", 0) or 0)
    return round(min(0.85 * coverage + 0.15 * (1.0 / vector_rank if vector_rank else 0.0), 1.0), 3)

def relevance_label(score):
    return "高" if score >= 0.5 else ("中" if score >= 0.3 else "低")
```

- **配置**：想改高/低门槛，改 `relevance_label()` 里的 0.5 / 0.3；想改权重，改 `source_relevance()` 里的 0.85 / 0.15
- **验证**：上面的 debug 命令会直接打印每条来源的分数与标签

### 第 15 步：提示词模板与两种回答模式

- **工具**：`langchain-core` 的 `ChatPromptTemplate`
- **位置**：
  - 模板字典：`rag_core.py:91-113`（`PROMPT_TEMPLATES`）
  - 模式规范化：`rag_core.py:85-87` `resolve_answer_mode()`
  - 切换方法：`rag_core.py:533-543` `set_answer_mode()`
- **关键代码**：

```python
PROMPT_TEMPLATES = {
    "smart":   """...优先依据知识库内容回答...知识库无关就用你自己的知识回答，并在开头注明"【通用知识】"...""",
    "kb_only": """根据以下上下文回答问题。如果上下文没有相关信息，请说"未找到相关答案"。...""",
}
```

- **配置**：`DEFAULT_ANSWER_MODE`（`rag_core.py:79`）改默认模式；模板里的 `{context}` `{question}` 是占位符，**不要改名**
- **验证**：界面左侧「回答方式」切换后各问一个问题，智能模式答不出时会带【通用知识】提示条

### 第 16 步：用 LCEL 把链路串起来

- **工具**：`langchain-core` 的 `RunnablePassthrough`
- **位置**：`rag_core.py:645-660` `build_rag_chain()`
- **关键代码**：

```python
prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATES[self.answer_mode])
self._rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | self.llm
)
```

- **配置**：`self.answer_mode` 决定用哪个模板；`self.llm` 决定用哪个模型
- **验证**：日志 `✅ RAG 问答链构建完成 (LCEL)`

### 第 17 步：RAGSystem 生命周期（对外唯一入口）

- **工具**：无（纯 Python 类设计）
- **位置**：`rag_core.py:484-750`，关键成员：

| 方法 | 行号 | 作用 |
|------|------|------|
| `__init__` | 484-502 | 只记配置，不加载任何模型 |
| `model_spec` / `llm` / `embeddings` | 504-516 / 544-550 | 懒加载属性 |
| `set_model()` | 518-531 | 换对话模型（不重建索引） |
| `set_answer_mode()` | 533-543 | 换回答模式（不重建索引） |
| `load_documents` / `split_documents` / `build_vectorstore` | 552-616 | 入库三件套 |
| `load_vectorstore` / `_load_all_documents` | 618-643 | 复用索引 + 取回全部块供 BM25 用 |
| `build_rag_chain` | 645-660 | 建链 |
| `initialize(force_rebuild)` | 662-702 | 总装：复用或重建 + 建检索器 + 建链 |
| `query()` | 704-750 | 提问：调用链 → 算来源相关度 → 判断是否用了知识库 |

- **配置**：`initialize(force_rebuild=True)` 会强制重建；界面上的「🔄 重建知识库」走的就是这条
- **验证**：`python -c "from rag_core import RAGSystem; r=RAGSystem(); print(r.initialize())"`（复用已有索引，秒级）

### 第 18 步：命令行入口（可选但建议保留）

- **工具**：内置 `input()`
- **位置**：`rag_core.py:876-907`（`if __name__ == "__main__":`），示例文档生成在 `753-873` `create_sample_knowledge()`
- **配置**：运行前设 `PYTHONIOENCODING=utf-8`，否则 Windows 控制台可能报 GBK 编码错
- **验证**：`python rag_core.py` → 选模型 → 连续提问 → 输入 `quit` 退出

### 第 19 步：搭 Web 界面骨架

- **工具**：Streamlit 1.63.0
- **位置**：`app.py:6-27`（导入）、`30-35`（页面配置）、`38-50`（CSS）、`53-62`（两个缓存函数）、`299-416`（`main()` 布局）
- **关键代码**：

```python
@st.cache_resource
def get_rag_system() -> RAGSystem:
    return RAGSystem()                       # 全局单例，模型只加载一次

@st.cache_data(ttl=10, show_spinner=False)
def ollama_model_ready(model_name: str) -> bool:
    return is_ollama_model_ready(model_name)
```

- **配置**：页面标题/图标/布局在 `app.py:30-35`；启动命令 `streamlit run app.py`（默认 http://localhost:8501）
- **验证**：浏览器能打开页面、侧边栏五个区块都在

### 第 20 步：界面接上模型与回答方式

- **工具**：Streamlit 的 `selectbox` / `radio` / `text_input` / `button` / `progress`
- **位置**：
  - 模型选择：`app.py:65-128` `render_model_selector()`（含 DeepSeek Key 输入 79-87、切换生效 89-104、一键下载 106-128）
  - 回答方式：`app.py:131-161` `render_answer_mode()`
- **配置**：新增模型后下拉框会自动多出一项（读的是 `MODEL_REGISTRY`）
- **验证**：切换模型后立刻提问，回答正常且没有重建索引的耗时

### 第 21 步：知识库状态、上传与重建

- **工具**：Streamlit 的 `file_uploader` / `expander` / `spinner`
- **位置**：
  - 格式白名单与文件列表：`app.py:164-176`
  - 状态显示：`app.py:178-189`
  - 保存上传文件：`app.py:192-203` `save_uploaded_files()`
  - 操作区（上传 + 重建 + 示例）：`app.py:206-245` `render_operations()`
- **配置**：想支持更多格式，改 `app.py:164` 的白名单（同时要在 `rag_core.load_documents()` 里加对应加载器）
- **验证**：上传一个 `.md` → 点「📥 保存到知识库」→ 点「🔄 重建知识库」→ 提问新内容能答上来

### 第 22 步：参考来源的展示逻辑

- **工具**：Streamlit 的 `expander` / `caption` / `warning`
- **位置**：`app.py:267-272` `source_file_name()`、`app.py:274-297` `render_sources()`
- **关键逻辑**：

```python
relevant = [s for s in sources if s.get("relevance") in ("高", "中")]   # 只展示高/中
weak     = [s for s in sources if s.get("relevance") not in ("高", "中")]  # 低相关折叠
if not result.get("used_knowledge_base", True):
    st.warning("本次回答来自模型自身知识，**未使用知识库内容**。")
```

- **配置**：想连"低"相关也默认展开，改这里的展开参数
- **验证**：问知识库内问题 → 来源标「高」且随问题变化；问「明天天气」→ 出现"未使用知识库内容"提示

### 第 23 步：加学习/调试辅助与文档

- **工具**：无（纯脚本 + Markdown）
- **位置**：

| 文件 | 作用 | 怎么用 |
|------|------|--------|
| `examples/check_env.py` | 环境自检（版本/模型/文档/向量库） | `python examples/check_env.py` |
| `examples/minimal_rag.py` | 80 行最小 RAG，看清骨架与纯向量的短板 | `python examples/minimal_rag.py` |
| `examples/debug_retrieval.py` | 检索调试：不调模型看命中块与分数 | `python examples/debug_retrieval.py "问题"` |
| `README.md` | 使用说明与排错 | 遇到问题先看它 |
| `RAG实现学习手册.md` | 原理 + 复现 + 口述稿 | 学习/答辩前看 |
| `RAG项目完整文档.md` | 数据流 + 行号索引 | 快速定位代码 |

- **验证**：三个脚本都能直接跑通

---
# 第四部分　速查表（工具 → 位置 → 作用）

> 用法：忘了某段逻辑写在哪，先在下面两张表里搜关键词，拿到行号后直接跳到对应文件的那一行。

## 4.1 `rag_core.py` 符号索引（907 行）

### 配置区（改配置只看这一段）

| 行号 | 符号 | 作用 | 常用取值 |
|------|------|------|----------|
| 45 | `KNOWLEDGE_BASE_DIR` | 知识库文档目录 | `knowledge_base/` |
| 46 | `CHROMA_PERSIST_DIR` | 向量库落盘目录 | `data/chroma_db/` |
| 48 | `EMBEDDING_MODEL` | 向量化模型名 | `nomic-embed-text`（**换它必须重建**） |
| 49 | `CHROMA_COLLECTION_NAME` | 集合名 | `langchain` |
| 50 | `OLLAMA_HOST` | 本地 Ollama 地址 | 默认 `http://127.0.0.1:11434` |
| 53-54 | `DEFAULT_MODEL` / `LLM_MODEL` | 默认对话模型 | `qwen2.5:3b` |
| 57-59 | `DEEPSEEK_API_KEY` / `BASE_URL` / `MODEL` | 外接 DeepSeek 配置 | Key 建议只放 `.env` |
| 61-62 | `CHUNK_SIZE` / `CHUNK_OVERLAP` | 切块大小与重叠 | `800` / `100`（**改了要重建**） |
| 65 | `RETRIEVAL_K` | 最终交给模型的块数 | `3` |
| 66-67 | `RETRIEVAL_VECTOR_K` / `RETRIEVAL_BM25_K` | 两路各自召回数 | `6` / `6` |
| 68 | `RRF_K` | RRF 融合平滑参数 | `60`（越大越平缓） |
| 69 | `USE_HYBRID_RETRIEVAL` | 是否开混合检索 | `True`（关掉退化成纯向量） |
| 70 | `BODY_MATCH_CREDIT` | 命中正文（非标题）时的折扣 | `0.65` |
| 73-75 | `ANSWER_MODE_*` / `LABELS` | 两种回答模式及中文名 | `smart` / `kb_only` |
| 79 | `DEFAULT_ANSWER_MODE` | 默认回答模式 | `smart` |
| 81-82 | `GENERAL_KNOWLEDGE_TAG` / `NOT_FOUND_ANSWER` | 标记语与兜底话术 | `【通用知识】` / `未找到相关答案` |

### 逻辑区（改功能看这里）

| 行号 | 符号 | 作用 |
|------|------|------|
| 85 | `resolve_answer_mode()` | 归一化回答模式参数 |
| 91-113 | `PROMPT_TEMPLATES` | 两套提示词模板（智能问答 / 严格知识库） |
| 116-124 | `ModelSpec` | 模型描述结构体（key/label/provider/model/description） |
| 127-149 | `MODEL_REGISTRY` | **模型注册表**：3B、7B、DeepSeek 三条记录 |
| 152-154 | `available_models()` | 返回全部可选模型（界面下拉框用它） |
| 157-168 | `resolve_model()` | 模型标识 → `ModelSpec`；未登记的本地模型名自动当 Ollama 模型 |
| 171-178 | `list_ollama_models()` | 读本机已装模型（`/api/tags`） |
| 181-184 | `is_ollama_model_ready()` | 判断某模型是否已下载 |
| 187-217 | `pull_ollama_model()` | 流式下载模型并回报进度（界面"一键下载"用它） |
| 220-234 | `_reset_chroma_collection()` | **重建前清空旧集合**（防重复堆积） |
| 238-243 | `QUESTION_STOPWORDS` | 疑问词停用表（"什么/如何/怎么"等） |
| 245 | `HEADING_PATTERN` | 识别 Markdown 标题行的正则 |
| 248-256 | `tokenize_for_bm25()` | **不装分词库的中文切词**（汉字二元 + 英文单词） |
| 259-266 | `extract_query_terms()` | 从问题里抽关键词（去停用词、去单字） |
| 269 | `class HybridRetriever` | **混合检索器**（整个系统的心脏） |
| 286-295 | `_ensure_bm25()` | 惰性建 BM25 索引，同时算文档频率 df |
| 297-302 | `_term_weight()` | 单关键词 IDF 权重 |
| 304-328 | `_coverage()` | 问题关键词在某个块里的加权覆盖率（0~1） |
| 330-375 | `_rank_documents()` | **双路检索 + RRF 融合 + 覆盖度重排** |
| 377-382 | `retrieve_with_scores()` / `_get_relevant_documents()` | 对外接口（带分数 / 标准接口） |
| 385-390 | `source_relevance()` | 来源相关度 = 0.85×覆盖度 + 0.15×向量排名 |
| 393-399 | `relevance_label()` | 分数 → 高 / 中 / 低 |
| 402-450 | `class DeepSeekChat` | 用 HTTP 直接调 DeepSeek（不依赖 openai 包） |
| 453-478 | `create_llm()` | **按 provider 造对话模型**：ollama → `ChatOllama`，deepseek → `DeepSeekChat` |
| 481 | `class RAGSystem` | 对外唯一入口 |
| 484-502 | `__init__()` | 初始化模型、模式、缓存占位 |
| 505-507 | `model_spec` 属性 | 当前模型描述 |
| 510-515 | `llm` 属性 | 当前会话型模型实例（带缓存） |
| 518-530 | `set_model()` | 切模型（切到 DeepSeek 时校验 Key） |
| 533-542 | `set_answer_mode()` | 切回答模式 |
| 545-549 | `embeddings` 属性 | 向量化模型实例（带缓存） |
| 552-587 | `load_documents()` | **加载** md / txt / pdf |
| 589-601 | `split_documents()` | **切分**（`RecursiveCharacterTextSplitter`） |
| 603-616 | `build_vectorstore()` | **入库**：先清空再写入（修复重复的关键） |
| 618-630 | `load_vectorstore()` | 读取已有向量库 |
| 632-643 | `_load_all_documents()` | 从库里把 96 个块全取回来（给 BM25 用） |
| 645-660 | `build_rag_chain()` | **LCEL 串链路**：检索 → 取正文 → 填模板 → 调模型 → 解析 |
| 662-702 | `initialize()` | 生命周期：加载/切分/建库/建检索器/建链 |
| 704-750 | `query()` | **一次完整问答**，返回 answer / sources / model / used_knowledge_base |
| 753-873 | `create_sample_knowledge()` + 示例函数 | 首次运行自动生成的示例文档 |
| 876-907 | `if __name__ == "__main__"` | 命令行版入口（选模型 → 循环提问） |

## 4.2 `app.py` 函数索引（421 行）

| 行号 | 函数 / 常量 | 作用 | 对应界面元素 |
|------|-------------|------|--------------|
| 54 | `get_rag_system()` | 创建并缓存 `RAGSystem` 实例 | 全局（`@st.cache_resource`） |
| 60 | `ollama_model_ready()` | 判断本地模型是否就绪 | 模型下拉框旁的状态 |
| 65-128 | `render_model_selector()` | **模型选择区**（3B / 7B / DeepSeek，含一键下载、Key 输入） | 左侧边栏 |
| 131-161 | `render_answer_mode()` | **回答方式选择**（智能问答 / 严格知识库） | 左侧边栏 |
| 164 | `KNOWLEDGE_FILE_SUFFIXES` | 允许上传的格式 | `.md` `.txt` `.pdf` |
| 167-175 | `knowledge_base_files()` | 列出知识库文件 | 状态区 |
| 178-189 | `render_knowledge_base_status()` | 显示文档数 / 块数 | 左侧边栏 |
| 192-203 | `save_uploaded_files()` | 上传文件写入知识库目录 | 「📥 保存到知识库」 |
| 206-245 | `render_operations()` | **操作区**：上传、重建、示例问题 | 左侧边栏 |
| 247-264 | `render_system_info()` | 显示当前模型 / 检索配置 | 左侧边栏底部 |
| 267-272 | `source_file_name()` | 从来源元数据取干净文件名 | 参考来源区 |
| 274-297 | `render_sources()` | **参考来源展示**（只展开高/中相关，低相关折叠） | 回答下方 |
| 299-416 | `main()` | 页面骨架与提问流程 | 整页 |

## 4.3 配置文件与数据文件

| 路径 | 是什么 | 要不要进版本库 |
|------|--------|----------------|
| `.env` | 真实密钥（**你自己创建**，当前项目里还没有） | 不要 |
| `.env.example` | 密钥模板 | 要 |
| `requirements.txt` | 13 个依赖及版本 | 要 |
| `knowledge_base/*.md` | 知识库源文档（19 份） | 要 |
| `data/chroma_db/` | 向量库落盘（约 5.7 MB，41 个文件） | 可不要，能重建 |
| `.venv/` | 虚拟环境 | 不要 |
| `启动.bat` | 双击启动脚本 | 要 |

## 4.4 数据流：从提问到回答

```
用户提问（app.py 输入框）
  │
  ▼
RAGSystem.query(question)                          rag_core.py:704
  │
  ├─① 混合检索  HybridRetriever._rank_documents()  rag_core.py:330
  │    ├─ 向量路：Chroma + nomic-embed-text        :618 / :545
  │    │     └─ 召回 RETRIEVAL_VECTOR_K = 6 块
  │    ├─ 关键词路：BM25（自建中文分词）            :248 / :286
  │    │     └─ 召回 RETRIEVAL_BM25_K = 6 块
  │    └─ RRF 融合 + IDF 覆盖度重排 → 取前 3 块     :367-375
  │
  ├─② 填提示词  PROMPT_TEMPLATES[回答模式]          rag_core.py:91
  │    {context} = 前 3 块正文   {question} = 用户问题
  │
  ├─③ 调模型  create_llm()                          rag_core.py:453
  │    ├─ provider = ollama   → ChatOllama（本地 3B / 7B）
  │    └─ provider = deepseek → DeepSeekChat（HTTP 外接）  :402
  │
  └─④ 返回 { answer, sources, model, used_knowledge_base }
       │
       ▼
   app.py render_sources()  只把「高 / 中」相关的来源展开          app.py:274
```

**一句话记忆**：切块入库是"备菜"，混合检索是"挑菜"，提示词模板是"菜谱"，模型是"厨师"，相关度标签是"验菜"。

---

# 第五部分　从零复现（照着敲一遍）

> 全程在项目根目录 `C:\Users\Azathoth\RAG-project` 下操作。命令给的是 **PowerShell** 版本；CMD 的差异在括号里注明。

## 5.1 完整命令序列

### 第 0 步：确认 Python 版本

```powershell
.venv\Scripts\python.exe -V     # 本机输出 Python 3.14.7
```

> ⚠️ 别用 PATH 里的 `python --version` —— 本机它是 **3.10.10**，与 `.venv` 无关。

### 第 1 步：建虚拟环境

```powershell
cd C:\Users\Azathoth\RAG-project
uv venv --python 3.14 .venv     # 已建好，无需重做；不要用 python -m venv（会建成 3.10）
```

### 第 2 步：激活虚拟环境

```powershell
.\.venv\Scripts\Activate.ps1
```

- CMD 用户改用：`.venv\Scripts\activate.bat`
- 若报"禁止运行脚本"，先执行一次：`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
- 激活成功的标志：命令行前面出现 `(.venv)`
- ⚠️ 本机执行策略是 `Restricted`，若报「禁止运行脚本」，改用 `.\.venv\Scripts\Activate.ps1 -ExecutionPolicy Bypass`（本次绕过）；或干脆不激活，所有命令都用 `.venv\Scripts\python.exe` 开头
- ⚠️ **激活成功后 `pip` 仍然指向全局 3.10**（venv 里没有 `pip.exe`），装依赖必须写成 `python -m pip`

### 第 3 步：安装依赖

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

装的是 13 个包：`streamlit`、`langchain`、`langchain-core`、`langchain-community`、`langchain-ollama`、`langchain-text-splitters`、`chromadb`、`rank-bm25`、`pypdf`、`python-dotenv`、`numpy`、`requests`、`ollama`。

### 第 4 步：安装 Ollama 并拉取模型

```powershell
ollama pull qwen2.5:3b          # 约 1.9 GB
ollama pull qwen2.5:7b          # 约 4.7 GB（想用 7B 才需要）
ollama pull nomic-embed-text    # 约 274 MB，向量化模型，必须有
ollama list                     # 确认三个模型都在
```

> Ollama 服务需保持运行（桌面版常驻托盘；命令行版 `ollama serve`）。

### 第 5 步：配置外接 DeepSeek（不用就跳过）

```powershell
Copy-Item .env.example .env
notepad .env
```

`.env` 里填：

```
DEEPSEEK_API_KEY=sk-你的真实密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

> 界面上也能直接输入 Key（侧边栏「外接 DeepSeek」），两种方式都行。

### 第 6 步：放知识库文档

把 `.md` / `.txt` / `.pdf` 拷进 `knowledge_base\`，或启动界面后用「📄 上传知识库文档」。

### 第 7 步：环境自检

```powershell
python examples\check_env.py
```

会依次检查：Python 版本 → 13 个依赖 → Ollama 服务与 2 个模型 → 知识库 19 份文档 → 向量库 96 个块。全 ✅ 就可以往下走。

### 第 8 步：启动界面

```powershell
streamlit run app.py
```

浏览器自动打开 `http://localhost:8501`。首次使用点一次 **「🔄 重建知识库」**（约 1-2 分钟，把文档切块并向量化）。

> 也可以直接双击项目里的 `启动.bat`，效果相同。

### 第 9 步：命令行版（不开浏览器）

```powershell
python rag_core.py
```

会先列模型让你选（1/2/3），然后进入循环提问，输入 `quit` 退出。

### 第 10 步：只测检索、不调模型（排查用）

```powershell
python examples\debug_retrieval.py "什么是 RAG"
```

直接打印命中的块、BM25 分、向量排名与相关度标签——回答不对时先跑它，能立刻分清是"没检索到"还是"模型没答好"。

## 5.2 用到的所有命令一览

> 下表命令假定虚拟环境**已激活**；若采用第 1 步的「方式 A」（不激活），把命令里的 `python` / `streamlit` 换成 `.venv\Scripts\python.exe` / `.venv\Scripts\streamlit.exe` 即可。
> **带 ⚠️ 的三行是本机会踩坑的地方，务必按新写法来。**

| 命令 | 作用 | 用在哪一步 |
|------|------|-----------|
| `.venv\Scripts\python.exe -V` | 查 venv 里的 Python 版本（PATH 里那个是 3.10，别用） | 0 |
| ⚠️ `uv venv --python 3.14 .venv` | 建虚拟环境（**不要**用 `python -m venv`） | 1 |
| `.\.venv\Scripts\Activate.ps1 -ExecutionPolicy Bypass` | 激活（PowerShell，绕过执行策略） | 2 |
| `.venv\Scripts\activate.bat` | 激活（CMD） | 2 |
| `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` | 一次性放行激活脚本 | 2（只做一次） |
| ⚠️ `python -m pip install -r requirements.txt` | 装 13 个依赖（**别写裸 `pip install`**） | 3 |
| `ollama pull <模型>` | 下载对话/向量模型 | 4 |
| `ollama list` | 看本机已装模型 | 4 |
| `ollama serve` | 手动启动 Ollama 服务 | 4（桌面版不需要） |
| `Copy-Item .env.example .env` | 复制密钥模板 | 5 |
| ⚠️ `.venv\Scripts\python.exe examples\check_env.py` | 环境自检（用全局 python 跑会全 ❌） | 7 |
| `streamlit run app.py` | 启动网页界面 | 8 |
| `python rag_core.py` | 命令行问答 | 9 |
| `python examples\debug_retrieval.py "问题"` | 只看检索结果 | 10 |
| `python examples\minimal_rag.py` | 跑 80 行最小 RAG | 学习用 |
| `Ctrl + C` | 停止服务 | 随时 |

## 5.3 复现检查清单

- [ ] `.venv\Scripts\python.exe -V` 输出 `Python 3.14.7`
- [ ] `(.venv)` 前缀出现（用「方式 A」不激活的话，这条跳过）
- [ ] `.venv\Scripts\python.exe -m pip list` 里能看到 `langchain`、`chromadb`、`streamlit`
- [ ] `ollama list` 里有 `qwen2.5:3b` 和 `nomic-embed-text`
- [ ] `knowledge_base\` 里有文档
- [ ] `.venv\Scripts\python.exe examples\check_env.py` 全 ✅
- [ ] 界面能打开，点「重建知识库」显示成功、块数不为 0
- [ ] 问知识库内的问题 → 有答案 + 来源标「高」
- [ ] 问知识库外的问题（如"明天天气"）→ 出现"未使用知识库内容"或【通用知识】
- [ ] 切换模型（3B → DeepSeek）后回答正常

## 5.4 常见报错对照

| 现象 | 原因 | 处理 |
|------|------|------|
| `Chroma() got multiple values for keyword argument 'embedding_function'` | 入库时 `from_documents` 传了 `embedding_function=` | 已修复：`from_documents` 用 `embedding=`，构造函数用 `embedding_function=`（`rag_core.py:603-616`） |
| 任何问题都显示"未找到相关答案" | 回答模式停在「严格知识库」，或知识库没内容 | 切到「智能问答」；检查块数是否为 0 |
| 参考来源和回答无关、且不随问题变化 | 旧算法用"BM25 分 ÷ 本次最高分"，任何问题都有满分来源 | 已修复：改为 IDF 加权覆盖度排序 + 只展示高/中相关（`rag_core.py:304-390`） |
| 重建后检索到重复内容 | 旧数据没清空就追加 | 已修复：`_reset_chroma_collection()` 先清空（`rag_core.py:220-234`） |
| 连不上本地模型 | Ollama 没启动 | 启动 Ollama；`ollama list` 验证 |
| DeepSeek 报鉴权失败 | Key 没填或填错 | 检查 `.env` 或界面输入框；确认余额 |
| 换了向量模型后结果异常 | 新旧向量维度不一致 | 改 `EMBEDDING_MODEL` 后必须重建知识库 |
| 界面改完不生效 | Streamlit 有缓存 | 按 `R` 刷新页面，或重启服务（`Ctrl + C` 后重跑） |

---

# 附：几份文档怎么配合用

| 文档 | 什么时候看 |
|------|-----------|
| `RAG实现步骤与配置清单.md`（本文） | 想知道"用了什么工具、代码在哪、怎么配" |
| `RAG实现学习手册.md` | 想从原理上理解、要口述/答辩 |
| `README.md` | 日常使用、遇到问题先翻它 |
| `RAG项目完整文档.md` | 想顺着数据流读代码 |
