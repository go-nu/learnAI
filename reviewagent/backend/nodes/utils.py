def get_text(response) -> str:
    """LangChain response.content가 str 또는 list 어느 쪽이든 텍스트를 반환합니다."""
    content = response.content
    if isinstance(content, list):
        return "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    return str(content)
