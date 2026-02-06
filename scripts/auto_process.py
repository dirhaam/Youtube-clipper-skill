#!/usr/bin/env python3
"""
Full Automation Pipeline
Orchestrates the entire process: Download -> Auto-Analyze -> Clip -> Burn
"""

import sys
import os
import json
import time
from pathlib import Path
import subprocess

# Add current directory to path to import other scripts if needed, 
# but we will call them via subprocess to ensure clean execution environments
SCRIPTS_DIR = Path(__file__).parent.resolve()

def run_command_stream(script, args):
    """Run a script and stream output to console. Returns True if success."""
    cmd = ["py", str(SCRIPTS_DIR / script)] + args
    print(f"\n▶️ Running {script}...")
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    try:
        # Popen allows streaming stdout/stderr
        process = subprocess.Popen(
            cmd,
            stdout=sys.stdout,
            stderr=sys.stderr, # Stream directly to console
            env=env,
            encoding='utf-8'
        )
        process.wait()
        
        if process.returncode != 0:
            print(f"❌ Error running {script} (Exit Code: {process.returncode})")
            return False
        return True
    except Exception as e:
        print(f"❌ Failed to launch {script}: {e}")
        return False

def run_command_capture(script, args):
    """Run a script, stream stderr to console, but capture stdout. Returns stdout string or None."""
    cmd = ["py", str(SCRIPTS_DIR / script)] + args
    print(f"\n▶️ Running {script}...")
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    try:
        # Capture stdout (for parsing) but stream stderr (for logs/progress/retries)
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=sys.stderr, # Stream logs to console
            text=True,
            encoding='utf-8',
            env=env,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script}: Exit code {e.returncode}")
        # Not printing stderr here because it was already streamed
        return None

def main():
    if len(sys.argv) < 3:
        print("Usage: python auto_process.py <youtube_url> <api_key> [model] [watermark] [burn_subtitle]")
        sys.exit(1)

    url = sys.argv[1]
    api_key = sys.argv[2]
    model = sys.argv[3] if len(sys.argv) > 3 else "gemini-2.0-flash"
    watermark = sys.argv[4] if len(sys.argv) > 4 else ""
    burn_subtitle_flag = (sys.argv[5].lower() == "true") if len(sys.argv) > 5 else True

    print("🚀 Starting Full Automation Pipeline")
    print(f"Target: {url}")
    print(f"Model: {model}")
    print(f"Burn Subtitle: {burn_subtitle_flag}")

    # Create valid filename safe video ID for folder
    # We'll use the ID we get from yt-dlp
    
    # 1. Get Info & Setup Directory
    print("\n[ Step 1/5 ] Setup & Download Video...")
    try:
        import yt_dlp
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info['id']
            video_title = info['title']
    except Exception as e:
        print(f"❌ Failed to extract info: {e}")
        sys.exit(1)

    # Output Directory: results/<video_id>
    # Sanitize video_title for nice folder name if desired, but ID is safest for uniqueness
    # Let's use ID to avoid path length issues, maybe separate valid title file?
    project_dir = Path("results") / video_id
    project_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📂 Working Directory: {project_dir}")

    # Video path inside project dir
    video_file = project_dir / f"{video_id}.mp4"
    
    if not video_file.exists():
        # Pass output_dir to download_video.py
        # Usage: download_video.py <url> [output_dir]
        run_command_stream("download_video.py", [url, str(project_dir)])
        
        # Check if file exists (it might be mkv or webm if not mp4, but our script forces mp4)
        # But download_video.py forces .mp4 in opts.
        if not video_file.exists():
           # Fallback check for other extensions
           found = list(project_dir.glob(f"{video_id}.*"))
           if found:
               video_file = found[0]
           else:
               print("❌ Video download failed or file not found.")
               sys.exit(1)
    else:
        print("   Video already exists, skipping download.")

    # 2. Download Subtitle
    print("\n[ Step 2/5 ] Downloading Subtitle...")
    lang = 'id' 
    subtitle_file = project_dir / f"{video_id}.{lang}.vtt"
    
    # Usage: download_subtitle.py <url> [lang] [auto] [output_dir]
    run_command_stream("download_subtitle.py", [url, lang, "true", str(project_dir)])
    
    if not subtitle_file.exists():
        found = list(project_dir.glob(f"{video_id}*.vtt"))
        if found:
            subtitle_file = found[0]
            print(f"   Using subtitle: {subtitle_file}")
        else:
            print("❌ No subtitle found. Cannot proceed with auto-analysis.")
            sys.exit(1)

    # 3. Auto Analyze (Kie.ai)
    print("\n[ Step 3/5 ] Analyze Content with AI...")
    
    chapters_cache_file = project_dir / "chapters.json"
    chapters = []
    
    if chapters_cache_file.exists():
        print(f"   Using existing analysis from: {chapters_cache_file}")
        try:
            with open(chapters_cache_file, 'r') as f:
                chapters = json.load(f)
        except Exception as e:
            print(f"   ❌ Failed to load cache: {e}. Re-running analysis.")
    
    if not chapters:
        # auto_mapper.py takes file path
        # Use run_command_capture to get JSON output, but logs will stream to console
        output = run_command_capture("auto_mapper.py", [str(subtitle_file), api_key, model])
        if not output:
             # Error handled inside run_command logging
             sys.exit(1)
        
        # Parse JSON from output
        try:
            # Look for the last valid JSON structure
            json_start = output.find('{')
            json_array_start = output.find('[')
            
            data = None
            try:
                 data = json.loads(output)
            except json.JSONDecodeError:
                 # Try to find object
                 if json_start != -1:
                     snippet = output[json_start:output.rfind('}')+1]
                     try:
                        data = json.loads(snippet)
                     except:
                        pass
            
            if data is None:
                 raise ValueError("Could not extract JSON from output")
    
            # Handle different structures
            if isinstance(data, list):
                 chapters = data
            elif isinstance(data, dict):
                 # Check for explicit failure
                 if not data.get('success', True):
                     print(f"❌ AI Analysis Failed: {data.get('error', 'Unknown Error')}")
                     if 'debug' in data:
                         print(f"Debug Info: {data['debug']}")
                     sys.exit(1)
    
                 if 'chapters' in data:
                     chapters = data['chapters']
                 else:
                     print(f"❌ Unexpected JSON structure: {data.keys()}")
                     print(f"Full Data: {json.dumps(data, indent=2)}")
                     sys.exit(1)
            else:
                 raise ValueError(f"Unknown JSON type: {type(data)}")
                
            # Validate chapters structure
            if not chapters or not isinstance(chapters, list):
                print("❌ No chapters found or invalid format.")
                print(f"Debug Data: {data}")
                sys.exit(1)
                
            # Ensure each chapter is a dict
            for i, ch in enumerate(chapters):
                if isinstance(ch, str):
                    print(f"❌ Invalid chapter format at index {i}: {ch} (Expected dict)")
                    sys.exit(1)
                
            print(f"   ✅ AI identified {len(chapters)} highlights.")
            
            # Save to cache
            with open(chapters_cache_file, 'w') as f:
                json.dump(chapters, f, indent=2)
    
        except Exception as e:
            print(f"❌ Failed to parse AI output: {e}")
            print(f"Raw output: {output}")
            sys.exit(1)


    # 4 & 5. Loop: Clip, Extract, Burn
    print(f"\n[ Step 4-5/5 ] Processing {len(chapters)} Clips...")
    
    processed_files = []
    
    for i, chap in enumerate(chapters):
        idx = i + 1
        # Sanitize title for filename
        title_safe = "".join(x for x in chap['title'] if x.isalnum() or x in " -_").strip()
        base_name = f"{video_id}_clip{idx}_{title_safe}"
        
        # All output inside project_dir
        clip_file = project_dir / f"{base_name}.mp4"
        sub_clip_file = project_dir / f"{base_name}.srt"
        final_file = project_dir / f"{base_name}_final.mp4"
        
        print(f"\n   🎬 Clip {idx}: {chap['title']}")
        print(f"      Range: {chap['start']} - {chap['end']}")
        
        # RESUME: Check if final file exists
        if final_file.exists():
            print(f"      ✅ Final clip already exists. Skipping.")
            processed_files.append({
                "title": chap['title'],
                "file": str(final_file)
            })
            continue

        # Clip Video
        if not run_command_stream("clip_video.py", [str(video_file), chap['start'], chap['end'], str(clip_file)]):
            continue
            
        # Extract Subtitle
        if not run_command_stream("extract_subtitle_clip.py", [str(subtitle_file), chap['start'], chap['end'], str(sub_clip_file)]):
            continue
        
        # Burn Subtitle (optional)
        if burn_subtitle_flag:
            burn_args = [str(clip_file), str(sub_clip_file), str(final_file)]
            if watermark:
                 burn_args.extend(["24", "30", watermark])
            
            if not run_command_stream("burn_subtitles.py", burn_args):
                continue
            
            processed_files.append({
                "title": chap['title'],
                "file": str(final_file)
            })
        else:
            # Skip burning, final file is the clip itself
            print(f"      ⏭️ Skipping burn (disabled). Clip saved as: {clip_file.name}")
            processed_files.append({
                "title": chap['title'],
                "file": str(clip_file)
            })

    # Summary
    print("\n" + "="*60)
    print(f"🎉 Automation Complete! Created {len(processed_files)} clips:")
    print(f"📂 Output Folder: {project_dir.resolve()}")
    print("="*60)
    for p in processed_files:
        print(f"✅ {Path(p['file']).name} ({p['title']})")
    
    # Save a JSON manifest in the project dir
    manifest = {
        "video_id": video_id,
        "video_title": video_title,
        "clips": processed_files
    }
    with open(project_dir / "results.json", "w") as f:
        json.dump(manifest, f, indent=2)

if __name__ == "__main__":
    main()
