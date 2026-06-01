from django.shortcuts import render, redirect

# Create your views here.
from django.http import HttpResponse
from . models import Movie
from . translate import translate_en_to_ko

import requests
import json

# api_key
apiKey = ""

def movie_search(request):
    sendData = {
        "searchKeyword" : "abc",
    }
    return render(request, "webcrawl/movie_search.html", sendData)

def movie_all_search(request):
    print("func movie_all_search")

    # AI 프로그램, 데이터베이스 처리되는 루틴
    url = f"http://www.omdbapi.com/?s=movie&y=2026&apikey={apiKey}&page=1"
    response = requests.get(url)
        
    # 딕셔너리 변경 response.text
    data = json.loads(response.text)
    sendData = {
        "searchKeyword" : "",
        "qryData" : data,
    }

    # movie_search로 이동
    return render(request, "webcrawl/movie_search.html", sendData)

    # return HttpResponse("func movie_all_search")

########################################
# 영화 데이터 검색 함수
# 파라미터 : 
########################################
def movie_qry_search(request):
    print("func movie_qry_search")
    qry = request.GET.get("qry", "")
    print("qry = ", qry)

    # AI 프로그램, 데이터베이스 처리되는 루틴
    # url = f"http://www.omdbapi.com/?s=movie&y=2026&apikey={apiKey}&page=1"
    url = f"http://www.omdbapi.com/?apikey={apiKey}&s={qry}"
    response = requests.get(url)

    # 딕셔너리 변경 response.text
    data = json.loads(response.text)
    print(data)

    sendData = {
        "searchKeyword" : qry,
        "qryData" : data,
    }

    # movie_search로 이동
    return render(request, "webcrawl/movie_search.html", sendData)
    # return HttpResponse("func movie_qry_search")


def movie_save(request, imdbId):
    print("movie_save")
    print("imdbId =", imdbId)

    # API에서 상세정보 가져오기.
    url = f"http://www.omdbapi.com/?apikey={apiKey}&i={imdbId}"
    response = requests.get(url)

    # 딕셔너리 변경 response.text
    data = json.loads(response.text)
    print(data)

    # 데이터베이스에서 저장
    saveData = Movie()

    saveData.title      = data['Title']
    # 한국어 번역
    saveData.ko_tilte   = translate_en_to_ko(data['Title'])
    saveData.year       = data['Year']
    saveData.rated      = data['Rated']
    saveData.released   = data['Released']
    saveData.runtime    = data['Runtime']
    saveData.genre      = data['Genre']
    saveData.director   = data['Director']
    saveData.writer     = data['Writer']
    saveData.actors     = data['Actors']
    saveData.plot       = data['Plot']
    saveData.language   = data['Language']
    saveData.country    = data['Country']
    saveData.awards     = data['Awards']
    saveData.poster     = data['Poster']

    # Ratings
    saveData.ratings1_source     = data['Ratings'][0]['Source']
    saveData.ratings1_value      = data['Ratings'][0]['Value']
    try : 
        saveData.ratings2_source     = data['Ratings'][1]['Source']
        saveData.ratings2_value      = data['Ratings'][1]['Value']
    except : 
        saveData.ratings2_source     = ''
        saveData.ratings2_value      = ''
    
    # Score fields
    saveData.metascore      = data['Metascore']
    saveData.imdb_rating    = data['imdbRating']
    saveData.imdb_votes     = data['imdbVotes']
    saveData.imdb_id        = data['imdbID']

    # Metadata
    saveData.type       = data['Type']
    saveData.dvd        = data['DVD']
    saveData.box_office = data['BoxOffice']
    saveData.production = data['Production']
    saveData.website    = data['Website']
    saveData.response   = data['Response']

    # 저장
    try :
        saveData.save()
    except : 
        return HttpResponse("중복된 데이터입니다.")

    return redirect('/webcrawl/')