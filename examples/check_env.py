"""
环境自检：一条命令看清依赖版本、Ollama 模型、知识库与向量库状态
用法： python examples/check_env.py

它不依赖 rag_core（即使 LangChain 装坏了也能跑），用来快速定位环境问题。
"""
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB_DIR = ROOT / "knowledge_base"
DB_DIR = ROOT / "data" / "chroma_db"
OLLAMA_HOST = "http://127.0.0.1:11434"
REQUIRED_PACKAGES = [
    ("langchain", "编排框架"),
    ("langchain-community", "文档加载 + Chroma 封装"),
    ("langchain-ollama", "对接 Ollama"),
    ("langchain-text-splitters", "文本切分"),
    ("chromadb", "向量数据库"),
    ("rank-bm25", "关键词检索"),
    ("pypdf", "读取 PDF"),
    ("streamlit", "Web 界面"),
    ("openai", "调用 DeepSeek"),
    ("python-dotenv", ".env 环境变量"),
]
REQUIRED_MODELS = ["qwen2.5:3b", "nomic-embed-text"]

print("=" * 62)
print("RAG 环境自检")
print("=" * 62)

# ① Python 版本
major, minor = sys.version_info[:2]
flag = "✅" if (major, minor) >= (3, 11) else "⚠️"
print(f"{flag} Python {sys.version.split()[0]}（建议 3.11+）")
print(f"   解释器：{sys.executable}")

# 判断当前用的是不是虚拟环境里的 Python（用全局 Python 跑，依赖必然全报未安装）
IN_VENV = sys.prefix != sys.base_prefix
if not IN_VENV:
    print("   ⚠️ 这不是虚拟环境里的 Python —— 下面「依赖包」会全部报未安装")
    print(r"   应改用：.venv\Scripts\python.exe examples\check_env.py")

# ② Python 依赖
print("\n[依赖包]")
try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:
    print("  ⚠️ importlib.metadata 不可用")
else:
    for name, role in REQUIRED_PACKAGES:
        try:
            print(f"  ✅ {name} {version(name)}  — {role}")
        except PackageNotFoundError:
            print(f"  ❌ {name} 未安装  — {role}")

# ③ Ollama 服务与模型
print(f"\n[Ollama 服务] {OLLAMA_HOST}")
try:
    with urllib.request.urlopen(f"{OLLAMA_HOST}/api/tags", timeout=5) as response:
        models = [item.get("name", "") for item in json.loads(response.read()).get("models", [])]
    print(f"  ✅ 服务可用，已下载 {len(models)} 个模型")
    for required in REQUIRED_MODELS:
        hit = any(m == required or m.startswith(required + ":") for m in models)
        print(f"  {'✅' if hit else '❌'} {required}{'' if hit else '（未下载，运行 ollama pull ' + required + '）'}")
    others = [m for m in models if not any(m.startswith(r) for r in REQUIRED_MODELS)]
    if others:
        print(f"  ℹ️ 其他模型: {', '.join(others[:6])}")
except Exception as exc:
    print(f"  ❌ 无法连接：{exc}")
    print("     解决：先启动 Ollama（桌面版打开即可，或运行 ollama serve）")

# ④ 知识库文档
print("\n[知识库文档]")
if KB_DIR.exists():
    files = [p for p in sorted(KB_DIR.iterdir())
             if p.is_file() and p.suffix.lower() in (".md", ".txt", ".pdf")]
    total_chars = sum(len(p.read_text(encoding="utf-8", errors="ignore")) for p in files if p.suffix.lower() != ".pdf")
    print(f"  ✅ {len(files)} 个文档（文本类约 {total_chars} 字）")
    for p in files[:5]:
        print(f"     📄 {p.name}")
    if len(files) > 5:
        print(f"     ... 还有 {len(files) - 5} 个")
else:
    print(f"  ❌ 目录不存在: {KB_DIR}")

# ⑤ 向量库
print("\n[向量库]")
try:
    import chromadb

    if DB_DIR.exists() and any(DB_DIR.iterdir()):
        client = chromadb.PersistentClient(path=str(DB_DIR))
        collections = client.list_collections()
        if collections:
            for item in collections:
                name = item.name if hasattr(item, "name") else str(item)
                print(f"  ✅ 集合 {name}：{client.get_collection(name).count()} 个文本块")
        else:
            print("  ⚠️ 目录存在但没有集合，需要初始化一次")
    else:
        print("  ⚠️ 尚未构建，启动后点「初始化 RAG 系统」即可")
except ImportError:
    print("  ❌ chromadb 未安装")
except Exception as exc:
    print(f"  ⚠️ 读取失败：{exc}")

print("\n" + "=" * 62)
if IN_VENV:
    print("全部 ✅ 即可直接运行： streamlit run app.py")
else:
    print("⚠️ 本次用的是全局 Python，上面「依赖包」全 ❌ 属正常现象，不代表环境坏了。")
    print(r"   请改用：.venv\Scripts\python.exe examples\check_env.py 重新自检")
print("=" * 62)