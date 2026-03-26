"""
========================================
 카카오톡 개인 메시지 자동 전송 스크립트
========================================
 fixed_messages.txt  → 고정 메시지 (계속 추가 가능)
 today_message.txt   → 오늘 자유 메시지 (전송 후 자동 초기화)
 1_메시지전송.bat    → 실행 파일
"""

import json
import os
import sys
import time
import subprocess
import datetime

try:
    import pyautogui
    import pyperclip
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

# ─────────────────────────────────────────
# 경로 설정
# ─────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))   # _core/
PARENT_DIR = os.path.dirname(BASE_DIR)                     # 개인메시지 자동화/

FIXED_FILE   = os.path.join(PARENT_DIR, 'fixed_messages.txt')
FREE_FILE    = os.path.join(PARENT_DIR, 'free_message.txt')
PENDING_FILE = os.path.join(BASE_DIR,   'pending.json')

FREE_TEMPLATE = "# 여기에 제목 입력\n채팅방: 여기에 채팅방 이름 입력\n시간: 즉시\n여기에 메시지를 입력하세요.\n"

SEND_DELAY = 1.0


# ─────────────────────────────────────────
# txt 파서
# ─────────────────────────────────────────
def parse_message_file(filepath):
    """
    txt 파일을 파싱하여 메시지 목록 반환.
    각 항목: {'title': str, 'chatroom': str, 'time': str, 'message': str}
    블록은 === 으로 구분.
    """
    results = []
    if not os.path.exists(filepath):
        return results

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return results

    blocks = content.split('===')
    for block in blocks:
        lines = [l.rstrip() for l in block.strip().splitlines()]
        if not lines:
            continue

        # 주석(#으로 시작)만 있는 블록은 건너뜀
        non_comment = [l for l in lines if not l.strip().startswith('#')]
        if not non_comment:
            continue

        title    = ''
        chatroom = ''
        send_time = '즉시'
        msg_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                if not title:
                    title = stripped.lstrip('#').strip()
            elif stripped.lower().startswith('채팅방:'):
                chatroom = stripped.split(':', 1)[1].strip()
            elif stripped.lower().startswith('시간:'):
                send_time = stripped.split(':', 1)[1].strip()
            else:
                # 본문(msg_lines)이 아직 비어있는데 빈 줄이 들어오면 무시 (시작 부분 빈 줄 방지)
                if not msg_lines and not stripped:
                    continue
                msg_lines.append(line)

        # 다 모은 후에도 끝에 남은 빈 줄 정리
        message = '\n'.join(msg_lines).strip()

        # 채팅방과 메시지가 모두 있어야 유효
        if not chatroom or not message:
            continue


        results.append({
            'title':    title if title else f'메시지 {len(results)+1}',
            'chatroom': chatroom,
            'time':     send_time,
            'message':  message,
        })

    return results


def reset_free_file():
    """free_message.txt 를 초기 템플릿으로 초기화"""
    with open(FREE_FILE, 'w', encoding='utf-8') as f:
        f.write(FREE_TEMPLATE)


# ─────────────────────────────────────────
# 카카오톡 전송 핵심 로직
# ─────────────────────────────────────────
def find_kakao_window(title):
    try:
        import win32gui
        result = []
        def enum_cb(hwnd, _):
            t = win32gui.GetWindowText(hwnd)
            if title in t:
                rect = win32gui.GetWindowRect(hwnd)
                w = rect[2] - rect[0]
                h = rect[3] - rect[1]
                if w > 100 and h > 100:
                    result.append(hwnd)
        win32gui.EnumWindows(enum_cb, None)
        return result[0] if result else None
    except Exception:
        return None


def activate_hwnd(hwnd):
    try:
        import win32gui, win32con, win32process, win32api
        import ctypes
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        user32    = ctypes.windll.user32
        target_tid, _ = win32process.GetWindowThreadProcessId(hwnd)
        current_tid    = win32api.GetCurrentThreadId()
        if current_tid != target_tid:
            user32.AttachThreadInput(current_tid, target_tid, True)
            win32gui.SetForegroundWindow(hwnd)
            user32.BringWindowToTop(hwnd)
            user32.AttachThreadInput(current_tid, target_tid, False)
        else:
            win32gui.SetForegroundWindow(hwnd)
            user32.BringWindowToTop(hwnd)
        time.sleep(0.5)
        rect    = win32gui.GetWindowRect(hwnd)
        pyautogui.click(rect[0] + 100, rect[1] + 10)
        time.sleep(1.0)
    except Exception as e:
        print(f'[경고] 창 활성화 실패: {e}')


def click_chat_tab(hwnd):
    try:
        import win32gui
        rect  = win32gui.GetWindowRect(hwnd)
        tab_x = rect[0] + 30
        tab_y = rect[1] + int((rect[3] - rect[1]) * 0.15)
        pyautogui.click(tab_x, tab_y)
        time.sleep(0.8)
        print('[정보] 채팅 탭 클릭 완료.')
    except Exception as e:
        print(f'[경고] 채팅 탭 전환 실패: {e}')


def send_to_kakao(chatroom_name, message):
    if not GUI_AVAILABLE:
        print('[오류] pyautogui / pyperclip 라이브러리가 없습니다.')
        print('   py -3.13 -m pip install pyautogui pyperclip pywin32')
        return False

    subprocess.Popen(
        r'"C:\Program Files\Kakao\KakaoTalk\KakaoTalk.exe"',
        shell=True
    )
    print('[정보] 카카오톡 창 활성화 대기 중...')
    time.sleep(5)

    chat_hwnd = find_kakao_window(chatroom_name)
    if chat_hwnd:
        print(f"[정보] '{chatroom_name}' 채팅창 직접 탐지 성공.")
        activate_hwnd(chat_hwnd)
        time.sleep(SEND_DELAY)
        pyperclip.copy(message)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(0.5)
        pyautogui.press('esc')
        time.sleep(0.5)
        print('[완료] 메시지 전송 완료!')
        return True

    kakao_hwnd = find_kakao_window('카카오톡')
    if not kakao_hwnd:
        print('[오류] 카카오톡 창을 찾지 못했습니다.')
        return False

    activate_hwnd(kakao_hwnd)
    time.sleep(SEND_DELAY)
    click_chat_tab(kakao_hwnd)
    time.sleep(SEND_DELAY)

    # ★ 돋보기 아이콘 2번 클릭: 1번=검색창 닫힘(텍스트 초기화), 2번=빈 검색창 열림
    #   → Ctrl+F / Ctrl+A 등 카카오톡 전역 단축키 충돌 완전 회피
    import win32gui
    rect     = win32gui.GetWindowRect(kakao_hwnd)
    win_x    = rect[0]
    win_y    = rect[1]
    win_w    = rect[2] - rect[0]
    # 돋보기 아이콘 위치: 채팅 헤더 오른쪽, 위에서 약 38px
    # (창 크기에 따라 오차 있을 수 있음 – 조정 필요 시 아래 값 수정)
    icon_x   = win_x + win_w - 115   # 🔍 돋보기 아이콘 (오픈채팅 ➕ 보다 좌측)
    icon_y   = win_y + 42

    pyautogui.click(icon_x, icon_y)   # 1번 클릭: 닫기 + 텍스트 초기화
    time.sleep(0.6)
    pyautogui.click(icon_x, icon_y)   # 2번 클릭: 빈 검색창 열기
    time.sleep(1.2)                   # 검색창 완전히 열릴 때까지 대기

    pyperclip.copy(chatroom_name)
    pyautogui.hotkey('ctrl', 'v')     # 빈 검색창에 채팅방 이름 붙여넣기
    time.sleep(SEND_DELAY)
    pyautogui.press('enter')          # 첫 번째 결과(채팅방) 열기
    time.sleep(2.0)                   # 채팅방 창 열릴 때까지 대기

    # ★ 핵심: 열린 채팅방 창을 다시 탐지해서 직접 사용
    #   → 통합검색창이 아니라 채팅방 입력창에 메시지 전달
    chat_hwnd = find_kakao_window(chatroom_name)
    if chat_hwnd:
        print(f"[정보] 검색 후 '{chatroom_name}' 채팅창 탐지 성공. 창에 직접 전송합니다.")
        activate_hwnd(chat_hwnd)
        time.sleep(SEND_DELAY)
        pyperclip.copy(message)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(0.5)
        pyautogui.press('esc')
        time.sleep(0.5)
        print('[완료] 메시지 전송 완료!')
        return True

    # 채팅방 창을 따로 찾지 못하면 포커스 그대로 붙여넣기 (fallback)
    print('[경고] 채팅방 창 재탐지 실패 → 현재 포커스에 직접 전송 시도')
    pyperclip.copy(message)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(0.5)
    pyautogui.press('esc')
    time.sleep(0.5)

    print('[완료] 메시지 전송 완료!')
    return True


# ─────────────────────────────────────────
# 예약 전송 (schtasks)
# ─────────────────────────────────────────
def schedule_with_schtasks(chatroom_name, message, target_time):
    """Windows 작업 스케줄러에 1회성 작업 등록 후 창 종료"""
    # 메시지를 pending.json에 저장
    pending = {
        'chatroom': chatroom_name,
        'message':  message,
        'is_today': False,  # today_message 여부는 사전에 처리됨
    }
    with open(PENDING_FILE, 'w', encoding='utf-8') as f:
        json.dump(pending, f, ensure_ascii=False, indent=2)

    script_path = os.path.abspath(__file__)
    time_str    = target_time.strftime('%H:%M')
    date_str    = target_time.strftime('%m/%d/%Y')

    # schtasks 명령 구성
    cmd = (
        f'schtasks /create /tn "KakaoPersonalMsg" '
        f'/tr "py -3.13 \\"{script_path}\\" --auto-send" '
        f'/sc once /sd {date_str} /st {time_str} /f'
    )

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f'\n  ✅ 예약 완료! [{time_str}] 에 자동 전송됩니다.')
        print('  창을 닫아도 예약이 유지됩니다.')
    else:
        print(f'\n  [오류] 예약 등록 실패: {result.stderr}')
        print('  직접 전송으로 대체합니다...')
        # 실패 시 카운트다운 방식으로 fallback
        countdown_fallback(chatroom_name, message, target_time)


def countdown_fallback(chatroom_name, message, target_time):
    """schtasks 실패 시 기존 카운트다운 방식으로 전송"""
    print(f"\n  ⚠ 카운트다운 대기 중 (창을 닫으면 취소)")
    while True:
        now       = datetime.datetime.now()
        remaining = (target_time - now).total_seconds()
        if remaining <= 0:
            break
        h = int(remaining // 3600)
        m = int((remaining % 3600) // 60)
        s = int(remaining % 60)
        print(f'\r  [대기중] {target_time.strftime("%H:%M")} 까지  {h:02d}:{m:02d}:{s:02d} 남음   ', end='', flush=True)
        time.sleep(1)
    print('\n\n[정보] 전송 시작...')
    send_to_kakao(chatroom_name, message)


def parse_time_str(time_str):
    """시간 문자열 파싱 → datetime or None(즉시)"""
    if time_str.strip() in ('즉시', ''):
        return None
    try:
        hour, minute = map(int, time_str.strip().split(':'))
        now    = datetime.datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += datetime.timedelta(days=1)
        return target
    except Exception:
        return None


# ─────────────────────────────────────────
# 메뉴 출력
# ─────────────────────────────────────────
def hr(char='─', width=50):
    print(char * width)


def _dw(s):
    """터미널 표시 너비 계산 (한글/전각 = 2, 나머지 = 1)"""
    import unicodedata
    return sum(2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1 for c in s)


def _ljust(s, width):
    """표시 너비 기준 왼쪽 정렬 (한글 혼용 대응)"""
    return s + ' ' * max(0, width - _dw(s))


def show_menu(fixed_list, today_list):
    """통합 메뉴 출력 및 선택"""
    print()
    hr('=')
    print('  카카오톡 메시지 전송')
    hr('=')

    idx = 1
    item_map = {}  # 번호 → (type, item)

    if fixed_list:
        print()
        print('  [ 고정 메시지 ]')
        hr()
        for item in fixed_list:
            time_label = item['time'] if item['time'] != '즉시' else '즉시'
            print(f"  [{idx}] {_ljust(item['title'], 20)} → {item['chatroom']} / {time_label}")
            item_map[str(idx)] = ('fixed', item)
            idx += 1
    else:
        print('\n  (fixed_messages.txt 에 고정 메시지가 없습니다.)')

    if today_list:
        print()
        print('  [ 자유 메시지 ]')
        hr()
        for item in today_list:
            time_label = item['time'] if item['time'] != '즉시' else '즉시'
            # 제목 우선, 없으면 내용 앞부분
            display_title = item['title'] if item['title'] else (item['message'][:20] + '...' if len(item['message']) > 20 else item['message'])
            print(f"  [{idx}] {_ljust(display_title, 20)} → {item['chatroom']} / {time_label}")
            item_map[str(idx)] = ('today', item)
            idx += 1
    else:
        print('\n  (today_message.txt 에 전송할 메시지가 없습니다.)')
        print('   → free_message.txt 를 메모장으로 열어 내용을 작성하세요.')

    print()
    hr()
    print('  [0] 종료')
    hr()

    while True:
        choice = input('  선택: ').strip()
        if choice == '0':
            return None, None
        if choice in item_map:
            return item_map[choice]
        print('  ⚠ 올바른 번호를 선택하세요.')


# ─────────────────────────────────────────
# --auto-send 모드 (schtasks가 실행)
# ─────────────────────────────────────────
def auto_send_mode():
    """schtasks 예약에 의해 자동 실행되는 모드"""
    if not os.path.exists(PENDING_FILE):
        print('[오류] pending.json 을 찾을 수 없습니다.')
        return

    with open(PENDING_FILE, 'r', encoding='utf-8') as f:
        pending = json.load(f)

    chatroom  = pending.get('chatroom', '')
    message   = pending.get('message', '')
    is_today  = pending.get('is_today', False)

    if not chatroom or not message:
        print('[오류] pending.json 데이터가 잘못되었습니다.')
        return

    print(f'[정보] 예약 전송 실행: {chatroom}')
    ok = send_to_kakao(chatroom, message)

    # 전송 후 파일 정리
    os.remove(PENDING_FILE)
    if ok and is_today:
        reset_free_file()
        print('[정보] free_message.txt 초기화 완료.')

    # schtasks 작업 삭제
    subprocess.run(
        'schtasks /delete /tn "KakaoPersonalMsg" /f',
        shell=True, capture_output=True
    )


# ─────────────────────────────────────────
# 메인
# ─────────────────────────────────────────
def main():
    # 예약 자동 실행 모드
    if '--auto-send' in sys.argv:
        auto_send_mode()
        return

    # txt 파일 파싱
    fixed_list = parse_message_file(FIXED_FILE)
    free_list  = parse_message_file(FREE_FILE)

    if not fixed_list and not free_list:
        print()
        print('  ⚠ 전송할 메시지가 없습니다.')
        print('   fixed_messages.txt 또는 today_message.txt 를 작성해 주세요.')
        input('  엔터를 누르면 종료합니다.')
        return

    # 메뉴 선택
    msg_type, item = show_menu(fixed_list, free_list)
    if item is None:
        return

    # 미리보기
    print(f'\n  --- 전송 내용 확인 ---')
    print(f"  채팅방 : {item['chatroom']}")
    print(f"  시간   : {item['time']}")
    print(f"  메시지 :\n  {item['message'].strip()}")
    hr()

    # 시간 설정: txt의 값 그대로 사용하되 변경 가능
    time_input = input(f"  전송 시각 [{item['time']}] (변경 시 HH:MM 입력, 유지 시 엔터): ").strip()
    if time_input:
        send_time_str = time_input
    else:
        send_time_str = item['time']

    target_time = parse_time_str(send_time_str)
    is_today    = (msg_type == 'today')

    if target_time is None:
        # 즉시 전송
        ok = send_to_kakao(item['chatroom'], item['message'])
        if ok and is_today:
            reset_free_file()
            print('[정보] free_message.txt 초기화 완료.')
    else:
        # 예약 전송 (schtasks)
        print(f'\n  {target_time.strftime("%m/%d %H:%M")} 에 예약합니다...')
        # today 여부를 pending.json에 저장
        pending = {
            'chatroom': item['chatroom'],
            'message':  item['message'],
            'is_today': is_today,
        }
        with open(PENDING_FILE, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False)
        schedule_with_schtasks(item['chatroom'], item['message'], target_time)


if __name__ == '__main__':
    main()
