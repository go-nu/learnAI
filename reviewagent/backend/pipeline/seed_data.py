import os
import sys
import django

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import urllib.request
import random
from faker import Faker
from reviews.models import User, Product, Review

fake = Faker("ko_KR")

URL = "https://raw.githubusercontent.com/bab2min/corpus/master/sentiment/naver_shopping.txt"
SEED_COUNT = 300
FAKE_USER_COUNT = 30

# 텍스트에서 리스트로 변환
def load_reviews_from_url():
    with urllib.request.urlopen(URL) as f:
        lines = f.read().decode("utf-8").splitlines()

    reviews = []

    for line in lines:
        parts   = line.split("\t")
        rating  = int(parts[0])
        text    = parts[1]
        reviews.append((rating, text))
    
    return reviews


# 더미 사용자 생성
def create_fake_users():
    users = []

    for _ in range(FAKE_USER_COUNT):

        name        = fake.name()
        email       = fake.unique.email()
        google_id   = fake.unique.uuid4()

        user, created = User.objects.get_or_create(
            email = email,
            defaults = {
                "name": name,
                "google_id": google_id,
            }
        )

        users.append(user)

    return users


# 샘플 상품 생성 및 조회
def get_or_create_product():
    product, craeted = Product.objects.get_or_create(
        name = "샘플 상품",
        defaults = {
            "category": "주방/생활용품",
            "description": "샘플 데이터"
        }
    )
    
    return product


# 시드 생성
def seed():
    reviews = load_reviews_from_url()
    users   = create_fake_users()
    product = get_or_create_product()

    random.shuffle(reviews)
    reviews = reviews[:SEED_COUNT]

    Review.objects.bulk_create([
        Review(
            user    = random.choice(users),
            product = product,
            rating  = rating,
            text    = text,
        )
        for rating, text in reviews
    ], batch_size=100)

    print("review 샘플 생성 완료")


if __name__ == "__main__":
    seed()
