"""
检索调试工具：不调用大模型，直接看"某个问题会命中哪些文本块、分数多少"
用法： python examples/debug_retrieval.py "快速排序和归并排序有什么区别？"

用途：调知识库、改检索参数时，用它可以秒级看到效果，不用等模型推理。
"""
import sys

from rag_core import RAGSystem, relevance_label, source_relevance

question = sys.argv[1] if len(sys.argv) > 1 else "快速排序和归并排序有什么区别？"

rag = RAGSystem(model_key="qwen2.5:3b")
rag.initialize(force_rebuild=False)          # 用已有向量库，不重建

print(f"\n❓ {question}\n")
for index, (doc, info) in enumerate(rag._retriever.retrieve_with_scores(question), 1):
    score = source_relevance(info)
    name = doc.metadata.get("source", "?").replace("\\", "/").split("/")[-1]
    print(
        f"--- 片段 {index}｜{relevance_label(score)}（{score:.2f}）｜{name}"
        f"｜覆盖度 {info['coverage']:.2f}"
        f"｜向量排名 {int(info['vector_rank'])}"
        f"｜关键词排名 {int(info['keyword_rank'])}"
    )
    print(doc.page_content[:280].replace("\n", " "))
    print()