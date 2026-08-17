#!/usr/bin/env python3
"""
dlyoutube.py
------------
โปรแกรมสำหรับดาวน์โหลดวิดีโอ (หรือเสียง) จาก YouTube
โดยใช้ไลบรารี yt-dlp ซึ่งเป็นไลบรารีที่ได้รับความนิยมและได้รับการดูแล
(maintain) อย่างต่อเนื่อง รองรับการเปลี่ยนแปลงโครงสร้างของ YouTube ได้ดีกว่า
ไลบรารีรุ่นเก่าอย่าง pytube

การติดตั้งไลบรารีที่จำเป็นก่อนใช้งาน:
    pip install yt-dlp

วิธีใช้งาน (ตัวอย่าง):
    1) ดาวน์โหลดวิดีโอความละเอียดดีที่สุด
       python dlyoutube.py https://www.youtube.com/watch?v=XXXXXXXXXXX

    2) ดาวน์โหลดเฉพาะไฟล์เสียง (mp3)
       python dlyoutube.py https://www.youtube.com/watch?v=XXXXXXXXXXX --audio-only

    3) กำหนดโฟลเดอร์ปลายทางเอง
       python dlyoutube.py https://www.youtube.com/watch?v=XXXXXXXXXXX -o downloads
"""

import argparse   # ใช้สำหรับรับพารามิเตอร์จาก command line
import sys        # ใช้สำหรับจัดการการออกจากโปรแกรมเมื่อเกิดข้อผิดพลาด
import os         # ใช้สำหรับจัดการโฟลเดอร์ปลายทาง

try:
    import yt_dlp
except ImportError:
    # หากยังไม่ได้ติดตั้งไลบรารี yt-dlp ให้แจ้งเตือนผู้ใช้และหยุดโปรแกรม
    print("ไม่พบไลบรารี yt-dlp กรุณาติดตั้งก่อนโดยใช้คำสั่ง:")
    print("    pip install yt-dlp")
    sys.exit(1)


def progress_hook(d):
    """
    ฟังก์ชันนี้จะถูกเรียกโดย yt-dlp ระหว่างกระบวนการดาวน์โหลด
    เพื่อแสดงสถานะความคืบหน้าของการดาวน์โหลดให้ผู้ใช้เห็นแบบเรียลไทม์
    """
    if d['status'] == 'downloading':
        # ดึงค่าเปอร์เซ็นต์ความคืบหน้า (มีรหัสสีจาก yt-dlp ติดมาด้วย จึงต้องตัดออก)
        percent = d.get('_percent_str', 'N/A').strip()
        speed = d.get('_speed_str', 'N/A').strip()
        eta = d.get('_eta_str', 'N/A').strip()
        print(f"\rกำลังดาวน์โหลด... {percent} | ความเร็ว: {speed} | เวลาที่เหลือ: {eta}", end='')
    elif d['status'] == 'finished':
        print("\nดาวน์โหลดเสร็จสิ้น กำลังประมวลผลไฟล์ (post-processing)...")


def download_video(url: str, output_dir: str = "downloads", audio_only: bool = False):
    """
    ฟังก์ชันหลักสำหรับดาวน์โหลดวิดีโอจาก YouTube

    พารามิเตอร์:
        url (str)         : ลิงก์ของวิดีโอ YouTube ที่ต้องการดาวน์โหลด
        output_dir (str)  : โฟลเดอร์ปลายทางที่จะเก็บไฟล์ที่ดาวน์โหลด
        audio_only (bool) : ถ้าเป็น True จะดาวน์โหลดเฉพาะเสียงและแปลงเป็น mp3
    """

    # สร้างโฟลเดอร์ปลายทางหากยังไม่มี
    os.makedirs(output_dir, exist_ok=True)

    # กำหนดค่า options ให้กับ yt-dlp
    # outtmpl กำหนดรูปแบบชื่อไฟล์ที่จะบันทึก โดยใช้ชื่อวิดีโอ (%(title)s) และนามสกุลไฟล์ (%(ext)s)
    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'progress_hooks': [progress_hook],
        'noplaylist': True,   # ดาวน์โหลดเฉพาะวิดีโอเดียว ไม่ดึงทั้งเพลย์ลิสต์
        'quiet': True,        # ปิดข้อความ log ที่ไม่จำเป็นของ yt-dlp เอง
        'no_warnings': True,
    }

    if audio_only:
        # กรณีต้องการเฉพาะไฟล์เสียง: เลือกคุณภาพเสียงที่ดีที่สุด แล้วแปลงเป็น mp3
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        # กรณีต้องการวิดีโอ: เลือกวิดีโอ+เสียงที่ดีที่สุด แล้วรวมเป็นไฟล์ mp4
        ydl_opts.update({
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ดึงข้อมูลวิดีโอก่อน เพื่อแสดงชื่อเรื่องและความยาวให้ผู้ใช้เห็น
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'ไม่ทราบชื่อ')
            duration = info.get('duration', 0)

            print(f"ชื่อวิดีโอ : {title}")
            print(f"ความยาว   : {duration // 60} นาที {duration % 60} วินาที")
            print(f"ปลายทาง   : {os.path.abspath(output_dir)}")
            print("-" * 50)

            # เริ่มกระบวนการดาวน์โหลดจริง
            ydl.download([url])

        print("\nดำเนินการสำเร็จ! ไฟล์ถูกบันทึกเรียบร้อยแล้ว")

    except yt_dlp.utils.DownloadError as e:
        # กรณีลิงก์ผิด, วิดีโอถูกลบ, หรือติดปัญหาการเข้าถึง (private/region lock)
        print(f"\nเกิดข้อผิดพลาดในการดาวน์โหลด: {e}")
        sys.exit(1)
    except Exception as e:
        # ดักจับข้อผิดพลาดอื่น ๆ ที่ไม่คาดคิด
        print(f"\nเกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")
        sys.exit(1)


def main():
    # ตั้งค่า argument parser เพื่อรับค่าจาก command line
    parser = argparse.ArgumentParser(
        description="โปรแกรมดาวน์โหลดวิดีโอ/เสียงจาก YouTube ด้วย yt-dlp"
    )
    parser.add_argument("url", help="ลิงก์ของวิดีโอ YouTube ที่ต้องการดาวน์โหลด")
    parser.add_argument(
        "-o", "--output",
        default="downloads",
        help="โฟลเดอร์ปลายทางสำหรับเก็บไฟล์ (ค่าเริ่มต้น: downloads)"
    )
    parser.add_argument(
        "--audio-only",
        action="store_true",
        help="ดาวน์โหลดเฉพาะไฟล์เสียงและแปลงเป็น mp3"
    )

    args = parser.parse_args()

    download_video(url=args.url, output_dir=args.output, audio_only=args.audio_only)


if __name__ == "__main__":
    main()
