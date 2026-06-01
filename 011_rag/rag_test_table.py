from rag_bge_m3_class_table import RagBgeM3, get_llm, build_rag_components, runnable_lambda

rag = RagBgeM3()
llm = rag.get_llm()
retriever = rag.build_rag_components()

while True:
    human_message = input('[질문(q:exit)]')

    if human_message == 'q':
        exit()

    answer = rag.runnable_lambda(retriever, llm, human_message)

    print(answer)