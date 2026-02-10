"""
YouTube Clipper - Web GUI
Flask backend for running video processing scripts
"""

import os
import sys
import subprocess
import json
import threading
import uuid
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Base directory
BASE_DIR = Path(__file__).parent.resolve()
SCRIPTS_DIR = BASE_DIR / "scripts"

# Get FFmpeg path from .env
from dotenv import load_dotenv
load_dotenv()
FFMPEG_PATH = os.getenv('FFMPEG_PATH', '')

# Background job tracking
jobs = {}  # {job_id: {"status": "running/done/error", "step": 1, "output": "", "result": None}}


def find_file_path(filename):
    """Find file in results folder by filename. Returns full path or original filename."""
    # If already a full path, return as-is
    if Path(filename).is_absolute() or Path(filename).exists():
        return filename
    
    # Search recursively in results folder
    results_dir = BASE_DIR / 'results'
    if results_dir.exists():
        for file_path in results_dir.rglob(filename):
            return str(file_path)
    
    # Search in BASE_DIR too
    base_match = BASE_DIR / filename
    if base_match.exists():
        return str(base_match)
    
    # Return original (will cause error in script, but with better message)
    return filename


def run_script(script_name, args):
    """Run a Python script and return output"""
    cmd = [sys.executable, str(SCRIPTS_DIR / script_name)] + args
    
    # Force UTF-8 encoding for Python subprocess
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        result = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding='utf-8',  # Explicitly read output as utf-8
            env=env,           # Pass env with UTF-8 setting
            timeout=300        # 5 minute timeout
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout + result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "Timeout: proses terlalu lama", "returncode": -1}
    except Exception as e:
        return {"success": False, "output": str(e), "returncode": -1}


@app.route('/')
def index():
    """Serve main page"""
    return render_template('index.html')


@app.route('/api/download', methods=['POST'])
def download_video():
    """Download video from URL"""
    data = request.json
    url = data.get('url', '')
    if not url:
        return jsonify({"success": False, "output": "URL tidak boleh kosong"})
    
    result = run_script("download_video.py", [url])
    return jsonify(result)


@app.route('/api/download-subtitle', methods=['POST'])
def download_subtitle():
    """Download subtitle only"""
    data = request.json
    url = data.get('url', '')
    lang = data.get('lang', 'id')
    auto = str(data.get('auto', True))
    
    if not url:
        return jsonify({"success": False, "output": "URL tidak boleh kosong"})
    
    result = run_script("download_subtitle.py", [url, lang, auto])
    return jsonify(result)


@app.route('/api/analyze', methods=['POST'])
def analyze_subtitle():
    """Analyze subtitle file"""
    data = request.json
    subtitle_file = data.get('file', '')
    if not subtitle_file:
        return jsonify({"success": False, "output": "File subtitle tidak boleh kosong"})
    
    # Find full path
    subtitle_file = find_file_path(subtitle_file)
    
    result = run_script("analyze_subtitles.py", [subtitle_file])
    return jsonify(result)


@app.route('/api/clip', methods=['POST'])
def clip_video():
    """Clip video segment"""
    data = request.json
    video = data.get('video', '')
    start = data.get('start', '')
    end = data.get('end', '')
    output = data.get('output', '')
    
    if not all([video, start, end, output]):
        return jsonify({"success": False, "output": "Semua field harus diisi"})
    
    # Find file in results folder if only filename provided
    video = find_file_path(video)
    
    # Auto-save output in the same folder as input video
    video_path = Path(video)
    if video_path.exists() and not Path(output).is_absolute():
        output = str(video_path.parent / output)
    
    result = run_script("clip_video.py", [video, start, end, output])
    return jsonify(result)


@app.route('/api/extract-subtitle', methods=['POST'])
def extract_subtitle():
    """Extract subtitle clip"""
    data = request.json
    subtitle = data.get('subtitle', '')
    start = data.get('start', '')
    end = data.get('end', '')
    output = data.get('output', '')
    
    if not all([subtitle, start, end, output]):
        return jsonify({"success": False, "output": "Semua field harus diisi"})
    
    # Find file in results folder if only filename provided
    subtitle = find_file_path(subtitle)
    
    result = run_script("extract_subtitle_clip.py", [subtitle, start, end, output])
    return jsonify(result)


@app.route('/api/burn', methods=['POST'])
def burn_subtitle():
    """Burn subtitle to video"""
    data = request.json
    video = data.get('video', '')
    subtitle = data.get('subtitle', '')
    output = data.get('output', '')
    
    if not all([video, subtitle, output]):
        return jsonify({"success": False, "output": "Semua field harus diisi"})
    
    # Find files in results folder if only filename is provided
    video = find_file_path(video)
    subtitle = find_file_path(subtitle)
    
    # Auto-save output in the same folder as input video
    video_path = Path(video)
    if video_path.exists() and not Path(output).is_absolute():
        output = str(video_path.parent / output)
    
    result = run_script("burn_subtitles.py", [video, subtitle, output])
    return jsonify(result)


@app.route('/api/files', methods=['GET'])
def list_files():
    """List files in directory"""
    path = request.args.get('path', '')
    
    # Default to results folder if no path specified
    if not path or path == '':
        path = str(BASE_DIR / 'results')
    
    try:
        target = Path(path)
        
        # If path doesn't exist, try results folder
        if not target.exists():
            target = BASE_DIR / 'results'
            target.mkdir(parents=True, exist_ok=True)
        
        files = []
        for item in sorted(target.iterdir()):
            if item.name.startswith('.'):
                continue
            files.append({
                "name": item.name,
                "path": str(item),
                "is_dir": item.is_dir(),
                "size": item.stat().st_size if item.is_file() else 0,
                "ext": item.suffix.lower() if item.is_file() else ""
            })
        
        return jsonify({
            "success": True,
            "current_path": str(target),
            "parent_path": str(target.parent) if target != target.parent else None,
            "files": files
        })
    except Exception as e:
        return jsonify({"success": False, "files": [], "error": str(e)})


@app.route('/api/move', methods=['POST'])
def move_file():
    """Move or rename file"""
    data = request.json
    src = data.get('src', '')
    dst = data.get('dst', '')
    
    try:
        Path(src).rename(dst)
        return jsonify({"success": True, "message": f"File dipindahkan ke {dst}"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/api/delete', methods=['POST'])
def delete_file():
    """Delete file"""
    data = request.json
    file_path = data.get('path', '')
    
    try:
        target = Path(file_path)
        if target.is_file():
            target.unlink()
            return jsonify({"success": True, "message": "File dihapus"})
        else:
            return jsonify({"success": False, "message": "Hanya bisa hapus file, bukan folder"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/api/open-folder', methods=['POST'])
def open_folder():
    """Open folder in Windows Explorer"""
    data = request.json
    folder = data.get('path', str(BASE_DIR))
    
    try:
        subprocess.Popen(['explorer', folder])
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/api/auto-map', methods=['POST'])
def auto_map_chapters():
    """Generate chapters using AI"""
    data = request.json
    vtt_file = data.get('file', '')
    api_key = data.get('api_key', '')
    model = data.get('model', 'gemini-2.0-flash') 
    
    # Fallback to .env API Key
    if not api_key:
        api_key = os.getenv('KIE_API_KEY', '')

    if not vtt_file or not api_key:
        return jsonify({"success": False, "output": "File dan API Key harus diisi (atau set KIE_API_KEY di .env)"})
    
    # Find full path
    vtt_file = find_file_path(vtt_file)
    
    # Run auto_mapper.py
    result = run_script("auto_mapper.py", [vtt_file, api_key, model])
    
    # Parse the output which is in JSON format printed to stdout
    try:
        output_json = json.loads(result['output'])
        return jsonify(output_json)
    except Exception:
        return jsonify(result)


@app.route('/api/full-auto', methods=['POST'])
def full_automation():
    """Run full automation pipeline (async)"""
    data = request.json
    url = data.get('url', '')
    api_key = data.get('api_key', '')
    model = data.get('model', 'gemini-2.0-flash')
    watermark = data.get('watermark', '')
    burn_subtitle = data.get('burn_subtitle', True)
    analysis_method = data.get('analysis_method', 'ai') # 'ai' or 'replayed'
    
    # Fallback to .env API Key
    if not api_key:
        api_key = os.getenv('KIE_API_KEY', '')
    
    if not url:
         return jsonify({"success": False, "output": "URL harus diisi"})

    # API key only needed for AI mode
    if analysis_method == 'ai' and not api_key:
        return jsonify({"success": False, "output": "API Key harus diisi untuk mode AI (atau set KIE_API_KEY di .env)"})
    
    # Create job ID
    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {"status": "running", "step": 0, "total_steps": 5, "message": "Memulai...", "output": ""}
    
    # Run in background thread
    def run_job():
        args = [url, api_key, model, watermark, "true" if burn_subtitle else "false", analysis_method]
        cmd = [sys.executable, str(SCRIPTS_DIR / "auto_process.py")] + args
        
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        
        try:
            # Use Popen to stream output
            process = subprocess.Popen(
                cmd,
                cwd=str(BASE_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                env=env
            )
            
            output_lines = []
            for line in iter(process.stdout.readline, ''):
                output_lines.append(line)
                jobs[job_id]["output"] = "".join(output_lines[-50:])  # Keep last 50 lines
                
                # Parse step from output - handle "Step 1/5", "Step 2/5", "Step 3/5", "Step 4-5/5"
                if "[ Step " in line:
                    try:
                        step_part = line.split("Step ")[1].split("/")[0]
                        # Handle "4-5" format
                        if "-" in step_part:
                            step_part = step_part.split("-")[0]  # Take first number
                        jobs[job_id]["step"] = int(step_part)
                    except:
                        pass
                
                # Track clip progress (step 4 has sub-progress per clip)
                if "🎬 Clip" in line:
                    jobs[job_id]["step"] = 4  # Ensure we're at step 4 during clips
                    jobs[job_id]["message"] = line.strip()
                elif "✂️" in line or "剪辑" in line:
                    jobs[job_id]["message"] = "✂️ Clipping video..."
                elif "📝" in line or "提取字幕" in line:
                    jobs[job_id]["message"] = "📝 Extracting subtitle..."
                elif "🔥" in line or "烧录" in line:
                    jobs[job_id]["message"] = "🔥 Burning subtitle..."
                elif "🤖 Sending" in line:
                    jobs[job_id]["step"] = 3
                    jobs[job_id]["message"] = "🤖 Analyzing with AI..."
                elif "Running" in line:
                    jobs[job_id]["message"] = line.strip()
                elif "✅" in line:
                    jobs[job_id]["message"] = line.strip()
                elif "Download" in line and "subtitle" in line.lower():
                    jobs[job_id]["step"] = 2
                    jobs[job_id]["message"] = "📥 Downloading subtitle..."
            
            process.wait()
            
            if process.returncode == 0:
                jobs[job_id]["status"] = "done"
                jobs[job_id]["step"] = 5
                jobs[job_id]["message"] = "✅ Selesai!"
            else:
                jobs[job_id]["status"] = "error"
                jobs[job_id]["message"] = "❌ Gagal!"
                
        except Exception as e:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["message"] = f"❌ Error: {str(e)}"
    
    thread = threading.Thread(target=run_job)
    thread.daemon = True
    thread.start()
    
    return jsonify({"success": True, "job_id": job_id, "message": "Job started"})


@app.route('/api/job-status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get status of a background job"""
    if job_id not in jobs:
        return jsonify({"success": False, "error": "Job not found"})
    
    job = jobs[job_id]
    return jsonify({
        "success": True,
        "status": job["status"],
        "step": job["step"],
        "total_steps": job["total_steps"],
        "message": job["message"],
        "output": job["output"]
    })


if __name__ == '__main__':
    print("=" * 60)
    print("YouTube Clipper GUI")
    print("Buka browser: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, port=5000, threaded=True)
