import csv
from re import search
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

searchList = []

search = input('검색어를 입력하세요 : ')

for i in range(1, 10):
    url = f'https://kin.naver.com/search/list.nhn?query={quote_plus(search)}&page={i}'

    response = requests.get(url)

    if response.status_code == 200:
        print( "============================ " + str(i) + " ============================" )

        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        ul = soup.select_one('ul.basic1')
        titles = ul.select('li > dl > dt > a')
        for title in titles:
            temp = []
            temp.append(title.text)
            temp.append(title.attrs['href'])
            searchList.append(temp)

            print(title.get_text())
    else : 
        print(response.status_code)

### csv 파일로 저장
# newline = '' 한줄로 내리기
f = open(f'{search}.csv', 'w', encoding='cp949', newline='')    
csvWriter = csv.writer(f)

for i in searchList:
    csvWriter.writerow(i)
f.close()
