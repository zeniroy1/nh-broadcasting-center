import sys
import os
import math
import datetime
import time
from PIL import Image, ImageFile

# 대용량 이미지 처리 무결성 설정
ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None  # DecompressionBombError 방지 (초고해상도 이미지 허용)

# ─────────────────────────────────────────
#  대회의실 전자현수막 목표 사이즈
#  aa.txt 참고: 2048 x 192 픽셀
# ─────────────────────────────────────────
TARGET_W   = 2048
TARGET_H   = 192
TARGET_DPI = 300            # 저장 DPI
RATIO_TOL  = 0.05           # 비율 오차 허용치 (5% 이내는 Crop, 초과시 Stretch)

SUPPORT_EXT = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp'}


def show_msg(title: str, text: str, icon: int = 0x40):
    """Windows MessageBox (ctypes). icon: 0x40=정보, 0x30=경고, 0x10=오류"""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, text, title, icon)
    except Exception:
        print(f"[{title}] {text}")


def load_image(img_path: str) -> Image.Image | None:
    """재시도 로직이 포함된 이미지 로드. 실패 시 None 반환."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with Image.open(img_path) as opened:
                return opened.copy()           # 파일 락 즉시 해제
        except PermissionError:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                show_msg(
                    "파일 접근 불가",
                    f"파일이 다른 프로그램에서 열려 있거나 저장 중입니다.\n"
                    f"해당 프로그램을 닫고 다시 시도해주세요.\n\n대상: {img_path}",
                    0x30
                )
                return None
        except Exception as e:
            show_msg("읽기 오류", f"이미지를 열 수 없습니다.\n\n{img_path}\n\n{e}", 0x10)
            return None
    return None


def to_rgb(img: Image.Image) -> Image.Image:
    """투명도/팔레트 모드를 흰색 배경 RGB로 변환."""
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        bg = Image.new('RGB', img.size, (255, 255, 255))
        bg.paste(img, mask=img.convert('RGBA').split()[3])
        return bg
    if img.mode != 'RGB':
        return img.convert('RGB')
    return img


def resize_image(img: Image.Image) -> Image.Image:
    """
    비율 오차가 RATIO_TOL 이내 → 중앙 Crop
    비율 오차 초과         → Stretch (강제 맞춤)
    """
    in_w, in_h   = img.size
    in_ratio      = in_w / in_h
    target_ratio  = TARGET_W / TARGET_H
    diff          = abs(in_ratio - target_ratio) / target_ratio

    if diff <= RATIO_TOL:
        # ── Crop 방식 ──────────────────────────────
        scale  = max(TARGET_W / in_w, TARGET_H / in_h)
        new_w  = math.ceil(in_w * scale)
        new_h  = math.ceil(in_h * scale)
        resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        left   = (new_w - TARGET_W) / 2
        top    = (new_h - TARGET_H) / 2
        result = resized.crop((left, top, left + TARGET_W, top + TARGET_H))
    else:
        # ── Stretch 방식 ───────────────────────────
        result = img.resize((TARGET_W, TARGET_H), Image.Resampling.LANCZOS)

    # 최종 크기 보장 (소수점 오차 1~2px 대비)
    if result.size != (TARGET_W, TARGET_H):
        result = result.resize((TARGET_W, TARGET_H), Image.Resampling.LANCZOS)

    return result


def process_image(img_path: str) -> bool:
    """단일 이미지 파일 변환. 성공 시 True 반환."""
    _, ext = os.path.splitext(img_path)
    if ext.lower() not in SUPPORT_EXT:
        return False                           # 지원 확장자 아님 → 조용히 넘김

    base_dir   = os.path.dirname(os.path.abspath(img_path))
    name       = os.path.splitext(os.path.basename(img_path))[0]
    out_dir    = os.path.join(base_dir, '_output')
    os.makedirs(out_dir, exist_ok=True)

    # 1. 로드
    img = load_image(img_path)
    if img is None:
        return False

    # 2. RGB 변환
    img = to_rgb(img)

    # 3. 리사이즈
    result = resize_image(img)

    # 4. 저장 (PNG 무손실 + DPI 메타데이터)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name  = f"{name}_{timestamp}_2048x192.png"
    out_path  = os.path.join(out_dir, out_name)

    try:
        result.save(
            out_path,
            format='PNG',
            dpi=(TARGET_DPI, TARGET_DPI)       # 300 DPI 메타데이터
        )
        return True
    except Exception as e:
        show_msg("저장 오류", f"파일 저장에 실패했습니다.\n\n{out_path}\n\n{e}", 0x10)
        return False


def main():
    args = sys.argv[1:]

    # 파일/폴더를 드롭하지 않고 실행했을 때 안내
    if not args:
        show_msg(
            "신관 배너 사이즈 변환기",
            "변환할 이미지 파일 또는 폴더를\n"
            "이 프로그램 아이콘 위로 드래그 앤 드롭 하세요.\n\n"
            f"목표 사이즈 : {TARGET_W} × {TARGET_H} 픽셀  /  {TARGET_DPI} DPI\n"
            "결과물 위치 : 원본 파일과 같은 폴더의 _output 폴더",
            0x40
        )
        return

    # 경로(파일/폴더) 순회 처리
    ok_count  = 0
    err_paths = []

    for path in args:
        if os.path.isfile(path):
            if process_image(path):
                ok_count += 1
            else:
                _, ext = os.path.splitext(path)
                if ext.lower() in SUPPORT_EXT:
                    err_paths.append(path)

        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for f in files:
                    fp = os.path.join(root, f)
                    if process_image(fp):
                        ok_count += 1
                    else:
                        _, ext = os.path.splitext(fp)
                        if ext.lower() in SUPPORT_EXT:
                            err_paths.append(fp)

    # 완료 메시지
    msg = f"변환 완료 : {ok_count}개 파일\n결과물은 _output 폴더에 저장되었습니다."
    if err_paths:
        msg += f"\n\n처리 실패 : {len(err_paths)}개\n" + "\n".join(err_paths[:5])
        if len(err_paths) > 5:
            msg += f"\n  ... 외 {len(err_paths)-5}개"
    icon = 0x40 if not err_paths else 0x30
    show_msg("신관 배너 변환 완료", msg, icon)


if __name__ == '__main__':
    main()
