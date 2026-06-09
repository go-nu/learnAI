from dotenv import load_dotenv

load_dotenv()

# 그래프상태 정의하기
from typing_extensions import TypedDict


# 스테이트를 선언할때 사용하는 함수 선언.
class State(TypedDict):
    messages: list[str]


from typing import TypedDict


class User(TypedDict):
    id: int
    name: str
    email: str


# user1: User = {
#     'id': 1,
#     'name': 234,
#     'email': 'test@naver.com'
# }
# print(user1)

# 문법 오류 확인
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str
    email: str


user2 = {"id": 1, "name": "홍길동", "email": "test@naver.com"}

user1 = User(**user2)
print(user1)
