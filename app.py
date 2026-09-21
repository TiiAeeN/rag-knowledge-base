"""
RAG 知识库问答系统 - Web 界面
基于 Streamlit 构建，支持本地 Qwen2.5（3B/7B）与外接 DeepSeek API
"""

import time
from pathlib import Path
from typing import Dict

import streamlit as st

from rag_core import (
    ANSWER_MODE_KB_ONLY,
    ANSWER_MODE_LABELS,
    ANSWER_MODE_SMART,
    DEFAULT_MODEL,
    DEEPSEEK_API_KEY,
    EMBEDDING_MODEL,
    GENERAL_KNOWLEDGE_TAG,
    KNOWLEDGE_BASE_DIR,
    RAGSystem,
    available_models,
    create_sample_knowledge,
    is_ollama_model_ready,
    pull_ollama_model,
    resolve_answer_mode,
)

# 页面配置
st.set_page_config(
    page_title="RAG 知识库问答",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 自定义 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_rag_system() -> RAGSystem:
    """获取 RAG 系统实例（全局缓存，模型可随时切换，无需重建向量库）"""
    return RAGSystem()


@st.cache_data(ttl=10, show_spinner=False)
def ollama_model_ready(model_name: str) -> bool:
    """查询本地 Ollama 是否已下载该模型（10 秒缓存）"""
    return is_ollama_model_ready(model_name)


def render_model_selector() -> None:
    """侧边栏：对话模型选择（本地 Qwen2.5-3B/7B 或外接 DeepSeek API）"""
    st.subheader("🤖 对话模型")

    specs = available_models()
    labels = [spec.label for spec in specs]
    keys = [spec.key for spec in specs]

    current_key = st.session_state.get("model_key", DEFAULT_MODEL)
    index = keys.index(current_key) if current_key in keys else 0
    selected_label = st.selectbox("选择对话模型", labels, index=index, key="model_selector")
    spec = specs[labels.index(selected_label)]
    st.caption(spec.description)

    api_key_input = None
    if spec.provider == "deepseek":
        api_key_input = st.text_input(
            "DeepSeek API Key",
            value=st.session_state.get("deepseek_api_key", DEEPSEEK_API_KEY),
            type="password",
            help="留空则使用 DEEPSEEK_API_KEY 环境变量或 rag_core.py 中的默认配置",
        )
        st.session_state["deepseek_api_key"] = api_key_input

    # 模型变化立即生效：只替换对话模型，不需要重建向量库
    applied_key = st.session_state.get("applied_model_key")
    applied_api_key = st.session_state.get("applied_api_key")
    if spec.key != applied_key or (spec.provider == "deepseek" and api_key_input != applied_api_key):
        try:
            get_rag_system().set_model(
                spec.key,
                api_key=api_key_input if spec.provider == "deepseek" else None,
            )
            st.session_state.applied_model_key = spec.key
            st.session_state.applied_api_key = api_key_input
            st.session_state.model_key = spec.key
            if applied_key is not None:  # 首次加载时不提示
                st.success(f"✅ 已切换到 {spec.label}")
        except Exception as exc:
            st.error(f"❌ 切换模型失败: {exc}")

    # 本地模型：检查是否已下载，未下载则支持一键下载
    if spec.provider == "ollama":
        if ollama_model_ready(spec.model):
            st.success(f"✅ 本地已就绪：{spec.model}")
        else:
            st.warning(f"⚠️ 本地尚未下载：{spec.model}")
            st.code(f"ollama pull {spec.model}", language="bash")
            if st.button("⬇️ 一键下载该模型", use_container_width=True):
                progress = st.progress(0.0, text="开始下载...")

                def _on_progress(status: str, percent: float) -> None:
                    progress.progress(
                        min(max(percent, 0.0), 1.0),
                        text=f"{status} {percent * 100:.1f}%",
                    )

                if pull_ollama_model(spec.model, _on_progress):
                    ollama_model_ready.clear()
                    st.success("✅ 模型下载完成！")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ 模型下载失败，可尝试用上面的命令行手动下载")


def render_answer_mode() -> None:
    """侧边栏：回答方式（智能问答 / 严格知识库）"""
    st.subheader("💡 回答方式")

    options = [ANSWER_MODE_SMART, ANSWER_MODE_KB_ONLY]
    labels = [ANSWER_MODE_LABELS[mode] for mode in options]
    current = resolve_answer_mode(st.session_state.get("answer_mode"))
    selected_label = st.radio(
        "选择回答方式",
        labels,
        index=options.index(current),
        key="answer_mode_selector",
        label_visibility="collapsed",
    )
    mode = options[labels.index(selected_label)]
    st.session_state["answer_mode"] = mode

    if mode == ANSWER_MODE_SMART:
        st.caption("知识库有的内容优先依据知识库回答；知识库里没有的问题，用模型自身知识回答（会标注「通用知识」）。")
    else:
        st.caption("只依据知识库回答；知识库里没有的问题会回答「未找到相关答案」。")

    if mode != st.session_state.get("applied_answer_mode"):
        try:
            get_rag_system().set_answer_mode(mode)
            applied_before = st.session_state.get("applied_answer_mode")
            st.session_state.applied_answer_mode = mode
            if applied_before is not None:  # 首次加载时不提示
                st.success("✅ 已切换回答方式")
        except Exception as exc:
            st.error(f"❌ 切换回答方式失败: {exc}")


KNOWLEDGE_FILE_SUFFIXES = (".md", ".txt", ".pdf")


def knowledge_base_files():
    """知识库目录下的文档文件列表"""
    if not KNOWLEDGE_BASE_DIR.exists():
        return []
    return sorted(
        f
        for f in KNOWLEDGE_BASE_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in KNOWLEDGE_FILE_SUFFIXES
    )


def render_knowledge_base_status() -> None:
    """侧边栏：知识库文档状态"""
    st.subheader("📂 知识库状态")
    files = knowledge_base_files()
    if files:
        st.success(f"✅ 共 {len(files)} 个文档")
        for f in files[:5]:  # 只显示前5个
            st.text(f"  📄 {f.name}")
        if len(files) > 5:
            st.text(f"  ... 还有 {len(files) - 5} 个文件")
    else:
        st.warning("⚠️ 知识库目录为空")


def save_uploaded_files(uploaded_files) -> int:
    """把网页上传的文档保存到 knowledge_base 目录，返回新增文件数"""
    KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
    saved = 0
    for uploaded in uploaded_files:
        target = KNOWLEDGE_BASE_DIR / Path(uploaded.name).name
        if target.exists():
            st.warning(f"⚠️ 已存在同名文件，跳过：{target.name}")
            continue
        target.write_bytes(uploaded.getvalue())
        saved += 1
    return saved


def render_operations() -> None:
    """侧边栏：知识库操作"""
    st.subheader("🔧 操作")

    with st.expander("➕ 添加自己的文档"):
        st.caption("支持 .md / .txt / .pdf，可一次选多个文件；保存后点「重建知识库」即可提问。")
        uploaded = st.file_uploader(
            "选择要加入知识库的文件",
            type=["md", "txt", "pdf"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        if uploaded and st.button("📥 保存到知识库", use_container_width=True):
            saved = save_uploaded_files(uploaded)
            if saved:
                st.success(f"✅ 已添加 {saved} 个文档，请点击「🔄 重建知识库」让新内容生效")
            else:
                st.info("没有新增文件（可能都是同名文件）")

    if st.button("🔄 重建知识库", use_container_width=True):
        rag = get_rag_system()
        if st.session_state.get("initialized"):
            with st.spinner("正在重建知识库..."):
                try:
                    if rag.initialize(force_rebuild=True):
                        st.success(f"✅ 知识库已重建（{len(knowledge_base_files())} 个文档）")
                    else:
                        st.error("❌ 重建失败：知识库目录中没有文档")
                except Exception as exc:
                    st.error(f"❌ 重建失败: {exc}")
        else:
            st.session_state["need_rebuild"] = True
            st.info("已标记重建，点击「初始化 RAG 系统」后生效")

    if st.button("📝 创建示例文档", use_container_width=True):
        create_sample_knowledge()
        st.success("✅ 示例文档已创建！")
        time.sleep(1)
        st.rerun()


def render_system_info() -> None:
    """侧边栏：当前系统信息"""
    st.subheader("ℹ️ 系统信息")
    rag = get_rag_system()
    spec = rag.model_spec
    provider_text = "本地 Ollama" if spec.provider == "ollama" else "外接 DeepSeek API"
    st.info(f"""
**模型配置：**
- 对话模型: {spec.label}
- 推理方式: {provider_text}
- 向量模型: {EMBEDDING_MODEL}
- 检索方式: 向量 + BM25 混合检索
- 回答方式: {ANSWER_MODE_LABELS[rag.answer_mode]}

**硬件加速：**
- GPU: NVIDIA RTX 4060
- 本地推理: Ollama
""")


def source_file_name(source: Dict) -> str:
    """从元数据里取来源文件名"""
    metadata = source.get("metadata") or {}
    path = metadata.get("source") or metadata.get("file_path")
    return Path(path).name if path else "知识库"


def render_sources(result: Dict) -> None:
    """展示参考来源：按相关度排序，只突出与问题相关的片段"""
    sources = sorted(result.get("sources", []), key=lambda item: -item.get("score", 0.0))
    relevant = [s for s in sources if s.get("relevance") in ("高", "中")]
    weak = [s for s in sources if s.get("relevance") not in ("高", "中")]

    if not result.get("used_knowledge_base", True):
        st.warning("本次回答来自模型自身知识，**未使用知识库内容**。")
    elif relevant:
        st.caption(f"检索到 {len(relevant)} 个与问题相关的片段（按相关度排序）")

    for index, source in enumerate(relevant, 1):
        title = f"📄 来源 {index}｜相关度：{source['relevance']}｜{source_file_name(source)}"
        with st.expander(title, expanded=(index == 1)):
            st.markdown(source["content"])
            st.caption(f"相关度评分：{source.get('score', 0):.2f}")

    if weak:
        with st.expander(f"🗂️ 其他检索到的片段（与问题关系不大，共 {len(weak)} 条）"):
            for source in weak:
                st.markdown(f"**{source_file_name(source)}**")
                st.markdown(source["content"])
                st.divider()


def main():
    # 标题
    st.markdown('<p class="main-header">📚 RAG 知识库问答系统</p>', unsafe_allow_html=True)
    st.markdown("---")

    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 系统设置")
        render_model_selector()
        st.divider()
        render_answer_mode()
        st.divider()
        render_knowledge_base_status()
        st.divider()
        render_operations()
        st.divider()
        render_system_info()

    # 主区域
    col1, col2 = st.columns([3, 2])

    with col1:
        st.header("💬 问答区域")

        if 'initialized' not in st.session_state:
            st.session_state.initialized = False

        if not st.session_state.get('initialized', False):
            st.info(f"当前选择的模型：**{get_rag_system().model_spec.label}**")

            if st.button("🚀 初始化 RAG 系统", type="primary", use_container_width=True):
                with st.status("正在初始化...", expanded=True) as status:
                    st.write("📂 加载文档...")
                    time.sleep(0.5)
                    st.write("🔍 构建向量索引...")
                    time.sleep(0.5)
                    st.write("🤖 加载 AI 模型...")
                    time.sleep(0.5)

                    try:
                        rag = get_rag_system()
                        force = st.session_state.get('need_rebuild', False)
                        success = rag.initialize(force_rebuild=force)
                        if success:
                            st.session_state.rag = rag
                            st.session_state.initialized = True
                            st.session_state.need_rebuild = False
                            status.update(label="✅ 初始化完成！", state="complete")
                            st.rerun()
                        else:
                            status.update(label="❌ 初始化失败", state="error")
                    except Exception as e:
                        status.update(label=f"❌ 错误: {str(e)}", state="error")
        else:
            # 问答界面
            rag = st.session_state.rag
            st.success(f"✅ RAG 系统已就绪（当前模型：{rag.model_spec.label}），可以开始提问！")

            # 问题输入
            question = st.text_input(
                "❓ 输入你的问题：",
                placeholder="例如：Python 中如何定义函数？",
                key="question_input"
            )

            # 提问按钮
            if st.button("🔍 提问", type="primary", use_container_width=True):
                if question.strip():
                    with st.spinner("AI 正在思考..."):
                        start_time = time.time()
                        try:
                            result = rag.query(question)
                            elapsed = time.time() - start_time

                            # 显示回答
                            st.session_state.last_result = result
                            st.session_state.response_time = elapsed
                        except Exception as e:
                            st.error(f"❌ 查询出错: {str(e)}")
                else:
                    st.warning("请输入问题！")

            # 显示结果
            if 'last_result' in st.session_state:
                result = st.session_state.last_result
                elapsed = st.session_state.get('response_time', 0)

                st.divider()

                # 回答区域
                st.markdown("### 🤖 AI 回答")
                answer = result["answer"]
                if answer.lstrip().startswith(GENERAL_KNOWLEDGE_TAG):
                    st.info("💡 知识库中没有找到相关内容，以下为模型自身知识的回答（非知识库内容）")
                    answer = answer.lstrip()[len(GENERAL_KNOWLEDGE_TAG):].lstrip()
                with st.container(border=True):
                    st.markdown(answer)

                # 响应时间与来源统计
                relevant_count = len(
                    [s for s in result.get("sources", []) if s.get("relevance") in ("高", "中")]
                )
                if result.get("used_knowledge_base", True):
                    source_text = f"📚 参考来源: {relevant_count} 条"
                else:
                    source_text = "📚 参考来源: 未使用知识库"
                st.caption(
                    f"⏱️ 响应时间: {elapsed:.2f} 秒 | {source_text} "
                    f"| 🤖 模型: {result.get('model', rag.model_spec.label)}"
                )

    with col2:
        st.header("📚 参考来源")

        if 'last_result' in st.session_state:
            render_sources(st.session_state.last_result)
        else:
            st.info("提问后，参考来源会显示在这里")


# 运行应用
if __name__ == "__main__":
    main()