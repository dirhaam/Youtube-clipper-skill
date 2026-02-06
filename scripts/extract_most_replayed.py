"""
YouTube Most Replayed Heatmap Extractor
Uses LemnosLife open API to get Most Replayed data without browser scraping
"""

import sys
import json
import re
import urllib.request
import urllib.error

def get_video_id(url):
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:v=|/v/|youtu\.be/|/embed/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_video_duration(video_id):
    """Get video duration using yt-dlp"""
    try:
        import yt_dlp
        url = f"https://www.youtube.com/watch?v={video_id}"
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('duration', 0)
    except Exception as e:
        print(f"⚠️ Could not get duration: {e}", file=sys.stderr)
        return 0

def fetch_most_replayed(video_id):
    """
    Fetch Most Replayed data from LemnosLife API.
    Returns heatMarkers array or None.
    """
    api_url = f"https://yt.lemnoslife.com/videos?part=mostReplayed&id={video_id}"
    
    print(f"🔍 Fetching Most Replayed data...", file=sys.stderr)
    print(f"   API: {api_url}", file=sys.stderr)
    
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        
        # Check response structure
        if 'items' in data and len(data['items']) > 0:
            item = data['items'][0]
            if 'mostReplayed' in item and item['mostReplayed']:
                markers = item['mostReplayed'].get('markers', [])
                if markers:
                    print(f"   ✅ Found {len(markers)} heatmap markers!", file=sys.stderr)
                    return markers
        
        print("   ⚠️ No Most Replayed data found (video may not have enough views)", file=sys.stderr)
        return None
        
    except urllib.error.HTTPError as e:
        print(f"   ❌ API Error: {e.code} {e.reason}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}", file=sys.stderr)
        return None

def find_peak_segments(markers, video_duration, num_peaks=10, min_duration=15):
    """
    Find peak replay segments from heatMarkers.
    Each marker has: startMillis, intensityScoreNormalized
    """
    if not markers:
        return []
    
    # Sort by intensity (highest first)
    sorted_markers = sorted(markers, key=lambda x: x.get('intensityScoreNormalized', 0), reverse=True)
    
    segments = []
    used_times = []
    
    for marker in sorted_markers:
        if len(segments) >= num_peaks:
            break
            
        start_ms = marker.get('startMillis', 0)
        intensity = marker.get('intensityScoreNormalized', 0)
        duration_ms = marker.get('durationMillis', 0)
        
        time_sec = start_ms / 1000
        
        # Check if this time overlaps with already selected segments
        is_overlapping = False
        for used_start, used_end in used_times:
            if not (time_sec >= used_end or time_sec + min_duration <= used_start):
                is_overlapping = True
                break
        
        if is_overlapping:
            continue
        
        # Create segment around this peak
        seg_start = max(0, time_sec - 2)  # Start 2 seconds before peak
        if video_duration > 0:
            seg_end = min(video_duration, time_sec + min_duration)
        else:
            seg_end = time_sec + min_duration
        
        segments.append({
            'title': f'Peak Moment #{len(segments)+1}',
            'start': format_timestamp(seg_start),
            'end': format_timestamp(seg_end),
            'intensity': round(intensity, 3),
            'peak_time': format_timestamp(time_sec),
            'reason': f'Most Replayed (intensity: {intensity:.1%})'
        })
        
        used_times.append((seg_start, seg_end))
    
    # Sort by time order
    segments.sort(key=lambda x: x['start'])
    
    # Re-number titles
    for i, seg in enumerate(segments):
        seg['title'] = f'Peak Moment #{i+1}'
    
    return segments

def format_timestamp(seconds):
    """Convert seconds to HH:MM:SS.mmm format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_most_replayed.py <youtube_url> [num_peaks] [min_duration]")
        print("  num_peaks: number of top segments to extract (default: 10)")
        print("  min_duration: minimum clip duration in seconds (default: 15)")
        sys.exit(1)
    
    url = sys.argv[1]
    num_peaks = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    min_duration = int(sys.argv[3]) if len(sys.argv) > 3 else 15
    
    # Extract video ID
    video_id = get_video_id(url)
    if not video_id:
        print(f"❌ Could not extract video ID from: {url}", file=sys.stderr)
        result = {"success": False, "error": "Invalid YouTube URL"}
        print(json.dumps(result))
        sys.exit(1)
    
    print(f"📊 Video ID: {video_id}", file=sys.stderr)
    
    # Get video duration
    duration = get_video_duration(video_id)
    if duration:
        print(f"   Duration: {format_timestamp(duration)}", file=sys.stderr)
    
    # Fetch heatmap data
    markers = fetch_most_replayed(video_id)
    
    if not markers:
        print("❌ No Most Replayed data available for this video.", file=sys.stderr)
        result = {"success": False, "error": "No Most Replayed data found"}
        print(json.dumps(result))
        sys.exit(1)
    
    # Find peak segments
    segments = find_peak_segments(markers, duration, num_peaks, min_duration)
    
    if segments:
        print(f"\n✅ Found {len(segments)} peak segments!", file=sys.stderr)
        for i, seg in enumerate(segments):
            print(f"   {i+1}. {seg['start']} - {seg['end']} ({seg['reason']})", file=sys.stderr)
        
        result = {
            "success": True,
            "video_id": video_id,
            "video_duration": format_timestamp(duration) if duration else "unknown",
            "chapters": segments  # Use 'chapters' to match auto_mapper format
        }
    else:
        result = {"success": False, "error": "Could not identify peak segments"}
    
    # Output JSON to stdout (for piping to other scripts)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
