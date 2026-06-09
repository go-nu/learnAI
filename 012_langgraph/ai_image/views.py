import os
import json
import importlib.util
import datetime

from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings

# 003_langgraph_comfyui_node.py 동적 임포트 (파일명이 숫자로 시작)
_node_path = os.path.join(settings.BASE_DIR, '003_langgraph_comfyui_node.py')
_spec = importlib.util.spec_from_file_location("comfyui_node", _node_path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
_generate_image = _module.generate_image

IMAGE_DIR = settings.MEDIA_ROOT
METADATA_FILE = os.path.join(IMAGE_DIR, '_metadata.json')


def _load_metadata() -> dict:
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_metadata(metadata: dict):
    os.makedirs(IMAGE_DIR, exist_ok=True)
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def movie_search(request):
    return render(request, "ai_image/main.html")


def api_generate(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    try:
        data = json.loads(request.body)
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return JsonResponse({'error': '프롬프트를 입력해주세요.'}, status=400)

        # ComfyUI 이미지 생성 호출
        result = _generate_image({"messages": [prompt]})
        result_msg = (result.get("messages") or [""])[-1]

        if "이미지 생성 완료:" not in result_msg:
            return JsonResponse({'error': result_msg or '이미지 생성에 실패했습니다.'}, status=500)

        # 저장된 파일 경로에서 파일명 추출
        paths_str = result_msg.replace("이미지 생성 완료:", "").strip()
        first_path = paths_str.split(",")[0].strip()
        filename = os.path.basename(first_path)
        image_url = f"{settings.MEDIA_URL}{filename}"

        # 메타데이터 저장 (프롬프트 이력 보존)
        metadata = _load_metadata()
        metadata[filename] = {
            "prompt": prompt,
            "created_at": datetime.datetime.now().strftime("%Y.%m.%d %H:%M"),
        }
        _save_metadata(metadata)

        return JsonResponse({'image_url': image_url, 'filename': filename})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def api_images(request):
    tab = request.GET.get('tab', 'recent')

    os.makedirs(IMAGE_DIR, exist_ok=True)
    metadata = _load_metadata()

    image_files = []
    for filename in os.listdir(IMAGE_DIR):
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            continue
        if filename.startswith('_'):
            continue
        filepath = os.path.join(IMAGE_DIR, filename)
        mtime = os.path.getmtime(filepath)
        meta = metadata.get(filename, {})
        image_files.append({
            'url': f"{settings.MEDIA_URL}{filename}",
            'prompt': meta.get('prompt', filename),
            'created_at': meta.get('created_at', datetime.datetime.fromtimestamp(mtime).strftime('%Y.%m.%d %H:%M')),
            'mtime': mtime,
        })

    image_files.sort(key=lambda x: x['mtime'], reverse=True)

    if tab == 'recent':
        image_files = image_files[:8]

    for img in image_files:
        del img['mtime']

    return JsonResponse({'images': image_files})
