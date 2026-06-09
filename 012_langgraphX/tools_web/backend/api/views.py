import os
from pathlib import Path

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from .models import GenerationRecord
from langgraph_service import run_text2img, run_img2img

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}


def _parse_image_paths(result_text: str) -> list[str]:
    """'이미지 생성 완료: path1, path2' 형태 문자열에서 경로 목록 추출."""
    if "이미지 생성 완료:" in result_text:
        paths_str = result_text.split("이미지 생성 완료:", 1)[1].strip()
        return [p.strip() for p in paths_str.split(",") if p.strip()]
    return []


def _path_to_url(file_path: str) -> str:
    """절대 파일 경로를 미디어 URL로 변환."""
    try:
        rel = Path(file_path).relative_to(settings.MEDIA_ROOT)
        return f"{settings.MEDIA_URL}{rel.as_posix()}"
    except ValueError:
        return f"{settings.MEDIA_URL}{Path(file_path).name}"


class Text2ImgView(APIView):
    parser_classes = [JSONParser]

    def post(self, request):
        prompt = request.data.get('prompt', '').strip()
        if not prompt:
            return Response({'error': '프롬프트를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = run_text2img(prompt)
            paths = _parse_image_paths(result)
            image_url = _path_to_url(paths[0]) if paths else None

            record = GenerationRecord.objects.create(
                mode='text2img',
                prompt=prompt,
                result_image=paths[0] if paths else '',
            )

            return Response({
                'status': 'success',
                'message': result,
                'image_url': image_url,
                'record_id': record.id,
            })

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Img2ImgView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        prompt = request.data.get('prompt', '').strip()
        image_file = request.FILES.get('image')
        denoise = float(request.data.get('denoise', 0.75))

        if not prompt:
            return Response({'error': '프롬프트를 입력해주세요.'}, status=status.HTTP_400_BAD_REQUEST)
        if not image_file:
            return Response({'error': '입력 이미지를 업로드해주세요.'}, status=status.HTTP_400_BAD_REQUEST)

        # 업로드 이미지 임시 저장
        upload_dir = settings.UPLOAD_TMP_DIR
        os.makedirs(upload_dir, exist_ok=True)
        tmp_path = os.path.join(upload_dir, image_file.name)
        with open(tmp_path, 'wb') as f:
            for chunk in image_file.chunks():
                f.write(chunk)

        try:
            result = run_img2img(prompt, tmp_path, denoise)
            paths = _parse_image_paths(result)
            image_url = _path_to_url(paths[0]) if paths else None

            record = GenerationRecord.objects.create(
                mode='img2img',
                prompt=prompt,
                denoise=denoise,
                result_image=paths[0] if paths else '',
                input_image=tmp_path,
            )

            return Response({
                'status': 'success',
                'message': result,
                'image_url': image_url,
                'record_id': record.id,
            })

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ImagesView(APIView):
    def get(self, request):
        image_dir = settings.MEDIA_ROOT
        images = []

        if os.path.exists(image_dir):
            for fname in sorted(os.listdir(image_dir), reverse=True):
                if Path(fname).suffix.lower() in IMAGE_EXTENSIONS:
                    fpath = os.path.join(image_dir, fname)
                    record = GenerationRecord.objects.filter(result_image__icontains=fname).first()
                    images.append({
                        'filename': fname,
                        'url': f"{settings.MEDIA_URL}{fname}",
                        'created_at': os.path.getmtime(fpath),
                        'prompt': record.prompt if record else '',
                        'mode': record.mode if record else 'text2img',
                    })

        return Response({'images': images})

    def delete(self, request):
        GenerationRecord.objects.all().delete()
        return Response({'message': '히스토리가 삭제되었습니다.'})
