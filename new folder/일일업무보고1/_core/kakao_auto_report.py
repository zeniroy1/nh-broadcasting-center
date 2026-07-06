"""
========================================
 카카오톡 일일업무보고 자동 전송 스크립트
========================================
기능: 일일업무보고.txt에서 최신 날짜의 당일/익일 일정을 파싱하여
      PC 카카오톡 단체톡방에 자동 전송합니다.

사용법:
  1. 아래 설정값을 수정하세요 (CHATROOM_NAME, REPORT_FILE)
  2. PC 카카오톡이 실행 중이어야 합니다
  3. python kakao_auto_report.py 실행

필요 라이브러리:
  pip install pyautogui pyperclip
"""

import re
import time
import sys
import subprocess

# pyautogui/pyperclip는 실제 전송 시에만 필요 → 없어도 --test 모드는 동작
try:
    import pyautogui
    import pyperclip
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

# ============================================================
# ★ 설정값 (수정 프로그램 `1_설정변경.bat`을 이용하세요) ★
# ============================================================
import json
import os

# _core 하위 폴더 기준으로 상위 폴더(..)의 일일업무보고.txt 위치 자동 설정
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_FILE = os.path.join(base_dir, '일일업무보고.txt')

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'settings.json')
try:
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        _settings = json.load(f)
        CHATROOM_NAME = _settings.get('chatroom_name', "함현식")
except:
    CHATROOM_NAME = "함현식"  # 기본 채팅방 이름

SEND_DELAY = 1.0             # 각 동작 사이 대기 시간(초)
# ============================================================


def parse_daily_report(filepath):
    """일일업무보고.txt에서 가장 최근 날짜의 당일/익일 일정 추출"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    date_pattern = re.compile(r'(\d{1,2}월\s*\d{1,2}\([월화수목금토일]\))')
    separator_pattern = re.compile(r'^-{5,}')

    first_date = None
    today_items = []
    tomorrow_items = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        match = date_pattern.search(line)

        if match:
            first_date = match.group(1)
            i += 1

            # 당일 일정 (점선 전까지)
            while i < len(lines):
                line = lines[i].strip()
                if separator_pattern.match(line):
                    i += 1
                    break
                if line.startswith('○'):
                    today_items.append(line)
                i += 1

            # 익일 일정 (빈줄 2개 이상 or 다음 날짜 전까지)
            blank_count = 0
            while i < len(lines):
                line = lines[i].strip()
                if date_pattern.search(line):
                    break
                if line == '':
                    blank_count += 1
                    if blank_count >= 2:
                        break
                else:
                    blank_count = 0
                if line.startswith('○'):
                    tomorrow_items.append(line)
                i += 1

            break  # 첫 번째(가장 최근) 날짜만 처리
        i += 1

    return first_date, today_items, tomorrow_items


def format_message(date, today_items, tomorrow_items):
    """카카오톡 전송용 메시지 생성 - 날짜 + 전체 일정 연속 나열"""
    msg = f"{date}\n"
    for item in today_items:
        msg += f"{item}\n"
    for item in tomorrow_items:
        msg += f"{item}\n"
    return msg.strip()


def find_kakao_window(title):
    """win32gui로 카카오톡 진짜 창 핸들을 탐색 (숨겨진 트레이 창 포함)"""
    try:
        import win32gui
        result = []
        def enum_cb(hwnd, _):
            t = win32gui.GetWindowText(hwnd)
            if title in t:
                rect = win32gui.GetWindowRect(hwnd)
                w = rect[2] - rect[0]
                h = rect[3] - rect[1]
                # 크기가 100x100 이상인 진짜 창만 선택 (보이는지 여부 상관없이)
                if w > 100 and h > 100:
                    result.append(hwnd)
        win32gui.EnumWindows(enum_cb, None)
        return result[0] if result else None
    except Exception:
        return None


def activate_hwnd(hwnd):
    """win32gui와 ctypes를 이용해 창을 완벽하게 전면 포커스합니다."""
    try:
        import win32gui, win32con, win32process, win32api
        import ctypes
        import pyautogui
        
        # 1. 윈도우 API로 창 복원 및 전면 호출
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

        # 2. 강제 포커스 탈취를 위한 AttachThreadInput 트릭
        user32 = ctypes.windll.user32
        target_tid, _ = win32process.GetWindowThreadProcessId(hwnd)
        current_tid = win32api.GetCurrentThreadId()

        if current_tid != target_tid:
            user32.AttachThreadInput(current_tid, target_tid, True)
            win32gui.SetForegroundWindow(hwnd)
            user32.BringWindowToTop(hwnd)
            user32.AttachThreadInput(current_tid, target_tid, False)
        else:
            win32gui.SetForegroundWindow(hwnd)
            user32.BringWindowToTop(hwnd)

        time.sleep(0.5)

        # 3. 확실한 포커스를 위해 창의 상단 (제목 표시줄)을 물리적으로 클릭
        rect = win32gui.GetWindowRect(hwnd)
        click_x = rect[0] + 100
        click_y = rect[1] + 10
        pyautogui.click(click_x, click_y)
        time.sleep(1.0)
    except Exception as e:
        print(f"[경고] 창 활성화 보조 로직 실패: {e}")


def click_chat_tab(hwnd):
    """카카오톡 메인 창에서 채팅 탭(말풍선) 아이콘을 눌러 채팅 탭으로 전환합니다."""
    try:
        import win32gui
        import pyautogui

        rect = win32gui.GetWindowRect(hwnd)
        win_x = rect[0]
        win_y = rect[1]
        win_h = rect[3] - rect[1]

        # 카카오톡 왼쪽 사이드바의 채팅 탭(말풍선) 아이콘 위치:
        # - 창 왼쪽에서 약 30px, 창 높이의 약 15% 지점 (친구→채팅 아이콘 순서)
        tab_x = win_x + 30
        tab_y = win_y + int(win_h * 0.15)

        pyautogui.click(tab_x, tab_y)
        time.sleep(0.8)
        print("[정보] 채팅 탭 클릭 완료.")
    except Exception as e:
        print(f"[경고] 채팅 탭 전환 클릭 실패: {e}")


def _write_log(msg):
    try:
        log_file = os.path.join(os.path.dirname(__file__), 'run_log.txt')
        now_str = time.strftime('%Y-%m-%d %H:%M:%S')
        with open(log_file, 'a', encoding='utf-8') as lf:
            lf.write(f"[{now_str}] {msg}\n")
    except Exception:
        pass

def send_to_kakao(chatroom_name, message):
    """PC 카카오톡 단톡방에 메시지 전송"""
    _write_log(f"시작: 카카오톡 전송 시도 ({chatroom_name})")
    if not GUI_AVAILABLE:
        print("[오류] pyautogui / pyperclip 라이브러리가 없습니다.")
        _write_log("실패: 라이브러리 없음")
        return

    try:
        # 1. 카카오톡 실행 (이미 실행 중이면 무시되거나 트레이에서 복원됨)
        subprocess.Popen(
            r'"C:\Program Files\Kakao\KakaoTalk\KakaoTalk.exe"',
            shell=True
        )
    except Exception as e:
        _write_log(f"실패: 카카오톡 실행 에러 - {e}")
        return

    print("[정보] 카카오톡 창 활성화 대기 중...")
    time.sleep(7)  # 트레이에서 올라오는 시간 충분히 대기

    # 2. 채팅방 창이 이미 열려있으면 바로 사용
    chat_hwnd = find_kakao_window(chatroom_name)
    if chat_hwnd:
        print(f"[정보] '{chatroom_name}' 채팅창 직접 탐지 성공.")
        activate_hwnd(chat_hwnd)
        time.sleep(SEND_DELAY)
        try:
            pyperclip.copy(message)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(0.5)
            pyautogui.press('esc')
            time.sleep(0.5)
            print("[완료] 메시지 전송 및 창 닫기 완료!")
            _write_log(f"성공: '{chatroom_name}' 채팅방 직접 전송 완료")
            return
        except Exception as e:
            _write_log(f"실패: 채팅방 직접 제어 중 오류 발생 - {e}")
            return

    # 3. 채팅창이 없으면 메인 카카오톡 창에서 검색
    print(f"[정보] '{chatroom_name}' 채팅창 미발견 -> 메인 창에서 검색합니다.")
    kakao_hwnd = find_kakao_window('카카오톡')
    if not kakao_hwnd:
        print("[오류] 카카오톡 창을 찾지 못했습니다. 카카오톡을 실행하고 다시 시도하세요.")
        _write_log(f"실패: 카카오톡 메인 창을 찾지 못함")
        return

    activate_hwnd(kakao_hwnd)
    time.sleep(SEND_DELAY)

    try:
        # ★ 핵심: 검색 전 반드시 채팅 탭(말풍선)으로 전환 ★
        print("[정보] 채팅 탭으로 전환 중 (말풍선 아이콘 클릭)...")
        click_chat_tab(kakao_hwnd)
        time.sleep(SEND_DELAY)

        # Ctrl+F: 카카오톡 채팅방 검색창 포커스
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(1.5)

        # 기존 검색어가 있으면 삭제
        pyautogui.press('home')
        time.sleep(0.2)
        pyautogui.hotkey('shift', 'end')
        time.sleep(0.2)
        pyautogui.press('delete')
        time.sleep(0.5)

        pyperclip.copy(chatroom_name)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(SEND_DELAY)

        pyautogui.press('enter')
        time.sleep(SEND_DELAY)

        pyperclip.copy(message)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)

        pyautogui.press('enter')
        time.sleep(0.5)

        # 전송 후 창 닫기 (Esc)
        pyautogui.press('esc')
        time.sleep(0.5)

        print("[완료] 메시지 전송 및 창 닫기 완료!")
        _write_log(f"성공: '{chatroom_name}' 채팅방 전송 완료")
    except Exception as e:
        print(f"[오류] 화면 잠금, 절전 모드 또는 카카오톡 제어 중 문제 발생: {e}")
        _write_log(f"실패: 제어 중 오류 발생 (화면잠금 등) - {e}")



def get_user_time():
    """사용자에게 전송 시간(시, 분)을 입력받아 반환"""
    print("\n" + "=" * 50)
    print(" 카카오톡 자동 전송 시간 설정")
    print("=" * 50)
    print(" 전송할 시간을 입력하세요. (24시간제 기준)")
    print(" 엔터만 누르면 기본값(15시 30분)으로 설정됩니다.")
    print("=" * 50)

    while True:
        try:
            hour_input = input("  시(HH) 입력 [기본: 15]: ").strip()
            hour = int(hour_input) if hour_input else 15
            if 0 <= hour <= 23:
                break
            print("  ⚠ 0~23 사이의 숫자를 입력하세요.")
        except ValueError:
            print("  ⚠ 숫자를 입력하세요.")

    while True:
        try:
            minute_input = input("  분(MM) 입력 [기본: 30]: ").strip()
            minute = int(minute_input) if minute_input else 30
            if 0 <= minute <= 59:
                break
            print("  ⚠ 0~59 사이의 숫자를 입력하세요.")
        except ValueError:
            print("  ⚠ 숫자를 입력하세요.")

    return hour, minute


def main():
    print("=" * 50)
    print(" 카카오톡 일일업무보고 자동 전송")
    print("=" * 50)

    import sys

    # ── 실행 모드 분기 ──────────────────────────────
    # 1) --test    : 파싱 결과만 화면에 출력 (카톡 전송 안 함)
    # 2) --schedule: 스케줄러에서 자동 실행 (사람 입력 없이 즉시 전송)
    # 3) 인수 없음 : 대화형 모드 (시간 입력 후 전송)
    # ────────────────────────────────────────────────
    mode = sys.argv[1] if len(sys.argv) > 1 else "interactive"

    # 파싱
    date, today, tomorrow = parse_daily_report(REPORT_FILE)

    if not date:
        print("❌ 오류: 일정 데이터를 찾을 수 없습니다.")
        return

    # 메시지 생성
    message = format_message(date, today, tomorrow)

    print(f"\n[날짜] {date}")
    print(f"[일정] 당일 {len(today)}건 / 익일 {len(tomorrow)}건")
    print(f"\n--- 전송 메시지 미리보기 ---\n{message}\n---\n")

    if mode == "--test":
        print("[테스트 모드] 위 메시지가 파싱 결과입니다. 카카오톡 전송은 하지 않습니다.")
        return

    # 전송 (즉시 or 대화형)
    send_to_kakao(CHATROOM_NAME, message)


if __name__ == "__main__":
    main()
