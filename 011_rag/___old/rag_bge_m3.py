from rag_bge_m3_lib import get_llm, build_rag_components, basic_rag_chain, runnable_lambda

try:
    llm = get_llm()
    retriever = build_rag_components()
except:
    print("llm, vectorDB 호출 실패")
    exit()

while True:
    human_message = input("[질문(q:종료)]")
    if human_message == 'q':
        exit()
    
    # ai_message = basic_rag_chain(retriever, llm, human_message)
    # LECL 방식 전처리 포함 구현
    ai_message = runnable_lambda(retriever, llm, human_message)

    print(f"[AI] {ai_message}")