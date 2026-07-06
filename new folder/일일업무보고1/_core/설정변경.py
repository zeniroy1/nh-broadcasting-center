import json
import os
import subprocess

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'settings.json')

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"chatroom_name": "함현식"}

def save_config(chatroom_name):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump({"chatroom_name": chatroom_name}, f, ensure_ascii=False, indent=4)

def setup_launcher():
    """폴더 위치가 바뀌어도 동작하도록 C:\\kakao_report 런처를 현재 위치 기반으로 자동 재생성"""
    kakao_report_dir = r"C:\kakao_report"
    os.makedirs(kakao_report_dir, exist_ok=True)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(current_dir, "kakao_auto_report.py")
    
    launcher_code = f'''"""
launcher.py - Korean path safe launcher for scheduled task
"""
import importlib.util
import sys
import os

SCRIPT_PATH = r"{script_path}"

spec = importlib.util.spec_from_file_location("kakao_auto_report", SCRIPT_PATH)
mod = importlib.util.module_from_spec(spec)
sys.argv = [SCRIPT_PATH]
spec.loader.exec_module(mod)
mod.main()
'''
    with open(os.path.join(kakao_report_dir, "launcher.py"), "w", encoding="utf-8") as f:
        f.write(launcher_code)
        
    bat_code = '''@echo off
py -3.13 "C:\\kakao_report\\launcher.py"
'''
    with open(os.path.join(kakao_report_dir, "run.bat"), "w", encoding="utf-8") as f:
        f.write(bat_code)

def setup_schedule():
    config = load_config()
    current_chat = config.get("chatroom_name", "함현식")
    
    print(f"\n[ 1. 카카오톡 채팅방 이름 설정 ]")
    print(f"현재 설정된 채팅방: {current_chat}")
    new_chat = input("새로운 카카오톡 채팅방 이름을 입력하세요 (변경하지 않으려면 그냥 엔터): ").strip()
    
    if new_chat:
        chatroom_name = new_chat
        save_config(chatroom_name)
        print(f" -> 채팅방 이름이 '{chatroom_name}'(으)로 변경되었습니다. (저장 완료)")
    else:
        chatroom_name = current_chat
        save_config(chatroom_name)
        print(" -> 채팅방 이름을 기존과 동일하게 유지합니다.")
        
    print("\n" + "=" * 60)
    print("[ 2. 스케줄러(자동 전송 시간) 시간 재설정 ]")
    
    time_input = input("새로운 자동 전송 시간을 HH:MM 형식으로 입력하세요 (예: 15:30) (변경하지 않으려면 엔터): ").strip()
    
    if time_input:
        if len(time_input) == 5 and ":" in time_input:
            print(f"\n스케줄러를 매일 {time_input} 자동 실행으로 재등록합니다...")
            subprocess.run(['schtasks', '/delete', '/tn', 'DailyReport', '/f'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            cmd = ['schtasks', '/create', '/tn', 'DailyReport', '/tr', r'C:\kakao_report\run.bat', '/sc', 'daily', '/st', time_input, '/f', '/it']
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                # 시간이 지나더라도 부팅/절전모드해제 시 "가능한 한 빨리 작업 시작" 옵션 제거 (아침에 보내지는 현상 방지)
                # 추가: 해당 시간에 컴퓨터가 절전 모드일 경우 깨워서 실행할 수 있도록 WakeToRun 옵션 추가
                ps_cmd = "Set-ScheduledTask -TaskName 'DailyReport' -Settings (New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun)"
                subprocess.run(['powershell', '-Command', ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f" -> 매일 {time_input} 전송 스케줄러 등록 완료! ✅")
            else:
                print(" -> [오류] 스케줄러 등록에 실패했습니다.")
        else:
            print(" -> [오류] 올바른 시간 형식이 아닙니다 (예: 15:30). 시간 변경 취소됨.")
    else:
        print(" -> 스케줄러 시간 변경을 건너뜁니다.")


def toggle_schedule():
    print("\n" + "=" * 60)
    print(" [ 전송 예약 켜기 / 끄기 (ON/OFF) ]")
    print("=" * 60)
    # capture_output 사용 시 한글 윈도우에서 인코딩 에러 방지를 위해 errors='ignore' 추가
    res = subprocess.run(['schtasks', '/query', '/tn', 'DailyReport'], capture_output=True, text=True, errors='ignore')
    stdout = res.stdout if res.stdout else ""
    if "Ready" in stdout or "준비" in stdout:
        print("\n▶ 현재 예약 상태: [자동 전송 켜짐 (ON)] 활성화 상태입니다.")
        ans = input("오늘 하루 혹은 당분간 예약 전송을 끄시겠습니까? (y/n): ").strip().lower()
        if ans == 'y':
            subprocess.run(['schtasks', '/change', '/tn', 'DailyReport', '/disable'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("\n[완료] 전송 예약이 일시정지(OFF) 되었습니다! 🛑")
        else:
            print("\n-> 예약을 끄지 않고 유지합니다.")
    else:
        print("\n▶ 현재 예약 상태: [자동 전송 꺼짐 (OFF)] 일시정지 상태입니다.")
        ans = input("예약 전송을 다시 켜시겠습니까? (y/n): ").strip().lower()
        if ans == 'y':
            subprocess.run(['schtasks', '/change', '/tn', 'DailyReport', '/enable'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("\n[완료] 전송 예약이 다시 활성화(ON) 되었습니다! ✅")
        else:
            print("\n-> 예약을 켜지 않고 유지합니다.")


def main():
    setup_launcher()
    while True:
        # 메뉴 표시 직전에 현재 스케줄러 상태를 매번 체크 (인코딩 에러 방지 적용)
        status_res = subprocess.run(['schtasks', '/query', '/tn', 'DailyReport'], capture_output=True, text=True, errors='ignore')
        stdout_text = status_res.stdout if status_res.stdout else ""
        if "Ready" in stdout_text or "준비" in stdout_text:
            current_status = "[자동 전송 켜짐 (ON) 🟢]"
        elif "Disabled" in stdout_text or "사용 안 함" in stdout_text:
            current_status = "[자동 전송 꺼짐 (OFF) 🔴]"
        else:
            current_status = "[상태 미확인 (스케줄 없음)]"

        print("\n" + "=" * 60)
        print(" 일일업무보고 자동 전송 - 통합 제어 프로그램 ")
        print("=" * 60)
        print(" 1. 채팅방 이름 및 전송 시간 설정")
        print(f" 2. 예약 전송 켜기 / 끄기 {current_status}")
        print(" 3. 프로그램 종료")
        print("=" * 60)
        
        choice = input("원하시는 메뉴 번호를 입력하세요 (1~3): ").strip()
        
        if choice == '1':
            setup_schedule()
        elif choice == '2':
            toggle_schedule()
        elif choice == '3':
            print("\n설정 변경 프로그램을 종료합니다.")
            break
        else:
            print("\n[안내] 1, 2, 3 중에서 올바른 번호를 입력해주세요.")

if __name__ == '__main__':
    main()
