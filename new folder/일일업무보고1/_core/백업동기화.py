import shutil
import os
import time

print("==============================================")
print(" 일일업무보고 2곳(서버, USB) 동시 덮어쓰기 시작")
print("==============================================\n")

# _core 하위 폴더 기준 상위 폴더의 일일업무보고.txt 경로
current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(current_dir)
source_file = os.path.join(base_dir, "일일업무보고.txt")

# 대상 경로
network_dest = r"\\Bss-data\자료폴더\◆ 책임자\04.수시\시설 일일업무보고\일일업무보고(메모장).txt"
usb_dest = r"D:\일일업무보고.txt"

# 1. 서버 복사
try:
    if not os.path.exists(source_file):
        print(f"[오류] 원본 파일이 없습니다: {source_file}")
    else:
        shutil.copy2(source_file, network_dest)
        print(f"[성공] 서버(Bss-data) 폴더에 원본이 덮어씌워졌습니다.")
except Exception as e:
    print(f"[실패] 서버 복사 실패: {e}")

print()

# 2. USB 복사
try:
    if os.path.exists(source_file):
        shutil.copy2(source_file, usb_dest)
        print(r"[성공] D:\ 드라이브(USB)에 백업되었습니다.")
except Exception as e:
    print(rf"[경고] D:\ 드라이브(USB) 저장 실패! (경고 메시지: {e})")

print("\n==============================================")
print("모든 작업이 끝났습니다.")
print("==============================================")
input("\n창을 닫으려면 엔터 키를 누르세요...")
