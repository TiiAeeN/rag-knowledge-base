"""
RAG 知识库问答系统 - Web 界面（简化版）
支持本地 Qwen2.5（3B/7B）与外接 DeepSeek API
"""

import traceback

import streamlit as st

from rag_core import (
    ANSWER_MODE_KB_ONLY,
    ANSWER_MODE_LABELS,
    ANSWER_MODE_SMART,
    DEFAULT_MODEL,
    GENERAL_KNOWLEDGE_TAG,
    DEEPSEEK_API_KEY,
    RAGSystem,
    available_models,
    create_sample_knowledge,
    is_ollama_model_ready,
    resolve_answer_mode,
)

# 页面配置
st.set_page_config(
    page_title="RAG 知识库问答",
    page_icon="📚",
    layout="wide",
)

# 标题
st.title("📚 RAG 知识库问答系统")
st.markdown("---")

if "model_key" not in st.session_state:
    st.session_state.model_key = DEFAULT_MODEL

# 侧边栏
with st.sidebar:
    st.header("⚙️ 系统设置")

    specs = available_models()
    labels = [spec.label for spec in specs]
    keys = [spec.key for spec in specs]
    index = keys.index(st.session_state.model_key) if st.session_state.model_key in keys else 0

    selected_label = st.selectbox("选择对话模型", labels, index=index)
    spec = specs[labels.index(selected_label)]
    st.caption(spec.description)

    api_key = None
    if spec.provider == "deepseek":
        api_key = st.text_input("DeepSeek API Key", value=DEEPSEEK_API_KEY, type="password")

    if spec.provider == "ollama":
        if is_ollama_model_ready(spec.model):
            st.success(f"✅ 本地已下载 {spec.model}")
        else:
            st.warning(f"⚠️ 本地尚未下载 {spec.model}")
            st.code(f"ollama pull {spec.model}", language="bash")

    # 切换模型时立即生效（不需要重建向量库）
    if spec.key != st.session_state.model_key:
        st.session_state.model_key = spec.key
        if st.session_state.get("initialized"):
            try:
                st.session_state.rag.set_model(spec.key, api_key=api_key)
                st.success(f"✅ 已切换到 {spec.label}")
            except Exception as exc:
                st.error(f"❌ 切换模型失败: {exc}")

    # 回答方式：智能问答（知识库优先）/ 严格知识库
    options = [ANSWER_MODE_SMART, ANSWER_MODE_KB_ONLY]
    mode_labels = [ANSWER_MODE_LABELS[mode] for mode in options]
    current_mode = resolve_answer_mode(st.session_state.get("answer_mode"))
    selected_mode_label = st.radio(
        "回答方式",
        mode_labels,
        index=options.index(current_mode),
        key="answer_mode_selector",
    )
    answer_mode = options[mode_labels.index(selected_mode_label)]
    st.session_state["answer_mode"] = answer_mode
    if answer_mode == ANSWER_MODE_SMART:
        st.caption("知识库有的内容优先用知识库；没有的用模型自身知识回答。")
    else:
        st.caption("只根据知识库回答，没有的内容回答「未找到相关答案」。")

    if st.session_state.get("initialized") and st.session_state.rag.answer_mode != answer_mode:
        try:
            st.session_state.rag.set_answer_mode(answer_mode)
            st.success("✅ 已切换回答方式")
        except Exception as exc:
            st.error(f"❌ 切换回答方式失败: {exc}")

    st.info("""
    **模型说明：**
    - Qwen2.5-3B / 7B：本地 Ollama 推理，数据不出本机
    - DeepSeek-V3：外接 API，需要 API Key 和网络
    """)

    if st.button("🗑️ 清除缓存"):
        st.session_state.clear()
        st.rerun()

# 主区域
st.header("💬 问答区域")

# 初始化按钮
if 'initialized' not in st.session_state or not st.session_state.initialized:
    if st.button("🚀 初始化 RAG 系统", type="primary"):
        with st.spinner("正在初始化..."):
            try:
                # 创建示例文档
                create_sample_knowledge()

                # 初始化 RAG（使用侧边栏选择的模型）
                rag = RAGSystem(
                    model_key=st.session_state.model_key,
                    api_key=api_key,
                    answer_mode=st.session_state.get("answer_mode"),
                )
                success = rag.initialize()

                if success:
                    st.session_state.rag = rag
                    st.session_state.initialized = True
                    st.success("✅ 初始化完成！")
                    st.rerun()
                else:
                    st.error("❌ 初始化失败")
            except Exception as e:
                st.error(f"❌ 错误: {e}")
                st.code(traceback.format_exc())
else:
    rag = st.session_state.rag
    st.success(f"✅ RAG 系统已就绪！当前模型：{rag.model_spec.label}")

    question = st.text_input(
        "❓ 输入你的问题：",
        placeholder="例如：Python 中如何定义函数？"
    )

    if st.button("🔍 提问", type="primary"):
        if question.strip():
            with st.spinner("AI 正在思考..."):
                try:
                    result = rag.query(question)

                    st.markdown("### 🤖 AI 回答")
                    answer = result["answer"]
                    if answer.lstrip().startswith(GENERAL_KNOWLEDGE_TAG):
                        st.info("💡 知识库中没有找到相关内容，以下为模型自身知识的回答（非知识库内容）")
                        answer = answer.lstrip()[len(GENERAL_KNOWLEDGE_TAG):].lstrip()
                    st.write(answer)

                    sources = sorted(result.get("sources", []), key=lambda s: -s.get("score", 0.0))
                    relevant = [s for s in sources if s.get("relevance") in ("高", "中")]
                    if result.get("used_knowledge_base", True):
                        st.caption(f"🤖 模型: {result.get('model', rag.model_spec.label)} | 📚 参考来源: {len(relevant)} 条")
                    else:
                        st.caption(f"🤖 模型: {result.get('model', rag.model_spec.label)} | 📚 参考来源: 未使用知识库")

                    for index, source in enumerate(relevant, 1):
                        with st.expander(f"📄 来源 {index}｜相关度：{source['relevance']}"):
                            st.text(source['content'])
                except Exception as e:
                    st.error(f"❌ 查询出错: {e}")
                    st.code(traceback.format_exc())
        else:
            st.warning("请输入问题！")