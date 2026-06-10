import json
import os
import re
import subprocess
import sys
import time
from typing import TypedDict, Annotated, List, Optional, Literal

# ══════════════════════════════════════════════════════════
# 설정값
# ══════════════════════════════════════════════════════════

GMAIL_SEARCH_QUERY  = "is:unread in:inbox"
MAX_EMAILS          = 5
DRAFT_ONLY          = True          # True=드래프트 / False=즉시 발송
GEMINI_MODEL        = "gemini-3.1-flash-lite"
DEFAULT_CALENDAR    = "primary"

URGENCY_HIGH        = "높음"    # ④-B 복잡예외 분기 기준
SIMPLE_CATEGORIES   = {"단순문의", "FAQ", "배송조회"}  # ④-C 단순 처리 분기
RAG_CATEGORIES      = {"약관문의", "이용방법문의", "배송문의", "기술지원", "계정문의", "일반문의"}  # ④-A RAG 처리 분기

RAG_DB_PATH         = "rag_data/cs"
BGE_MODEL_NAME      = "BAAI/bge-m3"
RAG_COLLECTION      = "terms_of_service"
RAG_TOP_K           = 5
RAG_SCORE_THRESHOLD = 0.35

# .env 속성 정보를 가져오는 함수
from dotenv import load_dotenv
load_dotenv()

from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

# 언어모델 설정
llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
   temperature=0.3)

llm_creative = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
   temperature=0.7)

def _extract_text(content) -> str:
    """LLM 응답 content가 str / list[dict] / list[str] 어느 형태든 문자열로 변환."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                text = block.get("text", "")
                parts.append(" ".join(str(t) for t in text) if isinstance(text, list) else str(text))
            else:
                parts.append(str(block))
        return " ".join(parts)
    return str(content) if content is not None else ""

################################################################
# 함수 선언부분
################################################################
class EmailState(TypedDict):
    # ── ① Gmail 수신 ────────────────────────────────
    email_id:        str     # thread_id (Gmail)
    message_id:      str
    sender_email:    str
    customer_name:   str
    subject:         str     # State: subject
    body:            str     # State: body  (원본 본문)

    # ── ② 중요도 분석 결과 ───────────────────────────
    urgency:         str     # State: urgency  높음|보통|낮음
    topic:           str     # State: topic    카테고리
    sentiment:       str     # 긍정|부정|중립

    # ── ③ 라우팅 결과 ────────────────────────────────
    route:           str     # "rag" | "escalate" | "auto"

    # ── ④-A RAG 검색 결과 ───────────────────────────
    rag_context:     str
    rag_sources:     List[str]

    # ── ④-B 예외 처리 결과 ──────────────────────────
    escalation_note: str     # 상담원에게 전달할 메모

    # ── ④-C / 공통 응답 ─────────────────────────────
    draft:           str     # State: draft  (응답 초안)
    action:          str     # State: action (수행할 액션 메모)

    # ── ⑤ 이관 & Tools ──────────────────────────────
    tools_called:    List[str]   # 호출된 외부 툴 목록
    tools_result:    str         # 툴 결과 요약

    # ── ⑥ 일정 예약 ──────────────────────────────────
    has_schedule:    bool
    schedule_info:   Optional[dict]
    calendar_event_id: str

    # ── ⑦ 발송 결과 ──────────────────────────────────
    draft_id:        str
    processed:       bool

    # ── 품질검토 루프 ────────────────────────────────
    revision_count:  int
    needs_revision:  bool
    review_feedback: str

# (2) 중요도 분석 — 긴급도·주제 분류 (LLM)
def analyze_importance(state: EmailState) -> dict:
    print(f"\n┌{'─'*61}┐")
    print(f"│  ② 중요도 분석 — 긴급도·주제 분류                        │")
    print(f"└{'─'*61}┘")

    res = llm.invoke([
        SystemMessage(content="""
고객 이메일 중요도 분석 전문가입니다. 아래 형식 세 줄만 출력하세요.
긴급도: [높음|보통|낮음] 중 하나
주제: [환불요청|배송문의|약관문의|이용방법문의|기술지원|계정문의|단순문의|FAQ|배송조회|복잡민원|일반문의] 중 하나
감정: [긍정|부정|중립] 중 하나

분류 기준:
- 높음: 환불·결제오류·장애·강한 불만
- 보통: 일반 문의·배송 확인·기술 지원
- 낮음: FAQ·단순 조회·칭찬
- 복잡민원: 법적 위협·반복 불만·다수 이슈 복합

주제 선택 기준:
- 약관문의: 이용약관·환불정책·반품정책·청약철회·계약조건 관련 질문
- 이용방법문의: 서비스 이용방법·회원가입·결제방법·주문절차 관련 질문
- 배송문의: 배송기간·배송비·배송현황·배송지역 관련 질문
- FAQ: 반복적으로 묻는 단순 정보 확인
- 배송조회: 특정 주문의 배송 추적 요청
        """),
        HumanMessage(content=f"제목: {state['subject']}\n\n{state['body']}"),
    ])

    content = _extract_text(res.content)

    urgency, topic, sentiment = "보통", "일반문의", "중립"
    for line in content.strip().splitlines():
        if line.startswith("긴급도:"):
            urgency   = line.split(":", 1)[1].strip()
        elif line.startswith("주제:"):
            topic     = line.split(":", 1)[1].strip()
        elif line.startswith("감정:"):
            sentiment = line.split(":", 1)[1].strip()

    print(f"   → 긴급도: {urgency} | 주제: {topic} | 감정: {sentiment}")
    return {"urgency": urgency, "topic": topic, "sentiment": sentiment}

# 의사결정 함수.
def decide_route(state: EmailState) -> dict:
    print(f"\n┌{'─'*61}┐")
    print(f"│  ③ 라우팅 — conditional_edge 분기                        │")
    print(f"└{'─'*61}┘")

    topic   = state.get("topic", "")
    urgency = state.get("urgency", "보통")

    # 복잡예외: 긴급도 높음 또는 복잡민원
    if urgency == URGENCY_HIGH or topic in {"복잡민원", "환불요청"}:
        route = "escalate"
    # 단순처리: FAQ·단순문의·배송조회
    elif topic in SIMPLE_CATEGORIES:
        route = "auto"
    # RAG 처리: 약관·이용방법·배송문의 등 이용약관.md 참조 필요 주제
    elif topic in RAG_CATEGORIES:
        route = "rag"
    # 그 외: RAG 검색
    else:
        route = "rag"

    label = {"rag": "일반문의 → ④-A RAG 검색",
             "escalate": "복잡예외 → ④-B 상담원 연결",
             "auto": "단순처리 → ④-C 자동 생성"}[route]
    print(f"   → {label}")
    return {"route": route}

# ══════════════════════════════════════════════════════════
# RAG 벡터스토어 (앱 시작 시 1회 초기화)
# ══════════════════════════════════════════════════════════

_vectorstore: Optional[Chroma] = None

def get_vectorstore() -> Optional[Chroma]:
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    if not os.path.exists(RAG_DB_PATH):
        print(f"⚠  RAG DB 없음 ({RAG_DB_PATH}) — RAG 없이 실행")
        return None

    print(f"📚 RAG 벡터DB 로딩 중... ({RAG_DB_PATH})")
    try:
        emb = HuggingFaceBgeEmbeddings(
            model_name=BGE_MODEL_NAME,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True, "batch_size": 32},
        )
        _vectorstore = Chroma(
            collection_name=RAG_COLLECTION,
            embedding_function=emb,
            persist_directory=RAG_DB_PATH,
        )
        print(f"   → 로드 완료 (문서 {_vectorstore._collection.count()}개)")
    except Exception as e:
        print(f"⚠  RAG 초기화 실패: {e}")
        _vectorstore = None
    return _vectorstore

# A RAG 검색 — 사내 문서 벡터 검색
def rag_search(state: EmailState) -> dict:
    print(f"\n┌{'─'*61}┐")
    print(f"│  ④-A RAG 검색 — 사내 문서 벡터 검색 (BGE-M3)             │")
    print(f"└{'─'*61}┘")

    vs = get_vectorstore()
    if vs is None:
        print("   → RAG DB 없음 — 빈 컨텍스트로 진행")
        return {"rag_context": "", "rag_sources": [], "action": "rag_fallback"}

    query = f"[주제: {state['topic']}]\n제목: {state['subject']}\n{state['body'][:300]}"

    try:
        docs_scores = vs.similarity_search_with_relevance_scores(query, k=RAG_TOP_K)
        filtered    = [(d, s) for d, s in docs_scores if s >= RAG_SCORE_THRESHOLD]

        if not filtered:
            print(f"   → 관련 문서 없음 (임계값 {RAG_SCORE_THRESHOLD} 미만)")
            return {"rag_context": "", "rag_sources": [], "action": "rag_no_result"}

        blocks, sources = [], []
        for i, (doc, score) in enumerate(filtered, 1):
            title = doc.metadata.get("title", doc.metadata.get("source", f"문서{i}"))
            sources.append(title)
            blocks.append(f"[참고자료 {i}] {title} (관련도: {score:.2f})\n{doc.page_content}")
            print(f"   • {title[:45]} (유사도: {score:.2f})")

        return {
            "rag_context": "\n\n".join(blocks),
            "rag_sources": sources,
            "action": "rag_retrieved",
        }
    except Exception as e:
        print(f"   ⚠ RAG 오류: {e}")
        return {"rag_context": "", "rag_sources": [], "action": "rag_error"}

# ────────────────────────────────────────────────────────
# ④-A 합류점 — RAG 결과 기반 응답 초안 생성
# ────────────────────────────────────────────────────────

def generate_rag_response(state: EmailState) -> dict:
    print(f"\n┌{'─'*61}┐")
    print(f"│  ④-A 응답 생성 — RAG 컨텍스트 기반 초안                  │")
    print(f"└{'─'*61}┘")

    tone = {
        "부정": "공감하고 사과하는 톤으로, 빠른 해결을 약속하며",
        "긍정": "밝고 친근한 톤으로",
        "중립": "전문적이고 친절한 톤으로",
    }.get(state.get("sentiment", "중립"), "전문적이고 친절한 톤으로")

    rag_block = ""
    if state.get("rag_context"):
        rag_block = (
            f"\n\n[CS 지식베이스 — 반드시 우선 참고]\n"
            f"{'─'*40}\n{state['rag_context']}\n{'─'*40}\n"
            f"위 내용의 정책·수치를 정확히 인용하세요. 없는 내용은 만들지 마세요."
        )

    feedback = (f"\n\n[필수 반영 피드백]\n{state['review_feedback']}"
                if state.get("revision_count", 0) > 0 else "")

    res = llm_creative.invoke([
        SystemMessage(content=f"""
고객 서비스 전문가입니다. {tone} 답변하세요.{rag_block}

규칙:
- 고객 이름 첫 문장 포함
- 인사 → 공감 → 본문(지식베이스 기반) → 추가도움 → 마무리
- 200~400자 이내
- 서명: "고객 서비스팀 드림"{feedback}
        """),
        HumanMessage(content=
            f"고객명: {state['customer_name']}\n제목: {state['subject']}\n"
            f"주제: {state['topic']} | 긴급도: {state['urgency']} | 감정: {state['sentiment']}\n\n"
            f"원본:\n{state['body']}"
        ),
    ])

    draft = _extract_text(res.content).strip()
    print("------- 초안 작성 ------")
    print(draft)
    print("-----------------------")

    print(f"   → 초안 완료 ({len(draft)}자)"
          + (" [RAG 적용]" if state.get("rag_context") else " [RAG 없음]"))
    return {"draft": draft, "revision_count": state.get("revision_count", 0)}

# ────────────────────────────────────────────────────────
# ④-B 예외 처리 — 상담원 연결 라우팅
# ────────────────────────────────────────────────────────

def escalate_to_agent(state: EmailState) -> dict:
    print(f"\n┌{'─'*61}┐")
    print(f"│  ④-B 예외 처리 — 상담원 연결 라우팅                      │")
    print(f"└{'─'*61}┘")

    # 상담원 전달용 요약 생성
    res = llm.invoke([
        SystemMessage(content="""
고객 서비스 매니저입니다.
아래 이메일을 상담원에게 인계할 간략한 요약을 작성하세요.
형식: [긴급도] 주제 | 고객명 | 핵심 이슈 1줄 | 권장 조치
        """),
        HumanMessage(content=
            f"긴급도: {state['urgency']} | 주제: {state['topic']}\n"
            f"고객: {state['customer_name']}\n"
            f"제목: {state['subject']}\n\n{state['body'][:400]}"
        ),
    ])

    note = _extract_text(res.content).strip()
    print(f"   → 상담원 인계 메모 생성 완료")
    # print(f"   {note[:80]}...")
    print(f"   {note}...")

    # 상담원 안내 임시 응답 초안 생성
    draft_res = llm_creative.invoke([
        SystemMessage(content="""
고객 서비스 담당자입니다.
고객에게 담당 상담원이 곧 연락드릴 것임을 안내하는 정중한 응답을 작성하세요.
150~200자, 서명: "고객 서비스팀 드림"
        """),
        HumanMessage(content=
            f"고객명: {state['customer_name']}\n"
            f"제목: {state['subject']}\n"
            f"긴급도: {state['urgency']}"
        ),
    ])

    print("----- 상담사 답변 초안 ------")
    escalation_draft = _extract_text(draft_res.content).strip()
    print(escalation_draft)
    print("---------------------------")

    return {
        "escalation_note": note,
        "draft": escalation_draft,
        "action": "escalated",
    }

# ────────────────────────────────────────────────────────
# ④-C 자동 생성 — 답변 초안 Agent (단순 처리)
# ────────────────────────────────────────────────────────

def auto_generate(state: EmailState) -> dict:
    print(f"\n┌{'─'*61}┐")
    print(f"│  ④-C 자동 생성 — 답변 초안 Agent                         │")
    print(f"└{'─'*61}┘")

    res = llm_creative.invoke([
        SystemMessage(content="""
고객 서비스 자동응답 시스템입니다.
단순·FAQ 문의에 대해 명확하고 친절한 답변을 작성하세요.
규칙: 고객 이름 포함 / 150~250자 / 서명: "고객 서비스팀 드림"
        """),
        HumanMessage(content=
            f"고객명: {state['customer_name']}\n"
            f"제목: {state['subject']}\n주제: {state['topic']}\n\n{state['body']}"
        ),
    ])

    draft = _extract_text(res.content).strip()
    print(f"   → 자동 초안 생성 완료 ({len(draft)}자)")
    return {"draft": draft, "action": "auto_generated"}


# ────────────────────────────────────────────────────────
# 품질 검토 루프 (④-A / ④-C 공통)
# ────────────────────────────────────────────────────────

def review_draft(state: EmailState) -> dict:
    print(f"\n┌{'─'*61}┐")
    print(f"│  품질 검토 — 응답 초안 검토 (최대 2회 루프)               │")
    print(f"└{'─'*61}┘")

    # escalate 경로는 검토 없이 바로 통과
    if state.get("action") == "escalated":
        print("   → 상담원 인계 경로 — 검토 건너뜀")
        return {"needs_revision": False, "final_response": state.get("draft", "")}

    res = llm.invoke([
        SystemMessage(content="""
고객 서비스 품질 검토자입니다.
평가 기준: ①감정공감 ②실질해결책 ③문법 ④전문친근톤 ⑤200~400자
첫 줄에 "승인" 또는 "수정필요", 수정 필요 시 두 번째 줄부터 피드백.
        """),
        HumanMessage(content=
            f"[원본]\n{state['body']}\n\n"
            f"[초안]\n{state['draft']}\n\n"
            f"[주제: {state['topic']} | 감정: {state['sentiment']} | 긴급도: {state['urgency']}]"
        ),
    ])

    review_text = _extract_text(res.content).strip()
    lines  = review_text.splitlines()

    print("---- 최종 승인 검토 -----")
    print(lines)
    print("-----------------------")
    
    revise = lines[0].strip() != "승인"
    fb     = "\n".join(lines[1:]).strip() if revise else ""

    if revise and state.get("revision_count", 0) >= 2:
        print("   → 최대 수정 횟수 도달 → 강제 승인")
        revise = False

    print(f"   → {'🔄 수정 필요' if revise else '✅ 승인'}")
    return {
        "needs_revision":  revise,
        "review_feedback": fb,
        "final_response":  state["draft"] if not revise else "",
        "revision_count":  state.get("revision_count", 0) + (1 if revise else 0),
    }

# ────────────────────────────────────────────────────────
# ⑤ 이관 & Tools 처리 — 복잡 이슈 → 외부 Tools 호출
# ────────────────────────────────────────────────────────

def tools_handler(state: EmailState) -> dict:
    print(f"\n┌{'─'*61}┐")
    print(f"│  ⑤ 이관 & Tools — 복잡 이슈 외부 Tools 호출              │")
    print(f"└{'─'*61}┘")

    called, results = [], []

    # ── 배송 조회 Tool ───────────────────────────────
    if state["topic"] in {"배송문의", "배송조회"}:
        print("   🔧 배송조회 Tool 호출...")
        called.append("delivery_tracker")
        results.append("배송조회: 현재 배송중 (예상 도착 2-3 영업일)")

    # ── 주문/결제 조회 Tool ──────────────────────────
    if state["topic"] in {"환불요청", "계정문의"}:
        print("   🔧 주문조회 Tool 호출...")
        called.append("order_lookup")
        results.append("주문조회: 최근 주문 확인됨 (환불 신청 가능 상태)")

    # ── 상담원 티켓 생성 Tool (escalate 경로) ─────────
    if state.get("action") == "escalated":
        print("   🔧 티켓 생성 Tool 호출...")
        called.append("ticket_creator")
        results.append(f"티켓 생성 완료: [{state['urgency']}] {state['customer_name']} — {state['subject'][:40]}")

    if called:
        print(f"   → {len(called)}개 Tool 호출 완료: {', '.join(called)}")
    else:
        print("   → 추가 Tool 호출 없음")

    return {
        "tools_called":  called,
        "tools_result":  "\n".join(results),
    }

# ────────────────────────────────────────────────────────
# ⑥ 후속 일정 예약 — 캘린더 MCP
# ────────────────────────────────────────────────────────

def schedule_followup(state: EmailState) -> dict:
    print(f"\n┌{'─'*61}┐")
    print(f"│  ⑥ 후속 일정 예약 — 캘린더 MCP                           │")
    print(f"└{'─'*61}┘")

    combined = f"제목: {state['subject']}\n\n{state['body']}"

    res = llm.invoke([
        SystemMessage(content=f"""
이메일에서 미팅·회의·약속·방문·상담 일정을 추출하세요.
오늘: {time.strftime('%Y-%m-%d')}

일정 있으면:
{{"has_schedule":true,"title":"...","date":"YYYY-MM-DD",
  "start_time":"HH:MM","end_time":"HH:MM","location":"...","description":"..."}}

없으면: {{"has_schedule":false}}

규칙: 날짜·시간 불명확하면 false / 종료시간 없으면 시작+1시간 / 상대날짜 오늘 기준 계산
        """),
        HumanMessage(content=combined),
    ])

    parsed = parse_json(_extract_text(res.content).strip()) or {"has_schedule": False}

    if not parsed.get("has_schedule"):
        print("   → 일정 없음")
        return {"has_schedule": False, "schedule_info": None, "calendar_event_id": ""}

    sched = {
        "title":       parsed.get("title", state["subject"]),
        "date":        parsed.get("date", ""),
        "start_time":  parsed.get("start_time", "09:00"),
        "end_time":    parsed.get("end_time", "10:00"),
        "location":    parsed.get("location", ""),
        "description": parsed.get("description",
                       f"발신자: {state['sender_email']}\n\n{state['body'][:300]}"),
    }

    print(f"   → 📅 일정 감지: [{sched['title']}] "
          f"{sched['date']} {sched['start_time']}~{sched['end_time']}")

    # Google Calendar MCP 등록
    start_dt = f'{sched["date"]}T{sched["start_time"]}:00+09:00'
    end_dt   = f'{sched["date"]}T{sched["end_time"]}:00+09:00'
    prompt = (
        f'Google Calendar MCP의 create_event 도구를 사용해서 아래 일정을 등록해줘.\n'
        f'calendarId: {DEFAULT_CALENDAR}\n'
        f'summary: {sched["title"]}\n'
        f'start: {start_dt}\n'
        f'end: {end_dt}\n'
        f'location: {sched["location"]}\n'
        f'description: 발신자: {state["customer_name"]} <{state["sender_email"]}> / {sched["description"][:200]}\n\n'
        f'등록 완료 후 반드시 아래 JSON 형식만 출력해줘 (다른 설명 없이):\n'
        f'{{"eventId":"<생성된 이벤트 ID>"}}'
    )
    out = run_claude_cli(prompt, timeout=120, allowed_tools=[
        "mcp__claude_ai_Google_Calendar__create_event",
    ])

    print(f"   [DEBUG] 캘린더 CLI 응답:\n{out[:300]}")

    p        = parse_json(out) or {}
    event_id = p.get("eventId") or p.get("id") or p.get("event_id", "")
    if event_id:
        print(f"   → ✅ 캘린더 등록 완료 (ID: {event_id})")
    else:
        print(f"   → ⚠ 캘린더 등록 응답에 eventId 없음 — CLI 응답을 확인하세요")

    return {"has_schedule": True, "schedule_info": sched, "calendar_event_id": event_id}


# ────────────────────────────────────────────────────────
# ⑦ 이메일 발송 — Gmail MCP
# ────────────────────────────────────────────────────────

def send_email(state: EmailState) -> dict:
    mode = "드래프트 저장" if DRAFT_ONLY else "발송"
    print(f"\n┌{'─'*61}┐")
    print(f"│  ⑦ 이메일 {mode} — Gmail MCP                    │")
    print(f"└{'─'*61}┘")

    final = state.get("final_response") or state.get("draft", "")

    if DRAFT_ONLY:
        out = run_claude_cli(
            f'Gmail MCP create_draft 툴로 답장 드래프트 생성.\n\n'
            f'threadId: {state["email_id"]}\n수신자: {state["sender_email"]}\n'
            f'제목: Re: {state["subject"]}\n본문:\n{final}\n\n'
            f'JSON: {{"draftId":"..."}}'
        )
    else:
        out = run_claude_cli(
            f'Gmail MCP로 답장 발송.\n\n'
            f'threadId: {state["email_id"]}\n수신자: {state["sender_email"]}\n'
            f'제목: Re: {state["subject"]}\n본문:\n{final}\n\n'
            f'JSON: {{"messageId":"..."}}'
        )

    p        = parse_json(out) or {}
    draft_id = p.get("draftId") or p.get("messageId") or p.get("id", "")
    print(f"   → {mode} 완료" + (f" (ID: {draft_id})" if draft_id else ""))

    # CUSTOMER_PROCESSED 라벨
    run_claude_cli(
        f'Gmail MCP label_thread 툴로 threadId="{state["email_id"]}"에 '
        f'"CUSTOMER_PROCESSED" 라벨 추가. 없으면 create_label로 생성.'
    )
    print("   → CUSTOMER_PROCESSED 라벨 추가")

    return {"draft_id": draft_id, "processed": True}


# 6. 라우팅 함수
def route_by_analysis(state: EmailState) -> Literal["rag_search", "escalate_to_agent", "auto_generate"]:
    """③ conditional_edge — 분석 결과에 따른 3방향 분기"""
    r = state.get("route", "rag")
    mapping = {"rag": "rag_search", "escalate": "escalate_to_agent", "auto": "auto_generate"}
    return mapping.get(r, "rag_search")

def route_after_review(state: EmailState) -> Literal["generate_rag_response", "tools_handler"]:
    return "generate_rag_response" if state.get("needs_revision") else "tools_handler"

################################################################
# LangGraph 그래프 구현 부분
################################################################
def build_graph():
    graph = StateGraph(EmailState)

    # 노드 만들기
    graph.add_node("analyze_importance", analyze_importance)
    graph.add_node("decide_route", decide_route)
    graph.add_node("rag_search", rag_search)
    graph.add_node("generate_rag_response", generate_rag_response)
    graph.add_node("escalate_to_agent", escalate_to_agent)
    graph.add_node("auto_generate", auto_generate)
    graph.add_node("review_draft", review_draft)
    graph.add_node("tools_handler", tools_handler)
    graph.add_node("schedule_followup", schedule_followup)
    graph.add_node("send_email", send_email)

    graph.add_edge( START, "analyze_importance" )
    graph.add_edge( "analyze_importance", "decide_route" )
    # 컨디너셜 엣지
    graph.add_conditional_edges(
        "decide_route",
        route_by_analysis,
        {
            "rag_search":        "rag_search",
            "escalate_to_agent": "escalate_to_agent",
            "auto_generate":     "auto_generate",
        },
    )
    graph.add_edge("rag_search", "generate_rag_response")
    graph.add_conditional_edges(
        "generate_rag_response",
        lambda s: "review_draft",
        {"review_draft": "review_draft"},
    )
    graph.add_edge("escalate_to_agent", "tools_handler")
    graph.add_edge("auto_generate", "review_draft")
    graph.add_conditional_edges(
        "review_draft",
        route_after_review,
        {
            "generate_rag_response": "generate_rag_response",
            "tools_handler":         "tools_handler",
        },
    )
    graph.add_edge("tools_handler", "schedule_followup")
    graph.add_edge("schedule_followup", "send_email")
    graph.add_edge("send_email", END)

    agent_graph = graph.compile()

    # 그래프 구조 확인
    from IPython.display import Image, display

    try:
        with open("agent_graph.png", "wb") as f:
            f.write(agent_graph.get_graph().draw_mermaid_png())
    except Exception:
        pass

    return agent_graph



# ══════════════════════════════════════════════════════════
# 2. Claude Desktop MCP 브릿지 (claude CLI subprocess)
# ══════════════════════════════════════════════════════════

def run_claude_cli(prompt: str, timeout: int = 60, allowed_tools: list[str] | None = None) -> str:
    """Claude Desktop MCP 세션을 subprocess로 재활용합니다. API 키 불필요."""
    cmd = ["claude", "--print", "--output-format", "text"]
    if allowed_tools:
        cmd += ["--allowedTools", ",".join(allowed_tools)]
    try:
        r = subprocess.run(
            cmd,
            input=prompt.encode("utf-8"),
            capture_output=True, text=False, timeout=timeout, check=False,
            cwd="C:\\ai_exam\\014_aiagent",
        )
        stdout = r.stdout.decode("utf-8", errors="replace") if r.stdout else ""
        stderr = r.stderr.decode("utf-8", errors="replace") if r.stderr else ""
        if r.returncode != 0 and stderr:
            print(f"     ⚠ CLI 경고: {stderr[:100]}")
        return stdout.strip()
    except FileNotFoundError:
        print("❌ 'claude' 명령어 없음. npm install -g @anthropic-ai/claude-code 후 claude login")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"     ⚠ CLI 타임아웃 ({timeout}초)")
        return ""

def parse_json(text: str) -> dict | list | None:
    cleaned = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    for pat in [r"\[.*?\]", r"\{.*?\}"]:
        m = re.search(pat, cleaned, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                continue
    return None

# Gmail 이메일 수집  (그래프 외부 — fetch 단계)
def fetch_emails(max_results: int = MAX_EMAILS) -> list[EmailState]:
    """① Gmail MCP — 받은편지함 폴링"""
    print(f"\n╔{'═'*61}╗")
    print(f"║  ① Gmail MCP — 받은편지함 폴링                           ║")
    print(f"╚{'═'*61}╝")
    print(f"   쿼리: {GMAIL_SEARCH_QUERY}")

    out = run_claude_cli(
        f'Gmail MCP search_threads 툴로 "{GMAIL_SEARCH_QUERY}" 쿼리 최대 {max_results}개. '
        f'JSON 배열만 출력: [{{"threadId":"...","subject":"...","snippet":"..."}}]'
    )
    print(f"   [DEBUG] CLI 응답 원문:\n{out[:500]}\n   [/DEBUG]")
    threads = parse_json(out)
    if not isinstance(threads, list) or not threads:
        print("   → 새 이메일 없음")
        return []

    print(f"   → {len(threads)}개 발견")
    states: list[EmailState] = []

    for t in threads[:max_results]:
        tid = t.get("threadId") or t.get("id", "")
        if not tid:
            continue

        det_out = run_claude_cli(
            f'Gmail MCP get_thread 툴로 threadId="{tid}". '
            f'JSON만: {{"messageId":"...","from":"...","senderName":"...","subject":"...","body":"..."}}'
        )
        det = parse_json(det_out) or {}

        sender  = det.get("from", "unknown@unknown.com")
        name    = det.get("senderName") or sender.split("@")[0]
        subject = det.get("subject") or t.get("subject", "(제목없음)")
        body    = det.get("body") or t.get("snippet", "")

        states.append({
            "email_id": tid, "message_id": det.get("messageId", ""),
            "sender_email": sender, "customer_name": name,
            "subject": subject[:80], "body": body,
            "urgency": "", "topic": "", "sentiment": "", "route": "",
            "rag_context": "", "rag_sources": [],
            "escalation_note": "",
            "draft": "", "action": "",
            "tools_called": [], "tools_result": "",
            "has_schedule": False, "schedule_info": None, "calendar_event_id": "",
            "draft_id": "", "processed": False,
            "revision_count": 0, "needs_revision": False, "review_feedback": "",
        })
        print(f"   ✉  [{name}] {subject[:50]}")

    return states

def main():
    print("Hello from 014-aiagent!")

def run_agent(max_emails: int = MAX_EMAILS) -> list[dict]:
    print("╔" + "═"*63 + "╗")
    print("║    LangGraph + MCP 고객 이메일 자동화 Agent v5            ║")
    print("╠" + "═"*63 + "╣")
    print(f"║  Gmail  : {GMAIL_SEARCH_QUERY:<51} ║")
    print(f"║  모드   : {'드래프트 저장' if DRAFT_ONLY else '즉시 발송':<51} ║")
    print(f"║  캘린더 : {DEFAULT_CALENDAR:<51} ║")
    print("╚" + "═"*63 + "╝")

    emails = fetch_emails(max_results=max_emails)
    if not emails:
        print("\n✅ 처리할 이메일 없음")
        return []

    print(f"\n총 {len(emails)}건 처리 시작")
    app     = build_graph()
    results = []

    for i, state in enumerate(emails, 1):
        print(f"\n\n{'╔'+'═'*63+'╗'}")
        print(f"║  [{i}/{len(emails)}] {state['customer_name']} — {state['subject'][:43]:<43} ║")
        print(f"{'╚'+'═'*63+'╝'}")

        try:
            result = app.invoke(state)
            results.append(result)
            # print(results)

    #         route_label = {"rag":"④-A RAG","escalate":"④-B 상담원","auto":"④-C 자동"}.get(
    #             result.get("route",""), result.get("route",""))
    #         cal = ""
    #         if result.get("has_schedule") and result.get("schedule_info"):
    #             s   = result["schedule_info"]
    #             cal = f"\n  📅 캘린더: {s.get('title','')} {s.get('date','')} {s.get('start_time','')}"

    #         print(f"\n  ✅ 완료 | 경로: {route_label} | 수정: {result['revision_count']}회"
    #               f" | 드래프트: {result.get('draft_id','N/A')}{cal}")
        except Exception as e:
            print(f"  ❌ 실패: {e}")
            results.append({**state, "processed": False, "error": str(e)})

    #     time.sleep(0.5)

    # ok  = sum(1 for r in results if r.get("processed"))
    # cal = sum(1 for r in results if r.get("calendar_event_id"))
    # print(f"\n{'═'*65}")
    # print(f"  이메일 처리: {ok}/{len(results)}건 | 캘린더 등록: {cal}건")
    # print(f"{'═'*65}\n")
    # return results

if __name__ == "__main__":
    run_agent(3)
