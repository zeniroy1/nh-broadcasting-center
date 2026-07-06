import sys
import os
import datetime
import math
import numpy as np
from PIL import Image, ImageFile

# 대용량 이미지 처리 시 디코딩 실패/잘림 오류 무시
ImageFile.LOAD_TRUNCATED_IMAGES = True

# 89376x5376 같은 초고해상도 이미지(DecompressionBombError 방지)를 처리하기 위해 픽셀 제한 해제
Image.MAX_IMAGE_PIXELS = None

# TARGET_W/H: JSX 원본값 기반 + 전광판 소프트웨어 OverScan 1px 보정
# (JPEG subsampling=0 + 우측 끝 클램프로 JPEG 번짐 문제는 이미 해결됨)
TARGET_W = 2146
TARGET_H = 130
RATIO_TOL = 0.02

def log_message(logfile, msg):
    # 로그파일 생성을 원하지 않으므로 아무 동작도 하지 않음
    pass

def process_image(img_path):
    # 기본 경로 파악
    base_dir = os.path.dirname(os.path.abspath(img_path))
    filename = os.path.basename(img_path)
    name, ext = os.path.splitext(filename)
    
    # 이미지 파일이 아닌 경우 통과 (확장자 필터링)
    if ext.lower() not in ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp']:
        return
        
    out_dir = os.path.join(base_dir, '_output')
    os.makedirs(out_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = None # 로그 사용 안함
    
    log_message(log_file, f"[{datetime.datetime.now()}] Target: {img_path}")
    
    import time
    max_retries = 3
    img = None
    
    for attempt in range(max_retries):
        try:
            with Image.open(img_path) as opened_img:
                img = opened_img.copy() # 완전히 메모리로 복사하여 파일 락을 해제
            break # 성공적으로 열었으면 반복문 탈출
        except PermissionError as pe:
            if attempt < max_retries - 1:
                time.sleep(1) # 1초 대기 후 재시도
            else:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, f"파일이 다른 프로그램(포토샵, 이미지뷰어 등)에서 열려있거나 저장 중입니다.\n\n해당 프로그램을 닫은 후 다시 시도해주세요.\n\n대상: {img_path}", "파일 접근 불가", 0x30)
                return # 처리를 중단하고 빠져나감
        except Exception as e:
            raise e # 권한 오류가 아닌 다른 오류는 아래의 기존 except 블록으로 넘김
            
    try:
        # 이미지는 위에서 img.copy()로 성공적으로 로드됨
        if img is not None:
            # 대용량 이미지(특히 초고해상도 JPG) 메모리 에러 방지용 초벌 draft (로딩 속도 & 메모리 획기적 절약)
            if hasattr(img, 'draft'):
                try:
                    img.draft('RGB', (TARGET_W * 4, TARGET_H * 4))
                except Exception:
                    pass

            # 포토샵 정규화 방식 (RGB 변환)
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                # 투명 배경인 경우 검정색 변환을 막고 흰색 배경에 병합
                bg = Image.new('RGB', img.size, (255, 255, 255))
                bg.paste(img, mask=img.convert('RGBA').split()[3])
                img = bg
            elif img.mode != 'RGB':
                img = img.convert('RGB')
                
            in_w, in_h = img.size
            in_ratio = in_w / in_h
            slot_ratio = TARGET_W / TARGET_H
            
            # 비율 오차 계산
            diff = abs(in_ratio - slot_ratio) / slot_ratio
            
            if diff <= RATIO_TOL:
                log_message(log_file, f"AUTO -> CROP (ratio diff {diff*100:.2f}% <= {RATIO_TOL*100}%)")
                # CROP 로직 (비율 꽉 채우기 + 남는부분 자르기)
                # ★ int() 버림 대신 ceil() 올림 사용 → 리사이즈 결과가 TARGET_W/H보다 짧아지는 1~2px 오차 방지
                scale = max(TARGET_W / in_w, TARGET_H / in_h)
                new_w = math.ceil(in_w * scale)
                new_h = math.ceil(in_h * scale)
                resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # 중앙 크롭(Center Crop)
                left = (new_w - TARGET_W) / 2
                top  = (new_h - TARGET_H) / 2
                right  = left + TARGET_W
                bottom = top  + TARGET_H
                
                final_img = resized.crop((left, top, right, bottom))
                
                # ★ crop 결과 크기를 TARGET_W×TARGET_H로 강제 보장 (소수점 오차로 1~2px 부족한 경우 대비)
                if final_img.size != (TARGET_W, TARGET_H):
                    final_img = final_img.resize((TARGET_W, TARGET_H), Image.Resampling.LANCZOS)
            else:
                log_message(log_file, f"AUTO -> STRETCH (ratio diff {diff*100:.2f}% > {RATIO_TOL*100}%)")
                # STRETCH 로직 (강제 가로세로 수정)
                final_img = img.resize((TARGET_W, TARGET_H), Image.Resampling.LANCZOS)
                
            # 변경: 캔버스 배경색을 완전한 검정색(0, 0, 0)으로 설정
            # 전광판 제어기기가 1~2px 영역 밖을 읽더라도 LED가 꺼진 상태(검은색)로 표시되어 보이지 않게 됨
            CANVAS_W, CANVAS_H = 2560, 900
            canvas = Image.new('RGB', (CANVAS_W, CANVAS_H), (0, 0, 0))
            
            # ★ 우측 끝 픽셀 클램프 및 블리딩(Bleeding):
            # 1. 마지막 2열 픽셀을 안쪽(3번째-마지막) 픽셀로 복제하여 압축 아티팩트 방지
            arr = np.array(final_img)
            if arr.shape[1] >= 3:
                arr[:, -1] = arr[:, -3]  # 마지막 열 = 안쪽 픽셀
                arr[:, -2] = arr[:, -3]  # 마지막-1 열 = 안쪽 픽셀
            
            # 2. 전광판 하드웨어의 1px 폭 오차를 덮기 위해 우측 끝 픽셀을 추가로 2px 더 늘림 (Bleeding)
            # 현수막 폭이 2146px -> 2148px로 살짝 길어지며 오차영역을 현수막 색상으로 채움
            bleed_col = arr[:, -1:] # 가장 오른쪽 열 추출
            arr_expanded = np.concatenate((arr, bleed_col, bleed_col), axis=1) # 2픽셀 우측에 추가
            final_img = Image.fromarray(arr_expanded)

            # 현수막을 지정된 좌표에 붙여넣기
            # (좌측 기준 고정 X=207, 상단 고정 Y=244)
            canvas.paste(final_img, (207, 244))

            # 결과물 저장
            # ★ PNG 무손실 저장: JPEG 압축 번짐(DCT 아티팩트) 자체가 발생하지 않아
            #    우측 끝 흰 선 문제를 근본적으로 해결
            out_name = f"{name}_{timestamp}_final.png"
            out_path = os.path.join(out_dir, out_name)
            canvas.save(out_path, format='PNG')
            log_message(log_file, f"Saved: {out_path}\n" + "-"*40)
            
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, f"변환 실패: {img_path}\n\n[에러 내용]\n{err_msg}", "오류 발생", 0x10)
        log_message(log_file, f"!! ERROR on {img_path}: {str(e)}\n{err_msg}\n" + "-"*40)

if __name__ == '__main__':
    args = sys.argv[1:]
    
    if len(args) == 0:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, "윈도우에서 변환할 원본 사진 파일이나 폴더를\n이 프로그램 아이콘 위로 드래그 앤 드롭 하세요.", "사용 안내", 0)
        sys.exit(0)
    
    for path in args:
        if os.path.isfile(path):
            process_image(path)
        elif os.path.isdir(path):
            # 폴더를 통째로 드롭한 경우 폴더 내부 파일 순회
            for root, dirs, files in os.walk(path):
                for f in files:
                    process_image(os.path.join(root, f))
