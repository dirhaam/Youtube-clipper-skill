#!/usr/bin/env python3
"""
下载 YouTube 视频和字幕
使用 yt-dlp 下载视频（最高 1080p）和英文字幕
"""

import os
import sys
import json
import shutil
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

try:
    import yt_dlp
except ImportError:
    print("❌ Error: yt-dlp not installed")
    print("Please install: pip install yt-dlp")
    sys.exit(1)

from utils import (
    validate_url,
    sanitize_filename,
    format_file_size,
    get_video_duration_display,
    ensure_directory
)


def download_video(url: str, output_dir: str = None) -> dict:
    """
    下载 YouTube 视频和字幕

    Args:
        url: YouTube URL
        output_dir: 输出目录，默认为当前目录

    Returns:
        dict: {
            'video_path': 视频文件路径,
            'subtitle_path': 字幕文件路径,
            'title': 视频标题,
            'duration': 视频时长（秒）,
            'file_size': 文件大小（字节）
        }

    Raises:
        ValueError: 无效的 URL
        Exception: 下载失败
    """
    # 验证 URL
    if not validate_url(url):
        raise ValueError(f"Invalid YouTube URL: {url}")

    # 设置输出目录
    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)

    output_dir = ensure_directory(output_dir)

    print(f"🎬 开始下载视频...")
    print(f"   URL: {url}")
    print(f"   输出目录: {output_dir}")

    # 获取 FFmpeg 路径
    ffmpeg_path = os.getenv('FFMPEG_PATH')
    if ffmpeg_path:
        print(f"   FFmpeg 路径: {ffmpeg_path}")

    # Check for cookies.txt
    cookie_file = Path("cookies.txt")
    use_cookies = cookie_file.exists()
    if use_cookies:
        print(f"   🍪 Using cookies from: {cookie_file.name}")

    # 配置 yt-dlp 选项
    # Format strategy:
    # - If FFmpeg available: bestvideo+bestaudio (merged by FFmpeg)
    # - If no FFmpeg: use pre-muxed format (has both video+audio in single stream)
    has_ffmpeg = ffmpeg_path or shutil.which('ffmpeg')
    
    if has_ffmpeg:
        # Best quality with FFmpeg merge
        format_str = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best'
    else:
        # Pre-muxed format (video+audio in one stream, no FFmpeg needed)
        # Format 18 = 360p mp4, Format 22 = 720p mp4 (both have audio)
        format_str = 'best[height<=720][ext=mp4]/best[ext=mp4]/best'
        print("   ⚠️ FFmpeg not found - using pre-muxed format (may be lower quality)")
    
    ydl_opts = {
        # 视频格式
        'format': format_str,

        # 输出模板：包含视频 ID（避免特殊字符问题）
        'outtmpl': str(output_dir / '%(id)s.%(ext)s'),

        # 暂时禁用字幕下载（避免 429 错误阻止视频下载）
        'writesubtitles': False,
        'writeautomaticsub': False,
        
        # 不下载缩略图
        'writethumbnail': False,

        # 静默模式（减少输出）
        'quiet': False,
        'no_warnings': False,

        # Anti-bot options
        'sleep_interval': 5,
        'sleep_interval_requests': 2,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',

        # 进度钩子
        'progress_hooks': [_progress_hook],
    }

    if use_cookies:
        ydl_opts['cookiefile'] = str(cookie_file)

    # 如果指定了 FFmpeg 路径，配置 ffmpeg_location
    if ffmpeg_path:
        ydl_opts['ffmpeg_location'] = ffmpeg_path

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 提取信息
            print("\n📊 获取视频信息...")
            info = ydl.extract_info(url, download=False)

            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            video_id = info.get('id', 'unknown')

            print(f"   标题: {title}")
            print(f"   时长: {get_video_duration_display(duration)}")
            print(f"   视频ID: {video_id}")

            # 下载视频
            print(f"\n📥 开始下载...")
            info = ydl.extract_info(url, download=True)

            # 获取下载的文件路径
            video_filename = ydl.prepare_filename(info)
            video_path = Path(video_filename)

            # 查找字幕文件（支持印尼文和英文）
            subtitle_path = None
            subtitle_patterns = ['.id.vtt', '.en.vtt', '.vtt']
            stem = video_path.stem
            for pattern in subtitle_patterns:
                # 尝试 <filename><lang>.vtt 格式
                potential_sub = video_path.parent / f"{stem}{pattern}"
                if potential_sub.exists():
                    subtitle_path = potential_sub
                    break

            # 获取文件大小
            file_size = video_path.stat().st_size if video_path.exists() else 0

            # 验证下载结果
            if not video_path.exists():
                raise Exception("Video file not found after download")

            print(f"\n✅ 视频下载完成: {video_path.name}")
            print(f"   大小: {format_file_size(file_size)}")

            if subtitle_path and subtitle_path.exists():
                print(f"✅ 字幕下载完成: {subtitle_path.name}")
            else:
                print(f"⚠️  未找到英文字幕")
                print(f"   提示：某些视频可能没有字幕或需要自动生成")

            return {
                'video_path': str(video_path),
                'subtitle_path': str(subtitle_path) if subtitle_path else None,
                'title': title,
                'duration': duration,
                'file_size': file_size,
                'video_id': video_id
            }

    except Exception as e:
        print(f"\n❌ 下载失败: {str(e)}")
        raise


def _progress_hook(d):
    """下载进度回调"""
    if d['status'] == 'downloading':
        # 显示下载进度
        if 'downloaded_bytes' in d and 'total_bytes' in d and d['total_bytes']:
            percent = d['downloaded_bytes'] / d['total_bytes'] * 100
            downloaded = format_file_size(d['downloaded_bytes'])
            total = format_file_size(d['total_bytes'])
            speed = d.get('speed', 0)
            speed_str = format_file_size(speed) + '/s' if speed else 'N/A'

            # 使用 \r 实现进度条覆盖
            bar_length = 30
            filled = int(bar_length * percent / 100)
            bar = '█' * filled + '░' * (bar_length - filled)

            print(f"\r   [{bar}] {percent:.1f}% - {downloaded}/{total} - {speed_str}", end='', flush=True)
        elif 'downloaded_bytes' in d:
            # 无总大小信息时，只显示已下载
            downloaded = format_file_size(d['downloaded_bytes'])
            speed = d.get('speed', 0)
            speed_str = format_file_size(speed) + '/s' if speed else 'N/A'
            print(f"\r   下载中... {downloaded} - {speed_str}", end='', flush=True)

    elif d['status'] == 'finished':
        print()  # 换行


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("Usage: python download_video.py <youtube_url> [output_dir]")
        print("\nExample:")
        print("  python download_video.py https://youtube.com/watch?v=Ckt1cj0xjRM")
        print("  python download_video.py https://youtube.com/watch?v=Ckt1cj0xjRM ~/Downloads")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        result = download_video(url, output_dir)

        # 输出 JSON 结果（供其他脚本使用）
        print("\n" + "="*60)
        print("下载结果 (JSON):")
        print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
