import easyocr

# 한국어('ko')와 영어('en')를 인식하도록 Reader 객체 생성
reader = easyocr.Reader(['ko', 'en'])

# 이미지 파일 경로 설정 후 텍스트 읽기 수행
result = reader.readtext('test2.png')

# 결과 출력 (글자 위치 좌표, 인식된 텍스트, 정확도 반환)
for (bbox, text, prob) in result:
    print(f'Text: {text} (Confidence: {prob:.4f})')