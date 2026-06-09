from dotenv import load_dotenv
load_dotenv()

# 그래프상태 정의하기
from typing_extensions import TypedDict

# state 선언에 사용하는 함수
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
#     'email': 'test@gmail.com'
# }
# print(user1)

# 문법 오류 확인
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str

user2 = {
    'id': 1,
    'name': '23',
    'email': 'test@naver.com'
}

user1 = User(**user2) # 클래스 지정 타입을 벗어나면 오류
print(user1)
print(user2)