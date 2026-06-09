import importlib.util
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent.parent  # 012_langgraph/
load_dotenv(ROOT_DIR / '.env')

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

# 004_langgraph_tools_comfyui.py 에서 TOOLS 로드 (파일명 숫자 시작 → importlib)
_spec = importlib.util.spec_from_file_location(
    "tools_comfyui",
    str(ROOT_DIR / "004_langgraph_tools_comfyui.py"),
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

TOOLS = _mod.TOOLS

llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")
agent = create_react_agent(llm, TOOLS)


def _extract_tool_result(messages: list) -> str:
    """agent 응답 메시지 목록에서 최종 AI 응답 or tool result 텍스트 추출."""
    for msg in reversed(messages):
        content = getattr(msg, "content", "")
        if content and not getattr(msg, "tool_calls", None):
            return content if isinstance(content, str) else str(content)
    return "응답을 받지 못했습니다."


def run_text2img(prompt: str) -> str:
    """텍스트 프롬프트로 이미지 생성 후 저장 경로 반환."""
    instruction = (
        f"generate_image 도구를 사용하여 이미지를 생성해주세요. "
        f"프롬프트: {prompt}"
    )
    result = agent.invoke({"messages": [HumanMessage(content=instruction)]})
    return _extract_tool_result(result["messages"])


def run_img2img(prompt: str, image_path: str, denoise: float = 0.75) -> str:
    """입력 이미지를 기반으로 img2img 이미지 생성 후 저장 경로 반환."""
    instruction = (
        f"generate_image_from_image 도구를 사용하여 이미지를 변환해주세요. "
        f"prompt='{prompt}', image_path='{image_path}', denoise={denoise}"
    )
    result = agent.invoke({"messages": [HumanMessage(content=instruction)]})
    return _extract_tool_result(result["messages"])
