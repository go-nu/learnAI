from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rag_bge_m3_class import RagBgeM3
from .models import Conversation, Message

# Create your views here.
rag = RagBgeM3()
llm = rag.get_llm()
retriever = rag.build_rag_components()


def index(request):
    return render(request, 'chatbot/main.html')


@csrf_exempt
def chat(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)

    human_message = request.POST.get('message', '').strip()
    if not human_message:
        return JsonResponse({'error': '질문이 비어 있습니다.'}, status=400)

    # 세션 키 확보
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    # Conversation 가져오기 or 새로 생성
    conversation_id = request.POST.get('conversation_id')
    if conversation_id:
        try:
            conversation = Conversation.objects.get(id=conversation_id, session_key=session_key)
        except Conversation.DoesNotExist:
            conversation = Conversation.objects.create(
                session_key=session_key,
                title=human_message[:50],
            )
    else:
        conversation = Conversation.objects.create(
            session_key=session_key,
            title=human_message[:50],
        )

    # 사용자 메시지 저장
    user_msg = Message.objects.create(conversation=conversation, role='user', content=human_message)

    # 이전 대화 이력 구성 (방금 저장한 메시지 제외, 최근 10개)
    history = list(conversation.messages.exclude(id=user_msg.id).order_by('created_at'))[-10:]
    if history:
        history_text = "\n".join(
            f"{'사용자' if m.role == 'user' else 'AI'}: {m.content}"
            for m in history
        )
        full_message = f"[이전 대화]\n{history_text}\n\n현재 질문: {human_message}"
    else:
        full_message = human_message

    # RAG 답변 생성
    response = rag.runnable_lambda(retriever, llm, full_message)

    # AI 응답 저장
    Message.objects.create(conversation=conversation, role='assistant', content=response)

    return JsonResponse({'response': response, 'conversation_id': conversation.id})
