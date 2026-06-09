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


# .env 속성 정보를 가져오는 함수
from dotenv import load_dotenv
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# 언어모델 설정
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")

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
            주제: [환불요청|배송문의|기술지원|계정문의|단순문의|FAQ|배송조회|복잡민원|일반문의] 중 하나
            감정: [긍정|부정|중립] 중 하나

            분류 기준:
            - 높음: 환불·결제오류·장애·강한 불만
            - 보통: 일반 문의·배송 확인·기술 지원
            - 낮음: FAQ·단순 조회·칭찬
            - 복잡민원: 법적 위협·반복 불만·다수 이슈 복합
        """),
        HumanMessage(content=f"제목: {state['subject']}\n\n{state['body']}"),
    ])

    content = res.content
    if isinstance(content, list):
        content = " ".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )

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
    # 일반문의: RAG 검색
    else:
        route = "rag"

    label = {"rag": "일반문의 → ④-A RAG 검색",
             "escalate": "복잡예외 → ④-B 상담원 연결",
             "auto": "단순처리 → ④-C 자동 생성"}[route]
    print(f"   → {label}")
    return {"route": route}

# A RAG 검색 — 사내 문서 벡터 검색
def rag_search(state: EmailState) -> dict:
    print("rag_search 모듈")
    return

# A 합류점 — RAG 결과 기반 응답 초안 생성
def generate_rag_response(state: EmailState) -> dict:
    print("generate_rag_response")
    return

# B 예외 처리 — 상담원 연결 라우팅
def escalate_to_agent(state: EmailState) -> dict:
    print("escalate_to_agent")
    return

# C 자동 생성 — 답변 초안 Agent (단순 처리)
def auto_generate(state: EmailState) -> dict:
    print("auto_generate")
    return

# 품질 검토 루프 (④-A / ④-C 공통)
def review_draft(state: EmailState) -> dict:
    print("review_draft")
    return

# 이관 & Tools 처리 — 복잡 이슈 → 외부 Tools 호출
def tools_handler(state: EmailState) -> dict:
    print("tools_handler")
    return

# 후속 일정 예약 — 캘린더 MCP
def schedule_followup(state: EmailState) -> dict:
    print("schedule_followup")
    return

# 이메일 발송 — Gmail MCP
def send_email(state: EmailState) -> dict:
    print("send_email")
    return

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

def run_claude_cli(prompt: str, timeout: int = 60) -> str:
    """Claude Desktop MCP 세션을 subprocess로 재활용합니다. API 키 불필요."""
    try:
        r = subprocess.run(
            ["claude", "--print", "--output-format", "text"],
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
            print(results)

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
    run_agent(5)
