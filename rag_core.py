"""
RAG 知识库问答系统 - 核心模块 (LangChain 1.x 版本)
基于：LangChain + Ollama + ChromaDB

对话模型可选：
- 本地 Ollama：qwen2.5:3b / qwen2.5:7b
- 外接 API：DeepSeek (deepseek-chat)
"""

import json
import math
import os
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# LangChain 组件 (1.x API)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader, DirectoryLoader
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import Runnable, RunnablePassthrough
from pydantic import PrivateAttr

try:  # BM25 关键词检索（未安装时自动退化为纯向量检索）
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None

try:  # 可选：从项目根目录的 .env 读取配置（如 DEEPSEEK_API_KEY）
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

# 配置常量
KNOWLEDGE_BASE_DIR = Path(__file__).parent / "knowledge_base"
CHROMA_PERSIST_DIR = Path(__file__).parent / "data" / "chroma_db"

EMBEDDING_MODEL = "nomic-embed-text"
CHROMA_COLLECTION_NAME = "langchain"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

# 默认对话模型（可在界面或代码中切换）
DEFAULT_MODEL = "qwen2.5:3b"
LLM_MODEL = DEFAULT_MODEL  # 兼容旧配置名

# DeepSeek API 配置（外接模型）
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = "deepseek-chat"  # 性价比最高

CHUNK_SIZE = 800        # 文本块大小（过小会把标题和正文拆散，影响检索）
CHUNK_OVERLAP = 100     # 相邻块重叠字符数

# 检索参数
RETRIEVAL_K = 3          # 最终交给模型的文本块数量
RETRIEVAL_VECTOR_K = 6   # 向量检索候选数
RETRIEVAL_BM25_K = 6     # 关键词检索候选数
RRF_K = 60               # RRF 融合参数
USE_HYBRID_RETRIEVAL = True  # 向量 + BM25 关键词混合检索
BODY_MATCH_CREDIT = 0.65  # 问题关键词出现在正文（而非标题）时的相关度折扣

# 回答模式
ANSWER_MODE_SMART = "smart"      # 智能问答：知识库优先，知识库没有的内容用模型自身知识回答
ANSWER_MODE_KB_ONLY = "kb_only"  # 严格知识库：只依据知识库回答，没有就答"未找到相关答案"
ANSWER_MODE_LABELS = {
    ANSWER_MODE_SMART: "智能问答（知识库优先，其他问题也能答）",
    ANSWER_MODE_KB_ONLY: "严格知识库（只根据知识库回答）",
}
DEFAULT_ANSWER_MODE = ANSWER_MODE_SMART

GENERAL_KNOWLEDGE_TAG = "【通用知识】"  # 智能问答模式下，模型自身知识的回答会带这个前缀
NOT_FOUND_ANSWER = "未找到相关答案"      # 严格知识库模式下，知识库没有相关内容时的回答


def resolve_answer_mode(mode: Optional[str]) -> str:
    """把回答模式标识规范化为合法值"""
    return mode if mode in ANSWER_MODE_LABELS else DEFAULT_ANSWER_MODE


# 两种模式的提示词模板
PROMPT_TEMPLATES: Dict[str, str] = {
    ANSWER_MODE_SMART: """你是知识库问答助手，请优先依据下面的"知识库内容"回答用户问题。

规则：
1. 如果知识库内容与问题相关，请依据它回答，不要编造知识库中没有的信息；
2. 如果知识库内容与问题无关或不足以回答，请直接用你自己的知识回答，并在回答开头注明"【通用知识】"；
3. 始终用中文回答，简洁准确。

知识库内容：
{context}

问题：{question}

回答：""",
    ANSWER_MODE_KB_ONLY: """根据以下上下文回答问题。如果上下文没有相关信息，请说"未找到相关答案"。

上下文：
{context}

问题：{question}

回答：""",
}


@dataclass(frozen=True)
class ModelSpec:
    """可选的对话模型"""

    key: str          # 唯一标识，界面与代码中使用
    label: str        # 显示名称
    provider: str     # "ollama"（本地）或 "deepseek"（外接 API）
    model: str        # 实际传给推理后端的模型名
    description: str  # 说明文字


MODEL_REGISTRY: Dict[str, ModelSpec] = {
    "qwen2.5:3b": ModelSpec(
        key="qwen2.5:3b",
        label="Qwen2.5-3B（本地 Ollama）",
        provider="ollama",
        model="qwen2.5:3b",
        description="轻量快速，占用约 2GB，适合日常问答",
    ),
    "qwen2.5:7b": ModelSpec(
        key="qwen2.5:7b",
        label="Qwen2.5-7B（本地 Ollama）",
        provider="ollama",
        model="qwen2.5:7b",
        description="回答质量更高，约 4.7GB，首次使用需下载",
    ),
    "deepseek-chat": ModelSpec(
        key="deepseek-chat",
        label="DeepSeek-V3（外接 API）",
        provider="deepseek",
        model="deepseek-chat",
        description="云端 API，能力最强，需要 API Key 和网络",
    ),
}


def available_models() -> List[ModelSpec]:
    """返回所有可选的对话模型"""
    return list(MODEL_REGISTRY.values())


def resolve_model(model_key: Optional[str]) -> ModelSpec:
    """把模型标识解析为 ModelSpec；未登记的本地模型名按 Ollama 模型处理"""
    key = (model_key or DEFAULT_MODEL).strip()
    if key in MODEL_REGISTRY:
        return MODEL_REGISTRY[key]
    return ModelSpec(
        key=key,
        label=f"{key}（本地 Ollama）",
        provider="ollama",
        model=key,
        description="自定义本地 Ollama 模型",
    )


def list_ollama_models() -> List[str]:
    """列出本地 Ollama 已下载的模型；服务不可用时返回空列表"""
    try:
        with urllib.request.urlopen(f"{OLLAMA_HOST}/api/tags", timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
        return [item.get("name", "") for item in data.get("models", [])]
    except Exception:
        return []


def is_ollama_model_ready(model_name: str) -> bool:
    """判断本地 Ollama 是否已下载指定模型"""
    target = model_name if ":" in model_name else f"{model_name}:latest"
    return target in list_ollama_models()


def pull_ollama_model(
    model_name: str,
    on_progress: Optional[Callable[[str, float], None]] = None,
    timeout: int = 3600,
) -> bool:
    """下载本地 Ollama 模型；on_progress(状态描述, 进度 0~1) 用于展示下载进度"""
    request = urllib.request.Request(
        f"{OLLAMA_HOST}/api/pull",
        data=json.dumps({"model": model_name, "stream": True}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                event = json.loads(line)
                if event.get("error"):
                    raise RuntimeError(event["error"])
                total = event.get("total") or 0
                completed = event.get("completed") or 0
                percent = (completed / total) if total else 0.0
                if on_progress:
                    on_progress(event.get("status", "下载中"), percent)
        return True
    except Exception as exc:
        if on_progress:
            on_progress(f"下载失败: {exc}", 0.0)
        return False


def _reset_chroma_collection(collection_name: str = CHROMA_COLLECTION_NAME) -> None:
    """删除旧的向量集合，保证重建时不会与旧数据重复累积"""
    try:
        import chromadb

        client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
        names = [
            item.name if hasattr(item, "name") else str(item)
            for item in client.list_collections()
        ]
        if collection_name in names:
            client.delete_collection(collection_name)
            print("🧹 已清除旧的向量集合")
    except Exception as exc:
        print(f"⚠️ 清除旧向量集合失败（可忽略，将直接追加）: {exc}")


# 问题里的通用词（疑问词、客套话）不参与"片段相关度"计算，避免"架构""什么"这类词造成假相关
QUESTION_STOPWORDS = {
    "什么", "是什", "么是", "有什", "怎么", "么样", "怎样", "如何", "为什", "哪些",
    "哪个", "是否", "能否", "可以", "一下", "介绍", "讲解", "说明", "解释", "举例",
    "例子", "示例", "详细", "简单", "区别", "不同", "一样", "意思", "作用", "用法",
    "请问", "告诉", "知道", "了解", "哪些", "多少",
}

HEADING_PATTERN = re.compile(r"^#{1,6}\s")


def tokenize_for_bm25(text: str) -> List[str]:
    """中英混合分词：英文单词 + 中文二元切分（不需要额外分词库）"""
    tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    for run in re.findall(r"[\u4e00-\u9fff]+", text):
        if len(run) == 1:
            tokens.append(run)
        else:
            tokens.extend(run[i : i + 2] for i in range(len(run) - 1))
    return tokens


def extract_query_terms(text: str) -> List[str]:
    """提取问题里的实词（去重、去掉疑问词等通用词），用于计算片段相关度"""
    terms: List[str] = []
    for token in tokenize_for_bm25(text):
        if len(token) < 2 or token in QUESTION_STOPWORDS or token in terms:
            continue
        terms.append(token)
    return terms


class HybridRetriever(BaseRetriever):
    """混合检索器：向量相似度 + BM25 关键词，用 RRF（倒数排名融合）合并结果。

    纯向量检索对中文关键词（如"文件""异常"）不敏感，加入 BM25 可显著提升召回质量。
    片段与问题的相关度用"IDF 加权覆盖度"衡量：问题里的关键词在片段中越是完整出现、
    越是出现在标题或文件名里，相关度越高；这样"参考来源"才会随问题变化且真实相关。
    """

    vectorstore: Any
    documents: List[Document] = []
    k: int = RETRIEVAL_K
    vector_k: int = RETRIEVAL_VECTOR_K
    keyword_k: int = RETRIEVAL_BM25_K

    _bm25: Any = PrivateAttr(default=None)
    _df: Dict[str, int] = PrivateAttr(default_factory=dict)

    def _ensure_bm25(self):
        if self._bm25 is None and BM25Okapi is not None and self.documents:
            corpus = [tokenize_for_bm25(doc.page_content) for doc in self.documents]
            self._bm25 = BM25Okapi(corpus)
            df: Dict[str, int] = {}
            for tokens in corpus:
                for token in set(tokens):
                    df[token] = df.get(token, 0) + 1
            self._df = df
        return self._bm25

    def _term_weight(self, term: str) -> float:
        """IDF 权重：越少见的词越能说明"片段在讲这个主题"；知识库里没有的词直接忽略"""
        df = self._df.get(term, 0)
        if df <= 0 or not self.documents:
            return 0.0
        return max(math.log((len(self.documents) + 1) / (df + 1)), 1e-6)

    def _coverage(self, terms: List[str], doc: Document) -> float:
        """片段对问题的覆盖度（0~1）：标题/文件名命中的词权重最高，正文命中次之"""
        if not terms:
            return 0.0
        content = doc.page_content
        body_tokens = set(tokenize_for_bm25(content))
        heading_tokens = set()
        for line in content.splitlines():
            if HEADING_PATTERN.match(line):
                heading_tokens.update(tokenize_for_bm25(line))
        source = str(doc.metadata.get("source", ""))
        heading_tokens.update(tokenize_for_bm25(Path(source).stem))

        total = 0.0
        hit = 0.0
        for term in terms:
            weight = self._term_weight(term)
            if weight <= 0:
                continue
            total += weight
            if term in heading_tokens:
                hit += weight
            elif term in body_tokens:
                hit += weight * BODY_MATCH_CREDIT
        return hit / total if total else 0.0

    def _rank_documents(self, query: str) -> List[tuple]:
        """返回 [(文档, 检索信息)]，检索信息含覆盖度、RRF 分数、向量/关键词排名"""
        found: Dict[str, Document] = {}
        info: Dict[str, Dict[str, float]] = {}

        def slot(doc: Document) -> Dict[str, float]:
            key = doc.page_content
            found.setdefault(key, doc)
            return info.setdefault(
                key,
                {"rrf": 0.0, "coverage": 0.0, "vector_rank": 0.0, "keyword_rank": 0.0},
            )

        def add(docs: List[Document], kind: str) -> None:
            for rank, doc in enumerate(docs, start=1):
                item = slot(doc)
                item["rrf"] += 1.0 / (RRF_K + rank)
                if not item[f"{kind}_rank"]:
                    item[f"{kind}_rank"] = rank

        # 1) 向量检索
        try:
            vector_docs = [doc for doc, _ in self.vectorstore.similarity_search_with_score(query, k=self.vector_k)]
        except Exception:
            vector_docs = self.vectorstore.similarity_search(query, k=self.vector_k)
        add(vector_docs, "vector")

        # 2) 关键词检索（BM25）
        bm25 = self._ensure_bm25()
        if bm25 is not None:
            keyword_scores = bm25.get_scores(tokenize_for_bm25(query))
            order = sorted(range(len(keyword_scores)), key=lambda i: -keyword_scores[i])
            hits = [i for i in order[: self.keyword_k] if keyword_scores[i] > 0]
            add([self.documents[i] for i in hits], "keyword")

        # 3) 覆盖度：判断片段是否真的讲到了问题里的关键内容
        terms = extract_query_terms(query)
        for doc in found.values():
            info[doc.page_content]["coverage"] = self._coverage(terms, doc)

        # 先按覆盖度、再按融合排名排序，避免命中通用词的无关片段被顶到最前面
        ranked = sorted(
            info.items(),
            key=lambda item: (-round(item[1]["coverage"], 2), -item[1]["rrf"]),
        )
        return [(found[key], item) for key, item in ranked[: self.k]]

    def retrieve_with_scores(self, query: str) -> List[tuple]:
        """供界面展示参考来源使用：返回带相关度信息的检索结果"""
        return self._rank_documents(query)

    def _get_relevant_documents(self, query: str, *, run_manager=None) -> List[Document]:
        return [doc for doc, _ in self._rank_documents(query)]


def source_relevance(info: Dict[str, float]) -> float:
    """把检索信息换算成 0~1 的相关度分数（关键词覆盖度为主，向量排名为辅）"""
    coverage = float(info.get("coverage", info.get("keyword", 0.0)) or 0.0)
    vector_rank = int(info.get("vector_rank", 0) or 0)
    vector_part = 1.0 / vector_rank if vector_rank > 0 else 0.0
    return round(min(0.85 * coverage + 0.15 * vector_part, 1.0), 3)


def relevance_label(score: float) -> str:
    """相关度标签：高 / 中 / 低"""
    if score >= 0.5:
        return "高"
    if score >= 0.3:
        return "中"
    return "低"


class DeepSeekChat(Runnable):
    """DeepSeek 对话模型适配器（OpenAI 兼容接口）。

    优先使用 langchain-openai 的 ChatOpenAI；未安装该库时退化为本适配器，
    仅依赖已安装的 openai SDK，并可像普通 Runnable 一样接入 LCEL 链。
    """

    def __init__(
        self,
        model: str = DEEPSEEK_MODEL,
        api_key: Optional[str] = None,
        base_url: str = DEEPSEEK_BASE_URL,
        temperature: float = 0.1,
    ):
        from openai import OpenAI

        if not (api_key or DEEPSEEK_API_KEY):
            raise ValueError("使用 DeepSeek 需要提供 API Key（界面输入或设置 DEEPSEEK_API_KEY 环境变量）")

        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self._client = OpenAI(api_key=api_key or DEEPSEEK_API_KEY, base_url=base_url)

    def invoke(self, input, config=None, **kwargs) -> AIMessage:
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=self._to_chat_messages(input),
                temperature=self.temperature,
            )
        except Exception as exc:
            raise RuntimeError(f"DeepSeek API 调用失败：{exc}") from exc
        return AIMessage(content=response.choices[0].message.content or "")

    @staticmethod
    def _to_chat_messages(input) -> List[Dict[str, str]]:
        if isinstance(input, str):
            return [{"role": "user", "content": input}]
        if hasattr(input, "to_messages"):
            input = input.to_messages()
        role_map = {"human": "user", "ai": "assistant", "system": "system"}
        return [
            {
                "role": role_map.get(getattr(message, "type", "human"), "user"),
                "content": message.content,
            }
            for message in input
        ]


def create_llm(
    model_key: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.1,
    num_ctx: int = 4096,
):
    """按模型标识创建对话模型实例（本地 Ollama 或外接 DeepSeek API）"""
    spec = resolve_model(model_key)

    if spec.provider == "deepseek":
        key = api_key or DEEPSEEK_API_KEY
        if not key:
            raise ValueError("使用 DeepSeek 需要提供 API Key（界面输入或设置 DEEPSEEK_API_KEY 环境变量）")
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            print("ℹ️ 未安装 langchain-openai，使用内置 DeepSeek 适配器 (openai SDK)")
            return DeepSeekChat(model=spec.model, api_key=key, temperature=temperature)
        return ChatOpenAI(
            model=spec.model,
            api_key=key,
            base_url=DEEPSEEK_BASE_URL,
            temperature=temperature,
        )

    return ChatOllama(model=spec.model, temperature=temperature, num_ctx=num_ctx)


class RAGSystem:
    """RAG 知识库问答系统 (LangChain 1.x LCEL 版本)"""

    def __init__(
        self,
        knowledge_base_dir: str = None,
        model_key: str = None,
        embedding_model: str = EMBEDDING_MODEL,
        api_key: str = None,
        llm_model: str = None,  # 兼容旧参数名
        answer_mode: str = DEFAULT_ANSWER_MODE,
    ):
        self.knowledge_base_dir = Path(knowledge_base_dir) if knowledge_base_dir else KNOWLEDGE_BASE_DIR
        self.model_key = resolve_model(model_key or llm_model or DEFAULT_MODEL).key
        self.embedding_model = embedding_model
        self.answer_mode = resolve_answer_mode(answer_mode)
        self._api_key = api_key or DEEPSEEK_API_KEY

        self._llm = None
        self._embeddings = None
        self._retriever = None
        self._rag_chain = None

    @property
    def model_spec(self) -> ModelSpec:
        """当前对话模型的信息"""
        return resolve_model(self.model_key)

    @property
    def llm(self):
        if self._llm is None:
            spec = self.model_spec
            print(f"🤖 正在加载对话模型: {spec.label}")
            self._llm = create_llm(self.model_key, api_key=self._api_key)
            print("✅ 对话模型加载完成")
        return self._llm

    def set_model(self, model_key: str, api_key: str = None) -> ModelSpec:
        """切换对话模型（只替换模型，不需要重建向量库）"""
        spec = resolve_model(model_key)
        if api_key:
            self._api_key = api_key
        if spec.provider == "deepseek" and not self._api_key:
            raise ValueError("使用 DeepSeek 需要提供 API Key（界面输入或设置 DEEPSEEK_API_KEY 环境变量）")

        self.model_key = spec.key
        self._llm = None  # 下次访问 llm 时按新模型重建
        if self._retriever is not None:
            self.build_rag_chain(self._retriever)
        print(f"🔄 已切换对话模型: {spec.label}")
        return spec

    def set_answer_mode(self, mode: str) -> str:
        """切换回答模式（智能问答 / 严格知识库），切换后自动重建问答链"""
        mode = resolve_answer_mode(mode)
        if mode == self.answer_mode:
            return mode
        self.answer_mode = mode
        if self._retriever is not None:
            self.build_rag_chain(self._retriever)
        print(f"🔄 已切换回答模式: {ANSWER_MODE_LABELS[mode]}")
        return mode

    @property
    def embeddings(self):
        if self._embeddings is None:
            print(f"📊 正在加载向量模型: {self.embedding_model}")
            self._embeddings = OllamaEmbeddings(model=self.embedding_model)
            print("✅ 向量模型加载完成")
        return self._embeddings

    def load_documents(self) -> List[Document]:
        """从知识库目录加载所有文档"""
        documents = []

        if not self.knowledge_base_dir.exists():
            print(f"⚠️ 知识库目录不存在: {self.knowledge_base_dir}")
            return documents

        print(f"📂 正在从 {self.knowledge_base_dir} 加载文档...")

        for ext in ["*.txt", "*.md"]:
            loader = DirectoryLoader(
                str(self.knowledge_base_dir),
                glob=ext,
                loader_cls=TextLoader,
                loader_kwargs={"encoding": "utf-8"},
            )
            try:
                docs = loader.load()
                documents.extend(docs)
                print(f"  📄 加载 {len(docs)} 个 {ext} 文件")
            except Exception as e:
                print(f"  ⚠️ 加载 {ext} 文件出错: {e}")

        pdf_files = list(self.knowledge_base_dir.glob("*.pdf"))
        for pdf_path in pdf_files:
            try:
                loader = PyPDFLoader(str(pdf_path))
                docs = loader.load()
                documents.extend(docs)
                print(f"  📕 加载 PDF: {pdf_path.name} ({len(docs)} 页)")
            except Exception as e:
                print(f"  ⚠️ 加载 PDF 出错 {pdf_path.name}: {e}")

        print(f"✅ 共加载 {len(documents)} 个文档片段")
        return documents

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """将文档分割成小块"""
        print(f"✂️ 正在分割文档...")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "！", "？", ".", " ", ""],
        )

        chunks = text_splitter.split_documents(documents)
        print(f"✅ 分割完成，共 {len(chunks)} 个文本块")
        return chunks

    def build_vectorstore(self, chunks: List[Document]) -> Chroma:
        """构建向量数据库（重建前会清空旧集合，避免新旧数据重复累积）"""
        print("🔍 正在构建向量索引...")
        CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
        _reset_chroma_collection()

        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=str(CHROMA_PERSIST_DIR),
        )

        print(f"✅ 向量数据库构建完成")
        return vectorstore

    def load_vectorstore(self):
        """加载已有的向量数据库"""
        if CHROMA_PERSIST_DIR.exists() and any(CHROMA_PERSIST_DIR.iterdir()):
            print(f"📂 加载已有向量数据库...")
            vectorstore = Chroma(
                collection_name=CHROMA_COLLECTION_NAME,
                persist_directory=str(CHROMA_PERSIST_DIR),
                embedding_function=self.embeddings,
            )
            print("✅ 向量数据库加载完成")
            return vectorstore
        return None

    @staticmethod
    def _load_all_documents(vectorstore) -> List[Document]:
        """取出向量库中的全部文本块，供 BM25 建立关键词索引"""
        try:
            data = vectorstore.get(include=["documents", "metadatas"])
        except Exception:
            return []
        texts = data.get("documents") or []
        metadatas = data.get("metadatas") or [{}] * len(texts)
        return [
            Document(page_content=text, metadata=meta or {})
            for text, meta in zip(texts, metadatas)
        ]

    def build_rag_chain(self, retriever):
        """使用 LCEL 构建 RAG 链 (LangChain 1.x 新 API)"""
        print(f"🔗 构建 RAG 问答链 (LCEL)，回答模式: {ANSWER_MODE_LABELS[self.answer_mode]}...")

        # 按回答模式选择提示词模板
        prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATES[self.answer_mode])

        # LCEL 链式调用
        self._rag_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | self.llm
        )

        print("✅ RAG 问答链构建完成 (LCEL)")
        return self._rag_chain

    def initialize(self, force_rebuild: bool = False):
        """初始化 RAG 系统"""
        print("\n" + "=" * 50)
        print("🚀 初始化 RAG 知识库系统")
        print(f"🤖 对话模型: {self.model_spec.label}")
        print("=" * 50)

        # 尝试加载已有的向量数据库
        if not force_rebuild:
            vectorstore = self.load_vectorstore()

        # 如果没有或需要重建
        if force_rebuild or 'vectorstore' not in locals() or vectorstore is None:
            documents = self.load_documents()
            if not documents:
                print("❌ 没有找到任何文档！请在 knowledge_base 目录中放入文档。")
                return False

            chunks = self.split_documents(documents)
            vectorstore = self.build_vectorstore(chunks)

        # 创建检索器（向量 + BM25 混合）
        all_docs = self._load_all_documents(vectorstore)
        if USE_HYBRID_RETRIEVAL and BM25Okapi is not None and all_docs:
            self._retriever = HybridRetriever(
                vectorstore=vectorstore,
                documents=all_docs,
                k=RETRIEVAL_K,
            )
            print(f"🔍 已启用混合检索（向量 + BM25），共 {len(all_docs)} 个文本块")
        else:
            self._retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": RETRIEVAL_K},
            )

        # 构建 RAG 链
        self.build_rag_chain(self._retriever)

        print("\n🎉 RAG 系统初始化完成！可以开始提问了。\n")
        return True

    def query(self, question: str) -> Dict:
        """查询问题"""
        if not self._rag_chain:
            raise RuntimeError("RAG 系统未初始化，请先调用 initialize()")

        print(f"\n❓ 问题: {question}")

        # 使用 LCEL 链调用
        response = self._rag_chain.invoke(question)
        answer = response.content

        print(f"💬 回答: {answer[:100]}..." if len(answer) > 100 else f"💬 回答: {answer}")

        # 获取参考来源（带相关度信息）
        if hasattr(self._retriever, "retrieve_with_scores"):
            ranked = self._retriever.retrieve_with_scores(question)
        else:
            ranked = [(doc, {}) for doc in self._retriever.invoke(question)]

        sources = []
        for doc, info in ranked:
            score = source_relevance(info)
            sources.append(
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score,
                    "relevance": relevance_label(score),
                }
            )

        # 回答是否真的来自知识库
        answer_head = answer.lstrip()
        used_knowledge_base = not (
            answer_head.startswith(GENERAL_KNOWLEDGE_TAG)
            or answer_head.startswith(NOT_FOUND_ANSWER)
        )

        return {
            "question": question,
            "model": self.model_spec.label,
            "mode": self.answer_mode,
            "answer": answer,
            "used_knowledge_base": used_knowledge_base,
            "sources": sources,
            "source_count": len(sources),
        }


def create_sample_knowledge():
    """创建示例知识库文档"""
    kb_dir = KNOWLEDGE_BASE_DIR
    kb_dir.mkdir(parents=True, exist_ok=True)

    sample_file = kb_dir / "Python入门指南.md"
    if not sample_file.exists():
        sample_content = """# Python 入门指南

## 1. Python 简介
Python 是一种高级编程语言，由 Guido van Rossum 于 1991 年创建。
它以其简洁的语法和强大的功能而闻名，被广泛应用于 Web 开发、数据科学、人工智能等领域。

## 2. 基本语法

### 2.1 变量和数据类型
Python 支持多种数据类型：
- 整数 (int): 如 42, -17, 0
- 浮点数 (float): 如 3.14, -0.001, 2.0
- 字符串 (str): 如 "Hello", 'World'
- 布尔值 (bool): True, False
- 列表 (list): 如 [1, 2, 3], ['a', 'b', 'c']
- 字典 (dict): 如 {'name': 'Alice', 'age': 25}

### 2.2 控制流
Python 使用缩进来定义代码块：

```python
if x > 0:
    print("正数")
elif x < 0:
    print("负数")
else:
    print("零")

for i in range(5):
    print(i)
```

### 2.3 函数定义
使用 def 关键字定义函数：

```python
def greet(name, greeting="你好"):
    '''向用户问好'''
    return f"{greeting}，{name}！"

message = greet("世界")
print(message)
```

## 3. 常用内置函数

### 3.1 数据处理
- len(): 返回对象长度
- type(): 返回对象类型
- range(): 生成数字序列

### 3.2 类型转换
- int(): 转换为整数
- float(): 转换为浮点数
- str(): 转换为字符串

## 4. 文件操作

```python
with open('file.txt', 'r', encoding='utf-8') as f:
    content = f.read()

with open('output.txt', 'w', encoding='utf-8') as f:
    f.write('Hello, World!')
```

## 5. 异常处理

```python
try:
    result = 10 / 0
except ZeroDivisionError:
    print("不能除以零！")
except Exception as e:
    print(f"发生错误: {e}")
```

## 6. 列表推导式

```python
squares = [x**2 for x in range(10)]
even_squares = [x**2 for x in range(10) if x % 2 == 0]
```

## 7. 类和对象

```python
class Dog:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def bark(self):
        return f"{self.name} 说：汪汪！"

my_dog = Dog("旺财", 3)
print(my_dog.bark())
```

## 8. 最佳实践

1. **遵循 PEP 8** 编码规范
2. **编写文档字符串**
3. **使用有意义的变量名**
4. **保持函数简短专注**

---

*本文档最后更新: 2026年9月*
"""
        sample_file.write_text(sample_content, encoding="utf-8")
        print(f"✅ 已创建示例文档: {sample_file}")
        return True
    return False


if __name__ == "__main__":
    if not any(KNOWLEDGE_BASE_DIR.iterdir()):
        create_sample_knowledge()

    specs = available_models()
    print("\n可选对话模型：")
    for index, spec in enumerate(specs, 1):
        print(f"  {index}. {spec.label} — {spec.description}")
    choice = input(f"请选择对话模型 [1-{len(specs)}，回车使用默认 {DEFAULT_MODEL}]: ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(specs):
        model_key = specs[int(choice) - 1].key
    else:
        model_key = DEFAULT_MODEL

    rag = RAGSystem(model_key=model_key)
    if rag.initialize():
        print("\n" + "=" * 50)
        print(f"💬 进入问答模式（当前模型: {rag.model_spec.label}，输入 'quit' 退出）")
        print("=" * 50 + "\n")

        while True:
            question = input("❓ 请输入问题: ").strip()
            if question.lower() in ['quit', 'exit', 'q', '退出']:
                print("👋 再见！")
                break
            if not question:
                continue

            result = rag.query(question)
            print(f"\n{'─' * 40}")
            print(f"📖 回答（{result['model']}）:\n{result['answer']}")
            print(f"{'─' * 40}\n")