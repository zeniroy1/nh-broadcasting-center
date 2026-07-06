# -*- coding: utf-8 -*-
import os, glob, sys
from PIL import Image
import numpy as np

# PyInstaller exe로 실행될 때와 일반 py 실행 시 경로가 다름
if getattr(sys, 'frozen', False):
    # exe로 실행: exe 파일이 있는 폴더 기준
    base_dir = os.path.dirname(sys.executable)
else:
    # py 스크립트로 실행
    base_dir = os.path.dirname(os.path.abspath(__file__))

output_dir = os.path.join(base_dir, '_output')
jpgs = glob.glob(os.path.join(output_dir, '*.png')) + glob.glob(os.path.join(output_dir, '*.jpg'))

if not jpgs:
    import ctypes
    ctypes.windll.user32.MessageBoxW(
        0,
        f"_output 폴더에 JPG 파일이 없습니다.\n먼저 배너자동화.exe로 이미지를 처리해주세요.\n\n경로: {output_dir}",
        "분석 파일 없음", 0x30
    )
else:
    latest = max(jpgs, key=os.path.getmtime)
    img = Image.open(latest)
    arr = np.array(img)
    H, W, _ = arr.shape

    PASTE_X  = 207
    PASTE_Y  = 244
    TARGET_W = 2146
    TARGET_H = 130
    br = PASTE_X + TARGET_W  # 현수막 우측 끝 x좌표

    def analyze_col(x, label):
        col = arr[PASTE_Y:PASTE_Y+TARGET_H, min(x, W-1), :]
        whites = int(np.sum(np.all(col >= 248, axis=1)))
        avg = col.mean(axis=0).astype(int)
        status = "[!] 흰색 감지!" if whites > 0 else "[OK] 정상"
        return (f"{label}\n"
                f"  평균RGB=({avg[0]},{avg[1]},{avg[2]})  "
                f"흰픽셀={whites}/{TARGET_H}행  {status}")

    lines = []
    lines.append(f"파일: {os.path.basename(latest)}")
    lines.append(f"이미지 크기: {W} x {H}px")
    lines.append(f"현수막 우측끝: x={br-1}  경계다음: x={br}")
    lines.append("")
    lines.append(analyze_col(br-3, f"[x={br-3}] 현수막 끝-2열"))
    lines.append(analyze_col(br-2, f"[x={br-2}] 현수막 끝-1열"))
    lines.append(analyze_col(br-1, f"[x={br-1}] 현수막 마지막열  <<"))
    lines.append(analyze_col(br,   f"[x={br}  ] 경계 다음열 (흰배경시작)"))
    lines.append("")
    lines.append("--- 중간행 픽셀 샘플 (현수막끝 +-3) ---")
    mid = PASTE_Y + TARGET_H // 2
    for x in range(br-3, min(br+4, W)):
        r, g, b = arr[mid, x]
        mark = " << 현수막끝" if x == br-1 else (" << 흰배경시작" if x == br else "")
        lines.append(f"  x={x}: RGB({r:3},{g:3},{b:3}){mark}")

    result = "\n".join(lines)
    import ctypes
    ctypes.windll.user32.MessageBoxW(0, result, "픽셀 분석 결과", 0)
