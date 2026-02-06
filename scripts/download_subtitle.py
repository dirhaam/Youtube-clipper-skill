#!/usr/bin/env python3
"""
Download YouTube Subtitles Only
"""

import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import yt_dlp
except ImportError:
    print("❌ Error: yt-dlp not installed")
    sys.exit(1)

def download_subtitle(url, lang='id', auto=True, output_dir=None):
    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)

    print(f"🎬 Downloading subtitle for: {url}")
    print(f"   Language: {lang}")
    print(f"   Auto-generated: {auto}")

    # Check for cookies.txt in root directory
    cookie_file = Path("cookies.txt")
    use_cookies = cookie_file.exists()
    if use_cookies:
        print(f"   🍪 Using cookies from: {cookie_file.name}")

    ydl_opts = {
        'skip_download': True,  # Don't download video
        'writesubtitles': True,
        'writeautomaticsub': auto,
        'subtitleslangs': [lang],
        'subtitlesformat': 'vtt',
        'outtmpl': str(output_dir / '%(id)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        # Anti-bot options
        'sleep_interval': 5,
        'sleep_interval_requests': 2,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        
        # TRICK: Use Android client to bypass subtitle rate limits
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        }
    }
    
    if use_cookies:
        ydl_opts['cookiefile'] = str(cookie_file)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_id = info.get('id', 'unknown')
            title = info.get('title', 'Unknown')
            
            print(f"\n✅ Subtitle download complete for: {title}")
            return {
                "success": True,
                "video_id": video_id,
                "title": title
            }
    except Exception as e:
        print(f"\n⚠️ Primary download failed: {str(e)}")
        
        # Fallback: Try downloading AUTOMATIC English subs if manual ID failed
        if lang == 'id' and '429' not in str(e): # If 429, switching lang might not help, but switching client might have failed.
             print("   🔄 Trying fallback to auto-generated English...")
             ydl_opts['subtitleslangs'] = ['en']
             ydl_opts['writeautomaticsub'] = True
             try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(url, download=True)
                return {"success": True, "note": "Fallback to English"}
             except:
                pass
        
        # If it was 429 or fallback failed
        print(f"\n❌ Final Error: Could not download subtitles.")
        raise

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python download_subtitle.py <url> [lang] [auto] [output_dir]")
        sys.exit(1)

    url = sys.argv[1]
    lang = sys.argv[2] if len(sys.argv) > 2 else 'id'
    auto = sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else True
    output_dir = sys.argv[4] if len(sys.argv) > 4 else None

    # Handle 'all' language case for auto-sub
    if lang == 'all':
        # logic handled by yt-dlp, but we usually want specific logic. 
        # For simplicity in this script, we stick to passing what user gave, 
        # but the GUI usually sends 'id', 'en', or 'ja'.
        pass

    try:
        download_subtitle(url, lang, auto, output_dir)
    except Exception as e:
        sys.exit(1)
