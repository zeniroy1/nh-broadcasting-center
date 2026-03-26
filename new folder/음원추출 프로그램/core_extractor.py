import sys
import os
import yt_dlp

def my_hook(d):
    if d['status'] == 'finished':
        print('\n[DOWNLOAD DONE] 다운로드 완료! 오디오(mp3) 변환을 시작합니다...')
    elif d['status'] == 'downloading':
        p = d.get('_percent_str', 'N/A')
        print(f"진행 상태: {p}\r", end='')

def download_audio(url, output_dir):
    print(f"\n[TARGET URL] {url}")
    print(f"[OUTPUT DIR] {output_dir}")
    print("-" * 50)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'progress_hooks': [my_hook],
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print("\n[SUCCESS] 음원 추출이 폴더에 정상적으로 완료되었습니다.")
        return True
    except Exception as e:
        print(f"\n[ERROR] 추출 중 문제가 발생했습니다: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        # Example test URL: NoCopyrightSounds NCS release
        test_url = "https://www.youtube.com/watch?v=K4DyBUG242c"
        print("URL이 제공되지 않아 샘플 테스트 URL로 추출을 시도합니다.")
        
    out_dir = os.path.dirname(os.path.abspath(__file__))
    download_audio(test_url, out_dir)
