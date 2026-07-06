import os
import shutil
import time

WORK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usb_sim_env")
NET_DIR = os.path.join(WORK_DIR, "BSS-DATA_MOCK", "07. 녹음녹화파일")
USB_DIR = os.path.join(WORK_DIR, "USB_MOCK")

def setup_mock_env():
    print("--- [1] 가상 환경 초기화 ---")
    if os.path.exists(WORK_DIR):
        shutil.rmtree(WORK_DIR)
    os.makedirs(NET_DIR, exist_ok=True)
    os.makedirs(USB_DIR, exist_ok=True)
    
    # Create sample data based on user's image
    folders = [
        "2026.01.05(월) [화상] 26년 설특판 전략회의",
        "2026.01.12(월) [화상] 농심천심 실무자 회의",
        "2026.02.03(화) [대강당] 2월 정례조회",
        "##폐기파일",
        "#지난자료"
    ]
    for f in folders:
        f_path = os.path.join(NET_DIR, f)
        os.makedirs(f_path, exist_ok=True)
        if not f.startswith("#"):
            # Create dummy media files
            with open(os.path.join(f_path, f"{f}.mp3"), "w", encoding="utf-8") as file:
                file.write("dummy audio data")
            with open(os.path.join(f_path, f"{f}.mp4"), "w", encoding="utf-8") as file:
                file.write("dummy video data")
    print("✅ 가상 BSS-DATA 네트워크 폴더 및 가상 USB 세팅 완료.")

def simulate_search(keyword):
    print(f"\n--- [2] 검색 엔진 작동 시뮬레이션 ---")
    print(f"사용자 입력 키워드: '{keyword}'")
    
    all_folders = [f for f in os.listdir(NET_DIR) if os.path.isdir(os.path.join(NET_DIR, f)) and not f.startswith("#")]
    
    results = [f for f in all_folders if keyword in f]
    if results:
        for r in results:
            print(f"   👉 찾음: {r}")
    else:
        print("   ❌ 결과 없음")
    return results

def simulate_copy(target_folder_name):
    print(f"\n--- [3] USB 복사 및 예외 처리 시뮬레이션 ---")
    src = os.path.join(NET_DIR, target_folder_name)
    dst = os.path.join(USB_DIR, target_folder_name)
    
    # 예외 상황: 오버라이트(덮어쓰기) 방어 로직
    if os.path.exists(dst):
        print("   ⚠️ [이벤트 발생] 이미 가상 USB에 동일한 이름의 폴더가 존재합니다!")
        print("   (내부 로직 동작) => 사용자에게 덮어쓰기 여부 팝업창을 띄웁니다.")
        print("   (가정) => 사용자가 '예(덮어쓰기)'를 클릭했습니다.")
        shutil.rmtree(dst) # Delete old to overwrite
        
    print("   [진행률 0%] 복사 시작...")
    shutil.copytree(src, dst)
    print("   [진행률 100%] 복사 완료 무결성 검증 중...")
    
    # 검증
    copied_files = os.listdir(dst)
    print(f"   ✔️ 가상 USB 내 무사히 복사된 파일 목록: {copied_files}")
    print("   ✨ 미션 성공!")

if __name__ == "__main__":
    setup_mock_env()
    
    # 시나리오: '설특판' 검색 후 복사
    res = simulate_search("설특판")
    if res:
        simulate_copy(res[0])
        
        # 중복 충돌 감지(옵션 C)를 확인하기 위해 곧바로 1회 더 복사 시도
        simulate_copy(res[0])
