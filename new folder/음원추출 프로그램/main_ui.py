import sys
import os
import json
import yt_dlp
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLineEdit, QProgressBar, QLabel, QFrame, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QIcon

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def get_settings_path():
    appdata = os.getenv('APPDATA')
    if not appdata:
        appdata = os.path.expanduser('~')
    settings_dir = os.path.join(appdata, 'YoutubeAudioRadio')
    if not os.path.exists(settings_dir):
        try: os.makedirs(settings_dir)
        except: pass
    return os.path.join(settings_dir, 'settings.json')

def load_target_dir():
    path = get_settings_path()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                saved_dir = data.get('target_dir')
                if saved_dir and os.path.exists(saved_dir): return saved_dir
        except: pass
    desktop = os.path.join(os.path.join(os.environ.get('USERPROFILE', '')), 'Desktop') 
    if os.path.exists(desktop): return desktop
    return os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

def save_target_dir(target_dir):
    path = get_settings_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'target_dir': target_dir}, f)
    except: pass

class CancelDownload(Exception):
    pass

class DownloadThread(QThread):
    progress_signal = Signal(str, float, str)
    
    def __init__(self, url, output_dir, start_t=None, end_t=None):
        super().__init__()
        self.url = url
        self.output_dir = output_dir
        self.start_t = start_t
        self.end_t = end_t
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True

    def my_hook(self, d):
        if self.is_cancelled:
            raise CancelDownload("사용자가 다운로드를 중지했습니다.")
            
        if d['status'] == 'finished':
            self.progress_signal.emit('processing', 100, "다운로드 완료! 오디오 변환 중...")
        elif d['status'] == 'downloading':
            p_str = d.get('_percent_str', '0%').strip()
            import re
            p_str = re.sub(r'\x1b\[[0-9;]*m', '', p_str)
            p_str = p_str.replace('%', '')
            try: p = float(p_str)
            except: p = 0.0
            self.progress_signal.emit('downloading', p, f"다운로드 중... {p}%")

    def run(self):
        try: current_dir = sys._MEIPASS
        except AttributeError: current_dir = os.path.dirname(os.path.abspath(__file__))
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            'progress_hooks': [self.my_hook],
            'ffmpeg_location': current_dir,
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
        }
        
        if self.start_t is not None or self.end_t is not None:
            from yt_dlp.utils import download_range_func
            s = self.start_t if self.start_t is not None else 0
            e = self.end_t if self.end_t is not None else float('inf')
            ydl_opts['download_ranges'] = download_range_func(None, [(s, e)])
        
        try:
            self.progress_signal.emit('downloading', 0, "정보 가져오는 중...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            if not self.is_cancelled:
                self.progress_signal.emit('success', 100, "추출 완료!")
        except Exception as e:
            if isinstance(e, CancelDownload):
                self.progress_signal.emit('cancelled', 0, "추출이 중지되었습니다.")
            elif hasattr(e, 'orig_exc') and isinstance(getattr(e, 'orig_exc', None), CancelDownload):
                self.progress_signal.emit('cancelled', 0, "추출이 중지되었습니다.")
            elif self.is_cancelled:
                self.progress_signal.emit('cancelled', 0, "추출이 중지되었습니다.")
            else:
                self.progress_signal.emit('error', 0, str(e))

class RadioExtractorUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("엔틱 라디오 음원 추출기 (Silver & Black)")
        self.setFixedSize(600, 380) 
        self.setStyleSheet("background-color: #121212;")
        
        icon_path = resource_path("radio_icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)
        
        dial_frame = QFrame()
        dial_frame.setFixedHeight(125) 
        dial_frame.setStyleSheet("QFrame { background-color: #F4F4F5; border: 3px solid #A1A1AA; border-radius: 6px; }")
        dial_layout = QVBoxLayout(dial_frame)
        dial_layout.setContentsMargins(15, 12, 15, 12)
        dial_layout.setSpacing(8)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("🎵 유튜브/미디어 URL을 입력하세요 (예: https://youtube.com/...)")
        self.url_input.setStyleSheet("QLineEdit { background-color: #FFFFFF; color: #18181B; border: 1px solid #D4D4D8; border-radius: 4px; padding: 6px 10px; font-family: 'Malgun Gothic', sans-serif; font-size: 14px; font-weight: bold; } QLineEdit:focus { border: 2px solid #52525B; }")
        
        time_layout = QHBoxLayout()
        time_layout.setSpacing(8)
        
        time_label = QLabel("⏱️ 구간 설정:")
        time_label.setStyleSheet("color: #18181B; font-weight: bold; font-family: 'Malgun Gothic';")
        
        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("시작 (예: 01:30)")
        self.start_input.setFixedWidth(100)
        self.start_input.setStyleSheet("QLineEdit { background-color: #FFFFFF; color: #18181B; border: 1px solid #D4D4D8; border-radius: 4px; padding: 4px; font-family: 'Malgun Gothic'; font-size: 12px; }")
        
        wave_label = QLabel("~")
        wave_label.setStyleSheet("color: #18181B; font-weight: bold;")
        
        self.end_input = QLineEdit()
        self.end_input.setPlaceholderText("종료 (예: 02:45)")
        self.end_input.setFixedWidth(100)
        self.end_input.setStyleSheet("QLineEdit { background-color: #FFFFFF; color: #18181B; border: 1px solid #D4D4D8; border-radius: 4px; padding: 4px; font-family: 'Malgun Gothic'; font-size: 12px; }")
        
        hint_label = QLabel("(비워두면 영상 전체)")
        hint_label.setStyleSheet("color: #71717A; font-size: 11px; font-family: 'Malgun Gothic';")
        
        self.clear_time_btn = QPushButton("✖")
        self.clear_time_btn.setFixedSize(24, 24)
        self.clear_time_btn.setToolTip("시간 초기화")
        self.clear_time_btn.setCursor(Qt.PointingHandCursor)
        self.clear_time_btn.setStyleSheet("QPushButton { background-color: #E4E4E7; color: #52525B; border: 1px solid #D4D4D8; border-radius: 4px; font-weight: bold; font-size: 12px; } QPushButton:hover { background-color: #FEE2E2; color: #EF4444; border: 1px solid #FCA5A5; } QPushButton:pressed { background-color: #FECACA; }")
        self.clear_time_btn.clicked.connect(self.clear_time_inputs)
        
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.start_input)
        time_layout.addWidget(wave_label)
        time_layout.addWidget(self.end_input)
        time_layout.addWidget(self.clear_time_btn)
        time_layout.addWidget(hint_label)
        time_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("대기 중...")
        self.progress_bar.setFixedHeight(22)
        self.progress_bar.setStyleSheet("QProgressBar { background-color: #E4E4E7; color: #000000; border: 1px solid #A1A1AA; border-radius: 4px; text-align: center; font-weight: bold; } QProgressBar::chunk { background-color: #3F3F46; border-radius: 3px; }")
        
        dial_layout.addWidget(self.url_input)
        dial_layout.addLayout(time_layout)
        dial_layout.addWidget(self.progress_bar)
        
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)
        
        badge_layout = QVBoxLayout()
        badge_layout.addStretch()
        self.status_badge = QLabel()
        self.status_badge.setFixedSize(24, 24)
        self.set_badge_status("ready")
        badge_layout.addWidget(self.status_badge)
        
        grille_layout = QVBoxLayout()
        grille_layout.setSpacing(6)
        grille_layout.setContentsMargins(10, 5, 10, 0)
        for _ in range(12):
            line = QFrame()
            line.setFixedHeight(3)
            line.setStyleSheet("background-color: #18181B; border-bottom: 1px solid #27272A;")
            grille_layout.addWidget(line)
        grille_layout.addStretch()
        
        self.extract_btn = QPushButton("추출")
        self.extract_btn.setFixedSize(90, 90)
        self.extract_btn.setFont(QFont("Malgun Gothic", 16, QFont.Bold))
        self.extract_btn.setCursor(Qt.PointingHandCursor)
        self.reset_extract_btn_style()
        
        self.folder_btn = QPushButton("위치")
        self.folder_btn.setFixedSize(56, 56)
        self.folder_btn.setFont(QFont("Malgun Gothic", 11, QFont.Bold))
        self.folder_btn.setCursor(Qt.PointingHandCursor)
        self.folder_btn.setStyleSheet("QPushButton { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #D4D4D8, stop:1 #71717A); color: #18181B; border: 3px solid #52525B; border-radius: 28px; } QPushButton:hover { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #E4E4E7, stop:1 #A1A1AA); } QPushButton:disabled { background-color: #3F3F46; color: #71717A; border: 3px solid #27272A; }")
        
        knob_wrapper = QVBoxLayout()
        knob_wrapper.setAlignment(Qt.AlignCenter)
        knob_wrapper.addWidget(self.extract_btn, alignment=Qt.AlignRight)
        knob_wrapper.addWidget(self.folder_btn, alignment=Qt.AlignRight)
        
        bottom_layout.addLayout(badge_layout, 1)
        bottom_layout.addLayout(grille_layout, 5)
        bottom_layout.addLayout(knob_wrapper, 2)
        
        main_layout.addWidget(dial_frame)
        main_layout.addLayout(bottom_layout)
        
        self.folder_btn.clicked.connect(self.select_folder)
        self.extract_btn.clicked.connect(self.start_extraction)
        
        self.target_dir = load_target_dir()
        self.thread = None
        self.is_extracting = False

    def reset_extract_btn_style(self):
        self.extract_btn.setStyleSheet("QPushButton { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #E4E4E7, stop:1 #A1A1AA); color: #18181B; border: 4px solid #71717A; border-radius: 45px; } QPushButton:hover { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #F4F4F5, stop:1 #D4D4D8); border: 4px solid #A1A1AA; } QPushButton:pressed { background-color: #A1A1AA; border: 4px solid #52525B; color: #000000; } QPushButton:disabled { background-color: #3F3F46; color: #71717A; border: 4px solid #27272A; }")

    def set_stop_btn_style(self):
        self.extract_btn.setStyleSheet("QPushButton { background-color: #EF4444; color: #FFFFFF; border: 4px solid #B91C1C; border-radius: 45px; } QPushButton:hover { background-color: #F87171; border: 4px solid #EF4444; } QPushButton:pressed { background-color: #B91C1C; border: 4px solid #991B1B; color: #000000; } QPushButton:disabled { background-color: #7F1D1D; color: #FCA5A5; border: 4px solid #450A0A; }")

    def set_badge_status(self, status):
        if status == "ready": color, border = "#52525B", "#3F3F46"
        elif status in ["downloading", "processing"]: color, border = "#EF4444", "#B91C1C"
        elif status == "success": color, border = "#10B981", "#047857"
        elif status == "error": color, border = "#F59E0B", "#B45309"
        else: color, border = "#52525B", "#3F3F46"
        self.status_badge.setStyleSheet(f"QLabel {{ background-color: {color}; border: 2px solid {border}; border-radius: 4px; }}")

    def clear_time_inputs(self):
        self.start_input.clear()
        self.end_input.clear()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "저장할 폴더를 선택하세요", self.target_dir)
        if folder:
            self.target_dir = folder
            save_target_dir(folder)
            QMessageBox.information(self, "폴더 변경", f"저장 위치가 항상 기기억됩니다:\n{self.target_dir}")

    def update_progress(self, status, percent, message):
        self.set_badge_status(status)
        self.progress_bar.setValue(int(percent))
        self.progress_bar.setFormat(message)
        
        if status in ['success', 'error', 'cancelled']:
            self.is_extracting = False
            self.extract_btn.setText("추출")
            self.reset_extract_btn_style()
            self.extract_btn.setEnabled(True)
            self.folder_btn.setEnabled(True)
            self.url_input.setEnabled(True)
            self.start_input.setEnabled(True)
            self.end_input.setEnabled(True)
            
            if status == "success":
                QMessageBox.information(self, "추출 완료", "음원이 성공적으로 저장되었습니다!")
                self.progress_bar.setFormat("대기 중...")
            elif status == "error":
                QMessageBox.warning(self, "오류 발생", f"추출 중 문제가 발생했습니다:\n{message}")
                self.progress_bar.setFormat("오류 발생")
            elif status == "cancelled":
                QMessageBox.information(self, "추출 중지", "추출이 안전하게 중지되었습니다.")
                self.progress_bar.setFormat("대기 중...")
            
            if status in ["success", "cancelled"]:
                self.progress_bar.setValue(0)
                self.set_badge_status("ready")

    def start_extraction(self):
        if self.is_extracting:
            if self.thread and self.thread.isRunning():
                self.thread.cancel()
                self.extract_btn.setEnabled(False)
                self.progress_bar.setFormat("중지하는 중...")
            return

        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "입력 오류", "유튜브 또는 미디어 URL을 먼저 입력해주세요.")
            return
            
        if "threads.com" in url or "threads.net" in url:
            url = url.replace("threads.com", "threads.net")
            url = url.split("/media")[0]
            
        def parse_time(t_str):
            if not t_str: return None
            try:
                if ':' in t_str:
                    parts = t_str.split(':')
                    if len(parts) == 2: return float(parts[0])*60 + float(parts[1])
                    if len(parts) == 3: return float(parts[0])*3600 + float(parts[1])*60 + float(parts[2])
                return float(t_str)
            except:
                return -1

        s_val = parse_time(self.start_input.text().strip())
        e_val = parse_time(self.end_input.text().strip())
        
        if s_val == -1 or e_val == -1:
            QMessageBox.warning(self, "시간 입력 오류", "시간은 '분:초' (예: 01:30) 또는 '초' (예: 90) 형식으로 정확히 입력해주세요.")
            return
            
        if s_val is not None and e_val is not None and s_val >= e_val:
            QMessageBox.warning(self, "시간 입력 오류", "종료 시간이 시작 시간보다 나중이어야 합니다!")
            return

        self.is_extracting = True
        self.extract_btn.setText("중지")
        self.set_stop_btn_style()
        self.folder_btn.setEnabled(False)
        self.url_input.setEnabled(False)
        self.start_input.setEnabled(False)
        self.end_input.setEnabled(False)
        
        self.set_badge_status("downloading")
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("초기화 중...")
        
        self.thread = DownloadThread(url, self.target_dir, s_val, e_val)
        self.thread.progress_signal.connect(self.update_progress)
        self.thread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = RadioExtractorUI()
    window.show()
    sys.exit(app.exec())
