"""
교통사고 과실비율 RAG 챗봇 (Streamlit UI)

실행:
  uv run streamlit run app.py

RAG 모듈 교체 방법:
  아래 RAG_MODULE 값을 원하는 모듈 파일명(확장자 제외)으로 변경하면 됩니다.
  교체할 모듈은 ask(query: str) 또는 ask(query: str, json_input: str | None) 를 노출해야 합니다.
"""

import importlib
import inspect
import json

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── RAG 모듈 설정 (파일명만 바꾸면 교체됨) ───────────────────────────────────
RAG_MODULE = "baseline"   # "baseline"  또는  "main"  또는 다른 모듈명
# ─────────────────────────────────────────────────────────────────────────────


@st.cache_resource(show_spinner="RAG 모듈 초기화 중...")
def _load_ask_fn(module_name: str):
    """모듈을 임포트하고 통합 ask(query, json_input) 래퍼를 반환한다."""
    mod = importlib.import_module(module_name)

    # main.py: LangGraph 에이전트 + LightRAG 초기화
    if hasattr(mod, "build_agent") and hasattr(mod, "_run_in_rag_loop"):
        mod._run_in_rag_loop(mod._get_lightrag())
        agent = mod.build_agent()

        def _ask(query: str, json_input: str | None = None) -> str:
            result = agent.invoke({**mod._BLANK_STATE, "query": query, "json_input": json_input})
            return result.get("final_answer") or "답변을 생성하지 못했습니다."

        return _ask

    # 그 외 모듈: ask() 시그니처를 검사해서 호출
    sig = inspect.signature(mod.ask)
    accepts_json = "json_input" in sig.parameters

    def _ask(query: str, json_input: str | None = None) -> str:
        if accepts_json:
            return mod.ask(query, json_input=json_input)
        return mod.ask(query)

    return _ask


def _render_sidebar() -> str | None:
    """사이드바를 렌더링하고 유효한 JSON 문자열(또는 None)을 반환한다."""
    with st.sidebar:
        st.title("⚖️ 과실비율 AI")
        st.caption(f"모듈: `{RAG_MODULE}`")
        st.divider()

        if st.button("대화 초기화", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.divider()
        st.subheader("사고 상황 JSON (선택)")
        st.caption("main 모듈 사용 시 구조화된 사고 정보를 추가할 수 있습니다.")

        raw_json = st.text_area(
            "JSON 입력",
            placeholder='{"사고유형": "교차로", "신호": "적색신호위반"}',
            height=180,
            label_visibility="collapsed",
            key="json_input_area",
        )

        if raw_json.strip():
            try:
                json.loads(raw_json)
                st.success("JSON 형식 정상")
                return raw_json.strip()
            except json.JSONDecodeError as e:
                st.error(f"JSON 오류: {e}")
                return None

    return None


def main():
    st.set_page_config(
        page_title="교통사고 과실비율 AI",
        page_icon="⚖️",
        layout="wide",
    )

    json_input = _render_sidebar()

    st.header("교통사고 과실비율 AI 챗봇")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 채팅 히스토리 출력
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 질문 입력
    if query := st.chat_input("사고 상황을 입력하세요..."):
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        ask_fn = _load_ask_fn(RAG_MODULE)

        with st.chat_message("assistant"):
            with st.spinner("분석 중..."):
                answer = ask_fn(query, json_input)
            st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()
