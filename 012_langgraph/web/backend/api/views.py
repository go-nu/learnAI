import os
from pathlib import Path
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import ChatMessage
from langgraph_service import run_graph

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}


class GenerateView(APIView):
    def post(self, request):
        prompt = request.data.get('prompt', '').strip()
        if not prompt:
            return Response({'error': '프롬프트를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

        ChatMessage.objects.create(role='user', content=prompt, message_type='text')

        try:
            result = run_graph(prompt)
            all_messages = result.get('messages', [])
            # messages accumulate; AI response is everything after the initial prompt
            ai_messages = all_messages[1:]
            last_response = ai_messages[-1] if ai_messages else '응답이 없습니다. (질문이 너무 짧습니다)'

            is_image = '이미지 생성 완료' in last_response
            msg_type = 'image' if is_image else 'text'

            ChatMessage.objects.create(role='assistant', content=last_response, message_type=msg_type)

            return Response({'response': last_response, 'type': msg_type})

        except Exception as e:
            error_msg = str(e)
            ChatMessage.objects.create(role='assistant', content=f'오류: {error_msg}', message_type='text')
            return Response({'error': error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HistoryView(APIView):
    def get(self, request):
        messages = ChatMessage.objects.all()
        data = [
            {
                'id': m.id,
                'role': m.role,
                'content': m.content,
                'type': m.message_type,
                'created_at': m.created_at.isoformat(),
            }
            for m in messages
        ]
        return Response({'messages': data})

    def delete(self, request):
        ChatMessage.objects.all().delete()
        return Response({'message': '대화 기록이 삭제되었습니다.'})


class ImagesView(APIView):
    def get(self, request):
        image_dir = settings.MEDIA_ROOT
        images = []

        if os.path.exists(image_dir):
            for fname in sorted(os.listdir(image_dir), reverse=True):
                if Path(fname).suffix.lower() in IMAGE_EXTENSIONS:
                    fpath = os.path.join(image_dir, fname)
                    images.append({
                        'filename': fname,
                        'url': f"{settings.MEDIA_URL}{fname}",
                        'created_at': os.path.getmtime(fpath),
                    })

        return Response({'images': images})
