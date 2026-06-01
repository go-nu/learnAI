"""
╔══════════════════════════════════════════════════════════════════╗
║         AI 챗봇 - 화면 설계 파일 (chatbot_ui.py)                ║
║  ※ 이 파일은 UI(화면) 설계만 완성된 파일입니다.                  ║
║  ※ [코딩 영역] 표시된 부분에 코드를 작성하세요.                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import gradio as gr

# ================================================================
# [코딩 영역 1] 라이브러리 import
# ================================================================
# TODO: Gemini API를 사용하기 위한 라이브러리를 import 하세요.
# 힌트: google.generativeai 라이브러리를 사용합니다.

# 여기에 코드를 작성하세요 ↓
import google as genai



# ================================================================
# [코딩 영역 2] 채팅 응답 함수
# ================================================================
# TODO: 사용자의 메시지를 받아 Gemini API로 응답을 생성하는 함수를 작성하세요.
#
# 매개변수 설명:
#   - message    : 사용자가 입력한 현재 메시지 (문자열)
#   - history    : 이전 대화 내역 (리스트) — Gradio 6.0 형식:
#                  [{"role": "user", "content": ...}, ...]
#                  ※ content는 문자열 또는 [{"text": "...", "type": "text"}] 리스트일 수 있음
#                  ※ Gemini 전달 시 isinstance(content, list) 여부를 확인하여 text를 추출할 것
#   - system_prompt : 챗봇의 역할/성격 설정 (문자열)
#   - api_key    : Gemini API 키 (문자열)
#
# 반환값: 업데이트된 대화 내역 리스트
#         예) history + [{"role": "user", "content": message}, {"role": "assistant", "content": bot_reply}]

def chat_response(message, history, system_prompt, api_key):
    """
    Gemini API를 호출하여 채팅 응답을 생성합니다.

    Args:
        message (str)      : 사용자가 입력한 현재 메시지
        history (list)     : 이전 대화 내역 [[user, bot], ...]
        system_prompt (str): 챗봇의 역할/성격 설정 텍스트
        api_key (str)      : Gemini API 키

    Returns:
        list: 업데이트된 전체 대화 내역
    """

    # ── 입력값 검증 ──────────────────────────────────────────
    if not api_key.strip():
        history = history + [
            {"role": "user",      "content": message},
            {"role": "assistant", "content": "⚠️ API 키를 입력해 주세요."},
        ]
        return history

    if not message.strip():
        return history

    if not system_prompt.strip():
        system_prompt = "당신은 친절하고 유능한 AI 어시스턴트입니다."

    # ── Gemini API 설정 ──────────────────────────────────────
    genai.configure(api_key=api_key.strip())

    # 모델 생성 (시스템 프롬프트 포함)
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",       # 사용할 모델 이름
        system_instruction=system_prompt,    # 시스템 프롬프트 설정
    )

    # ── 이전 대화 내역 → Gemini 형식으로 변환 ────────────────
    # Gradio 6.0: content가 문자열 또는 [{"text": "...", "type": "text"}] 리스트로 올 수 있음
    gemini_history = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        content = msg["content"]
        if isinstance(content, list):
            text = " ".join(
                item.get("text", "")
                for item in content
                if isinstance(item, dict) and item.get("type") == "text"
            )
        else:
            text = str(content)
        if text.strip():
            gemini_history.append({"role": role, "parts": [text]})

    # ── 채팅 세션 생성 및 메시지 전송 ───────────────────────
    try:
        chat_session = model.start_chat(history=gemini_history)
        response     = chat_session.send_message(message)
        bot_reply    = response.text

    except Exception as e:
        bot_reply = f"❌ 오류가 발생했습니다: {str(e)}"

    # ── 대화 내역에 추가 후 반환 ─────────────────────────────
    history = history + [
        {"role": "user",      "content": message},
        {"role": "assistant", "content": bot_reply},
    ]
    return history


# ================================================================
# [코딩 영역 3] 대화 초기화 함수
# ================================================================
# TODO: 채팅 기록을 초기화하는 함수를 작성하세요.
#
# 반환값: 빈 리스트 []

def clear_chat():
    """
    채팅 기록을 초기화합니다.

    Returns:
        list: 빈 리스트 []
    """
    return []


# ================================================================
# [코딩 영역 4] 시스템 프롬프트 예시 함수
# ================================================================
# TODO: 버튼 클릭 시 시스템 프롬프트 입력창에 예시 텍스트를 넣어주는 함수를 작성하세요.
#
# 매개변수:
#   - example_type : 예시 종류 ("보험", "CS", "교육", "요리")
#
# 반환값: 해당 예시 프롬프트 문자열

def load_example_prompt(example_type):
    """
    예시 시스템 프롬프트를 반환합니다.
    """
    # 예시 프롬프트 딕셔너리 (참고용 - 학생이 내용 수정 가능)
    examples = {
        "보험": "당신은 친절한 보험 상담사입니다. 고객의 보험 관련 질문에 쉽고 친절하게 답변해 주세요. 복잡한 보험 용어는 쉬운 말로 설명하고, 고객의 상황에 맞는 보험 상품을 추천해 주세요.",
        "CS":   "당신은 전문 고객 서비스 담당자입니다. 고객의 불만이나 문의를 공감하며 듣고, 문제를 신속하게 해결할 수 있도록 도와주세요. 항상 정중하고 전문적인 태도를 유지하세요.",
        "교육": "당신은 친절한 학습 도우미 선생님입니다. 학생들이 이해하기 쉽도록 개념을 설명하고, 예시를 들어 설명해 주세요. 학생이 틀려도 격려하며 올바른 방향으로 안내해 주세요.",
        "요리": "당신은 전문 요리사입니다. 사용자가 원하는 요리의 레시피와 조리법을 단계별로 친절하게 알려주세요. 재료 대체 방법이나 요리 팁도 함께 제공해 주세요.",
    }

    # 여기에 코드를 작성하세요 ↓




    pass  # 코드 작성 후 이 줄을 삭제하세요


# ================================================================
# Gradio UI 화면 설계 (수정하지 마세요)
# ================================================================

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&family=Space+Grotesk:wght@400;600&display=swap');

body, .gradio-container {
    font-family: 'Noto Sans KR', sans-serif !important;
    background-color: #f0f4f8 !important;
}

.main-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border-radius: 16px;
    padding: 28px 36px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}

.main-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(83, 166, 255, 0.15) 0%, transparent 70%);
    border-radius: 50%;
}

.main-header h1 {
    font-family: 'Space Grotesk', sans-serif !important;
    color: #ffffff !important;
    font-size: 26px !important;
    font-weight: 600 !important;
    margin: 0 !important;
    letter-spacing: -0.5px;
}

.main-header p {
    color: #8ba3c7 !important;
    font-size: 14px !important;
    margin: 6px 0 0 0 !important;
}

.left-panel {
    background: #ffffff !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06) !important;
    border: 1px solid #e8edf2 !important;
    overflow: hidden !important;
}

.right-panel {
    background: #ffffff !important;
    border-radius: 14px !important;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06) !important;
    border: 1px solid #e8edf2 !important;
    overflow: hidden !important;
    padding: 0 !important;
    gap: 0 !important;
}

.section-label {
    font-size: 12px !important;
    font-weight: 700 !important;
    color: #5a7a9f !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    margin-bottom: 8px !important;
}

.example-btn {
    font-size: 12px !important;
    padding: 6px 12px !important;
    border-radius: 20px !important;
    border: 1.5px solid #d1e0f0 !important;
    background: #f7fafd !important;
    color: #3a6ea5 !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
}

.example-btn:hover {
    background: #e3eef9 !important;
    border-color: #3a6ea5 !important;
}

.chatbot-area .message {
    border-radius: 12px !important;
}

.send-btn {
    background: linear-gradient(135deg, #0f3460, #16213e) !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    min-width: 80px !important;
}

.clear-btn {
    border-radius: 10px !important;
    font-size: 13px !important;
}

.status-bar {
    background: #eef4fb;
    border: 1px solid #d1e0f0;
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 12px;
    color: #5a7a9f;
    margin-top: 8px;
}

.api-key-input input {
    font-family: 'Courier New', monospace !important;
    font-size: 13px !important;
    letter-spacing: 1px;
}

footer { display: none !important; }
.input-row { padding: 12px 16px 16px !important; }
"""

with gr.Blocks(title="AI 챗봇 실습") as demo:

    gr.HTML("""
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <script>
    (function() {
        function showLoading() {
            Swal.fire({
                title: 'AI 대화 생성중입니다...',
                allowOutsideClick: false,
                showConfirmButton: false,
                didOpen: () => Swal.showLoading()
            });
        }
        function init() {
            const sendBtn   = document.querySelector('.send-btn button');
            const inputArea = document.querySelector('.input-row textarea, .input-row input');
            const chatArea  = document.querySelector('.chatbot-area');
            if (!sendBtn || !chatArea) { setTimeout(init, 500); return; }
            sendBtn.addEventListener('click', showLoading);
            if (inputArea) {
                inputArea.addEventListener('keydown', e => {
                    if (e.key === 'Enter' && !e.shiftKey) showLoading();
                });
            }
            new MutationObserver(() => {
                setTimeout(() => { if (Swal.isVisible()) Swal.close(); }, 200);
            }).observe(chatArea, { childList: true, subtree: true });
        }
        setTimeout(init, 1000);
    })();
    </script>
    """)

    gr.HTML("""
    <div class="main-header">
        <h1>🤖 AI 챗봇 실습 플랫폼</h1>
        <p>Gemini API · Gradio · Python — 시스템 프롬프트 기반 챗봇 구현 실습</p>
    </div>
    """)

    with gr.Row(equal_height=True):

        with gr.Column(scale=1, min_width=300, elem_classes=["left-panel"]):

            gr.HTML('<p class="section-label">🔑 API 설정</p>')
            api_key_input = gr.Textbox(
                label="Gemini API Key",
                placeholder="여기에 API 키를 입력하세요...",
                type="password",
                elem_classes=["api-key-input"],
                info="Google AI Studio에서 발급받은 API 키를 입력하세요."
            )

            gr.HTML('<hr style="border:none;border-top:1px solid #e8edf2;margin:16px 0;">')
            gr.HTML('<p class="section-label">⚙️ 시스템 프롬프트</p>')

            system_prompt_input = gr.Textbox(
                label="챗봇 역할 설정",
                placeholder="챗봇의 역할과 행동 방식을 여기에 입력하세요.\n\n예) 당신은 친절한 보험 상담사입니다...",
                lines=7,
                max_lines=12,
                info="채팅 시작 전에 챗봇의 성격과 역할을 설정합니다."
            )

            gr.HTML('<p class="section-label" style="margin-top:12px;">📌 예시 프롬프트</p>')
            with gr.Row():
                btn_insurance = gr.Button("🏦 보험상담", elem_classes=["example-btn"], size="sm")
                btn_cs        = gr.Button("🎧 CS상담",  elem_classes=["example-btn"], size="sm")
            with gr.Row():
                btn_edu  = gr.Button("📚 교육도우미", elem_classes=["example-btn"], size="sm")
                btn_cook = gr.Button("🍳 요리사",    elem_classes=["example-btn"], size="sm")

            gr.HTML('<hr style="border:none;border-top:1px solid #e8edf2;margin:16px 0;">')
            clear_btn = gr.Button("🗑️ 대화 초기화", variant="secondary",
                                  elem_classes=["clear-btn"], size="sm")

            gr.HTML("""
            <div class="status-bar">
                💡 <strong>사용 방법:</strong><br>
                1. API 키 입력<br>
                2. 시스템 프롬프트 설정 (또는 예시 선택)<br>
                3. 오른쪽 채팅창에서 대화 시작
            </div>
            """)

        with gr.Column(scale=2, elem_classes=["right-panel"]):

            chatbot = gr.Chatbot(
                label="채팅창",
                height=480,
                elem_classes=["chatbot-area"],
                show_label=False,
                placeholder="💬 시스템 프롬프트를 설정하고 대화를 시작해보세요!",
            )

            with gr.Row(elem_classes=["input-row"]):
                msg_input = gr.Textbox(
                    placeholder="메시지를 입력하세요... (Enter로 전송)",
                    show_label=False,
                    container=False,
                    scale=5,
                    autofocus=True,
                )
                send_btn = gr.Button("전송 ▶", variant="primary",
                                     elem_classes=["send-btn"], scale=1)

    # ── 이벤트 연결 (수정하지 마세요) ──────────────────────────
    msg_input.submit(
        fn=chat_response,
        inputs=[msg_input, chatbot, system_prompt_input, api_key_input],
        outputs=[chatbot],
    ).then(fn=lambda: "", outputs=[msg_input])

    send_btn.click(
        fn=chat_response,
        inputs=[msg_input, chatbot, system_prompt_input, api_key_input],
        outputs=[chatbot],
    ).then(fn=lambda: "", outputs=[msg_input])

    clear_btn.click(fn=clear_chat, outputs=[chatbot])

    btn_insurance.click(fn=lambda: load_example_prompt("보험"), outputs=[system_prompt_input])
    btn_cs.click(       fn=lambda: load_example_prompt("CS"),   outputs=[system_prompt_input])
    btn_edu.click(      fn=lambda: load_example_prompt("교육"), outputs=[system_prompt_input])
    btn_cook.click(     fn=lambda: load_example_prompt("요리"), outputs=[system_prompt_input])


# ── 실행 ──────────────────────────────────────────────────────
if __name__ == "__main__":
    demo.launch(
        share=False,
        server_port=7860,
        css=CUSTOM_CSS,
        theme=gr.themes.Soft(),
    )
