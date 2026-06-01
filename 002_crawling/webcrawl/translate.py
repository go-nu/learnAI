import urllib.request
import urllib.parse
import json


def translate_en_to_ko(text: str) -> str:
    """
    영어 텍스트를 한글로 번역합니다.
    - API 키 불필요
    - 외부 라이브러리 불필요 (표준 라이브러리만 사용)
    - Python 3.11 이상 호환

    Args:
        text (str): 번역할 영어 텍스트

    Returns:
        str: 번역된 한글 텍스트

    Raises:
        ValueError: 입력 텍스트가 비어있을 경우
        RuntimeError: 번역 요청 실패 시
    """
    if not text or not text.strip():
        raise ValueError("번역할 텍스트를 입력해주세요.")

    url = "https://translate.googleapis.com/translate_a/single"
    params = urllib.parse.urlencode({
        "client": "gtx",
        "sl":     "en",
        "tl":     "ko",
        "dt":     "t",
        "q":      text
    })

    req = urllib.request.Request(
        f"{url}?{params}",
        headers={"User-Agent": "Mozilla/5.0"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            return "".join(item[0] for item in data[0] if item[0])
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"번역 요청 실패 (HTTP {e.code}): {e.reason}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"네트워크 오류: {e.reason}") from e

