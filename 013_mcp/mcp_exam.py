from fastmcp import FastMCP

# 객체 생성
mcp = FastMCP("Demo 🚀")

# 도구 추가, 실제 로직이 들어가는 부분
@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers""" # 지시문, 지우면 안되고 영어로 작성
    return a + b

# mcp를 클로드가 실행하기에 호출을 반드시 해야함.
if __name__ == "__main__":
    mcp.run()