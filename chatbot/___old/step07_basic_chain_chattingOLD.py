import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader

load_dotenv()
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

PDF_PATH = "source/manual.pdf"
DB_PATH = "./chroma_db_huggingface"

def get_llm():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️  GOOGLE_API_KEY 환경 변수가 없습니다.")
        print("   https://aistudio.google.com/apikey 에서 무료 발급 후 설정하세요.\n")
        return None
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0.7,
    )

def get_embeddings():
    """HuggingFace 로컬 임베딩 — API 키 불필요, 다국어 지원"""
    from langchain_huggingface import HuggingFaceEmbeddings
    print("  임베딩: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (로컬, API 키 불필요)")
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

def load_vectorstore():
    emb = get_embeddings()

    if os.path.exists(DB_PATH):
        print(f"  기존 '{DB_PATH}' 재사용")
        vs = Chroma(
            collection_name="jungdae_jaehai",
            embedding_function=emb,
            persist_directory=DB_PATH,
        )
        print(f"  → {vs._collection.count()}개 chunk 로드 완료\n")
        return vs

    print(f"  '{DB_PATH}' 없음 → '{PDF_PATH}'에서 새로 생성")
    exit()

def retrieve(vs, query: str, k: int = 3) -> str:
    docs = vs.similarity_search(query, k=k)
    return "\n\n".join(
        f"[p.{d.metadata.get('page','?')}] {d.page_content}" for d in docs
    )

def streaming(llm, vs, chat):
    print("=" * 50)
    print("[실습 2] 스트리밍 출력 (.stream())")

    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 중대재해처벌법 전문가입니다. 질문에 근거 있게 답변하세요."),
        ("human", "참고 문서:\n{context}\n\n질문: {question}"),
    ])
    chain = prompt | llm | StrOutputParser()

    question = chat
    context = retrieve(vs, question, k=3)

    print(f"  질문: '{question}'")
    print(f"  [실시간 출력 →] ", end="", flush=True)
    for token in chain.stream({"context": context, "question": question}):
        print(token, end="", flush=True)
    print("\n")

llm = get_llm()
if llm is None:
    print("API 키를 설정 후 다시 실행해주세요.")
    exit()

print("[VectorStore 준비 중...]")
vs = load_vectorstore()

while True:
    chat = input("[질의] ")
    streaming(llm, vs, chat)

