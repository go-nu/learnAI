from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

def index(request):
    return render(request, 'aichatbot/ai_chatbot.html')
    # return HttpResponse("안녕하세요. aichatbot 페이지 입니다.")