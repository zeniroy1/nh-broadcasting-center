"""
세로로 긴 화면 캡처기 (멀티 모니터 / 드래그 영역 선택)
=====================================================
더블클릭 실행 -> 영역 드래그 -> 자동 스크롤 캡처 -> 전체 이미지(png) 저장
* OCR/엑셀 기능 없음 (가볍고 빠름). 저장된 png를 눈으로 보고 확인.
"""

import os
import sys
import time
import threading
from datetime import datetime
import numpy as np
import cv2
import mss
import pyautogui
import tkinter as tk
from tkinter import messagebox

# Windows 멀티모니터/고해상도(DPI) 정확 인식
try:
    import ctypes
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

pyautogui.FAILSAFE = False


def base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


CONFIG = {
    "scroll_pixels": 500,
    "max_scrolls": 40,
    "scroll_delay": 0.6,
}


def get_virtual_screen():
    with mss.mss() as sct:
        vs = sct.monitors[0]
        mons = sct.monitors[1:]
    info = {"left": vs["left"], "top": vs["top"],
            "width": vs["width"], "height": vs["height"], "monitors": mons}
    return info


# ============================================================
# 영역 선택 오버레이 (모든 모니터를 덮음)
# ============================================================
class RegionSelector:
    def __init__(self, master, virtual):
        self.region = None
        self.start = None
        self.rect_id = None
        self.virtual = virtual

        self.win = tk.Toplevel(master)
        self.win.overrideredirect(True)
        geo = f"{virtual['width']}x{virtual['height']}+{virtual['left']}+{virtual['top']}"
        self.win.geometry(geo)
        self.win.attributes("-alpha", 0.25)
        self.win.attributes("-topmost", True)
        self.win.configure(bg="black")
        self.win.config(cursor="cross")
        self.win.focus_force()

        self.canvas = tk.Canvas(self.win, highlightthickness=0, bg="black",
                                width=virtual["width"], height=virtual["height"])
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_text(
            virtual["width"] // 2, 50,
            text="캡처할 영역을 드래그하세요 (어느 모니터든 가능 / 취소: ESC)",
            fill="white", font=("맑은 고딕", 22),
        )
        self.canvas.bind("<Button-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.win.bind("<Escape>", lambda e: self._close())

    def _press(self, e):
        self.start = (e.x, e.y)
        self.rect_id = self.canvas.create_rectangle(
            e.x, e.y, e.x, e.y, outline="red", width=3)

    def _drag(self, e):
        if self.rect_id:
            self.canvas.coords(self.rect_id, self.start[0], self.start[1], e.x, e.y)

    def _release(self, e):
        x1, y1 = self.start
        x2, y2 = e.x, e.y
        left = min(x1, x2) + self.virtual["left"]
        top = min(y1, y2) + self.virtual["top"]
        w, h = abs(x2 - x1), abs(y2 - y1)
        if w > 20 and h > 20:
            self.region = {"top": top, "left": left, "width": w, "height": h}
        self._close()

    def _close(self):
        self.win.grab_release()
        self.win.destroy()

    def select(self):
        self.win.grab_set()
        self.win.wait_window()
        return self.region


# ============================================================
# 스크롤 캡처 + 이어붙이기
# ============================================================
def capture_scrolling(region, log):
    shots = []
    cx = region["left"] + region["width"] // 2
    cy = region["top"] + region["height"] // 2
    pyautogui.moveTo(cx, cy)
    log("캡처 시작... (브라우저가 활성화돼 있어야 합니다)")
    time.sleep(1.5)
    with mss.mss() as sct:
        prev = None
        for i in range(CONFIG["max_scrolls"]):
            raw = sct.grab(region)
            img = np.array(raw)[:, :, :3]
            shots.append(img)
            log(f"  캡처 {i + 1}/{CONFIG['max_scrolls']}")
            if prev is not None and cv2.absdiff(prev, img).mean() < 1.0:
                log("  페이지 끝 도달, 캡처 종료.")
                shots.pop()
                break
            prev = img.copy()
            pyautogui.scroll(-CONFIG["scroll_pixels"])
            time.sleep(CONFIG["scroll_delay"])
    return shots


def stitch_vertical(shots, max_overlap=400):
    if not shots:
        raise ValueError("캡처된 이미지가 없습니다.")
    stitched = shots[0]
    for nxt in shots[1:]:
        off = _find_overlap(stitched, nxt, max_overlap)
        stitched = np.vstack([stitched, nxt[off:]])
    return stitched


def _find_overlap(top_img, bottom_img, max_overlap):
    h = min(top_img.shape[0], bottom_img.shape[0], max_overlap)
    best_off, best_score = 0, float("inf")
    tg = cv2.cvtColor(top_img, cv2.COLOR_BGR2GRAY)
    bg = cv2.cvtColor(bottom_img, cv2.COLOR_BGR2GRAY)
    for off in range(10, h):
        score = np.mean(np.abs(tg[-off:].astype(int) - bg[:off].astype(int)))
        if score < best_score:
            best_score, best_off = score, off
    return best_off if best_score < 15 else 0


def run_pipeline(region, log, save_path, on_done):
    try:
        shots = capture_scrolling(region, log)
        log("이미지 이어붙이는 중...")
        stitched = stitch_vertical(shots)
        # cv2.imwrite는 한글 경로에서 실패할 수 있어 imencode로 저장
        ok, buf = cv2.imencode(".png", stitched)
        if not ok:
            raise RuntimeError("이미지 인코딩 실패")
        with open(save_path, "wb") as fp:
            fp.write(buf.tobytes())
        log(f"저장 완료: {save_path}")
        log(f"이미지 크기: {stitched.shape[1]}x{stitched.shape[0]}")
        on_done(True, save_path)
    except Exception as e:
        log(f"[오류] {e}")
        on_done(False, None)


# ============================================================
# 메인 GUI
# ============================================================
class App:
    def __init__(self):
        self.region = None
        self.virtual = get_virtual_screen()
        self.root = tk.Tk()
        self.root.title("화면 캡처기")
        self.root.geometry("540x420")
        self.root.attributes("-topmost", True)

        tk.Label(self.root, text="긴 화면 캡처기 (멀티모니터)",
                 font=("맑은 고딕", 15, "bold")).pack(pady=10)
        tk.Label(self.root,
                 text=f"전체 가상화면: {self.virtual['width']}x{self.virtual['height']}",
                 fg="gray").pack()

        self.region_label = tk.Label(self.root, text="영역: 아직 선택 안 됨", fg="gray")
        self.region_label.pack(pady=4)

        tk.Button(self.root, text="1) 영역 선택 (드래그)",
                  font=("맑은 고딕", 12), command=self.select_region,
                  height=2, width=30).pack(pady=8)
        tk.Button(self.root, text="2) 캡처 시작",
                  font=("맑은 고딕", 12), command=self.start,
                  height=2, width=30, bg="#c62828", fg="white").pack(pady=4)

        self.logbox = tk.Text(self.root, height=10, width=64)
        self.logbox.pack(pady=10)

    def log(self, msg):
        self.logbox.insert("end", msg + "\n")
        self.logbox.see("end")
        self.root.update_idletasks()

    def select_region(self):
        sel = RegionSelector(self.root, self.virtual)
        region = sel.select()
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.focus_force()
        if region:
            self.region = region
            r = region
            self.region_label.config(
                text=f"영역: left={r['left']} top={r['top']} "
                     f"w={r['width']} h={r['height']}", fg="black")
            self.log(f"영역 선택됨: {r}")
        else:
            self.region_label.config(text="영역 선택 취소됨", fg="gray")
            self.log("영역 선택이 취소되었습니다.")

    def start(self):
        if not self.region:
            messagebox.showwarning("안내", "먼저 영역을 선택하세요.")
            return
        default_name = "capture_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
        output_dir = os.environ.get("LH_CAPTURE_OUTPUT_DIR") or os.path.join(base_dir(), "inputs")
        os.makedirs(output_dir, exist_ok=True)
        save_path = os.path.join(output_dir, default_name)
        self._save_path = save_path
        self.root.attributes("-topmost", False)
        self.log(f"저장 위치: {save_path}")
        self.log("3초 후 시작합니다. 대상 브라우저를 클릭해 활성화하세요!")
        threading.Thread(target=self._delayed_run, daemon=True).start()

    def _delayed_run(self):
        time.sleep(3)
        run_pipeline(self.region, self.log, self._save_path, self._on_done)

    def _on_done(self, ok, path):
        self.root.attributes("-topmost", True)
        self.root.lift()
        if ok:
            messagebox.showinfo("완료", f"캡처 완료!\n\n{path}")
        else:
            messagebox.showerror("오류", "처리 중 문제가 발생했습니다. 로그를 확인하세요.")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()

