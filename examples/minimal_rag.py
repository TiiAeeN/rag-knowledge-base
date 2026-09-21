"""
最小可运行版 RAG（约 80 行，含注释）——用来理解 RAG 的骨架
运行： python examples/minimal_rag.py

它和正式版的关系：
  正式版 rag_core.py = 这套骨架 + 混合检索 + 多模型 + 相关度 + 界面
  读懂这 80 行，后面每一块都只是在这条链上做加法。
"""
import shutil
from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE = Path(__file__).resolve().parent.parent   # 项目根目录
KB_DIR = BASE / "knowledge_base"                # 知识库原始文档
DB_DIR = BASE / "data" / "chroma_minimal"       # 示例专用向量库目录（不碰正式库）

if DB_DIR.exists():
    shutil.rmtree(DB_DIR)                       # 每次重建，避免旧数据重复累积

# ① 加载：把 knowledge_base 里的 .md 读成 Document 列表（含正文与来源路径）
documents = DirectoryLoader(
    str(KB_DIR), glob="*.md", loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"},
).load()
print(f"① 加载文档 {len(documents)} 份")

# ② 切分：长文档切成 800 字左右的小块，相邻块重叠 100 字（防止答案被切断）
chunks = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    separators=["\n\n", "\n", "。", "！", "？", ".", " ", ""],
).split_documents(documents)
print(f"② 切分得到 {len(chunks)} 个文本块")

# ③ 向量化 + 存储：每个块用 nomic-embed-text 转成 768 维向量，存进 Chroma
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vectorstore = Chroma.from_documents(
    chunks, embedding=embeddings, persist_directory=str(DB_DIR)
)
print("③ 向量库构建完成")

# ④ 检索：把问题也转成向量，找出最相似的 3 个块
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# ⑤ 生成：把检索到的 3 个块拼进提示词，交给本地模型回答
prompt = ChatPromptTemplate.from_template(
    "根据下面的资料回答问题；资料里没有就说不知道。\n\n资料：\n{context}\n\n问题：{question}\n\n回答："
)
llm = ChatOllama(model="qwen2.5:3b", temperature=0.1)

chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

for question in ["Docker 的镜像和容器有什么区别？", "什么是列表推导式？"]:
    print(f"\n❓ {question}")
    print("💬", chain.invoke(question))

print(
    "\n"
    "────────────────────────────────────────────────────────\n"
    "观察：第一个问题答对了，第二个问题（知识库里明明有答案）却说不知道。\n"
    "原因：nomic-embed-text 对中文的区分度很弱，它经常把同一个文档的『开头块』\n"
    "      排在前面（因为开头块包含标题，和任何问题都有点像），真正讲\n"
    "      『列表推导式』的那一块反而没进前 3。\n"
    "正式版的解法：rag_core.py 在向量检索之外再加一路 BM25 关键词检索，\n"
    "      用 RRF 融合两路结果，并按关键词覆盖度排序 —— 见 HybridRetriever。\n"
    "想验证效果：python examples/debug_retrieval.py \"什么是列表推导式？\"\n"
    "────────────────────────────────────────────────────────"
)