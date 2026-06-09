import os
import json
import importlib.util
import datetime

from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings

# 004_langgraph_comfyui_tools.py 동적 임포트 (파일명이 숫자로 시작)
_spec = importlib.util.spec_from_file_location(
    "comfyui_tools_module",
    os.path.join(settings.BASE_DIR, "004_langgraph_comfyui_tools.py"),
)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
_generate_text2img = _module.generate_text2img
_generate_img2img  = _module.generate_img2img

METADATA_FILE = os.path.join(settings.MEDIA_ROOT, "_metadata.json")


def _load_metadata() -> dict:
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_metadata(metadata: dict):
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def ai_node_view(request):
    return render(request, "ai_node/main.html")


def api_generate(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    prompt = request.POST.get("prompt", "").strip()
    if not prompt:
        return JsonResponse({"error": "프롬프트를 입력해주세요."}, status=400)

    denoise = float(request.POST.get("denoise", "0.75"))
    reference_image = request.FILES.get("reference_image")

    try:
        if reference_image:
            # 임시 파일로 저장 후 img2img 호출
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
            temp_path = os.path.join(settings.MEDIA_ROOT, f"_tmp_{reference_image.name}")
            with open(temp_path, "wb") as f:
                for chunk in reference_image.chunks():
                    f.write(chunk)
            try:
                result_msg = _generate_img2img(prompt, temp_path, denoise)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            gen_type = "img2img"
        else:
            result_msg = _generate_text2img(prompt)
            gen_type = "text2img"

        if "이미지 생성 완료:" not in result_msg:
            return JsonResponse({"error": result_msg or "이미지 생성에 실패했습니다."}, status=500)

        paths_str = result_msg.replace("이미지 생성 완료:", "").strip()
        first_path = paths_str.split(",")[0].strip()
        filename = os.path.basename(first_path)
        image_url = f"{settings.MEDIA_URL}{filename}"

        metadata = _load_metadata()
        metadata[filename] = {
            "prompt": prompt,
            "created_at": datetime.datetime.now().strftime("%Y.%m.%d %H:%M"),
            "type": gen_type,
        }
        _save_metadata(metadata)

        return JsonResponse({"image_url": image_url, "filename": filename})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
