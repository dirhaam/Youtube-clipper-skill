#!/usr/bin/env python3
"""
Auto-Generate Chapters using Kie.ai (OpenAI Compatible)
"""

import sys
import json
import os
from openai import OpenAI
from utils import time_to_seconds

def generate_chapters(vtt_file, api_key, model="gpt-4o", base_url="https://api.kie.ai/v1"):
    # 1. Read Subtitle File
    try:
        with open(vtt_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {"success": False, "error": f"Failed to read file: {str(e)}"}

    # Limit content length to avoid token limits (take first 15000 chars approx 20-30 mins or shorten)
    # For meaningful analysis, we might need the whole thing, but let's truncate for safety if too huge
    if len(content) > 30000:
        content = content[:30000] + "\n...[truncated]..."

    # 2. Setup Client
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    # Load config (optional target duration, but prioritize content)
    from dotenv import load_dotenv
    load_dotenv()
    target_duration_env = os.getenv("TARGET_CHAPTER_DURATION")
    
    # If environment variable is set, use it as a "soft" target, otherwise default to dynamic
    if target_duration_env:
        duration_guideline = f"aim for approximately {target_duration_env} seconds, but prioritize the complete story arc."
    else:
        duration_guideline = "Length should be determined by the content itself (typically 15s to 3 mins). Do not cut off early."

    # 3. Prompt
    prompt = f"""
    You are an expert video editor specializing in YouTube Shorts, TikTok, and Instagram Reels.
    Your task is to analyze the following transcript and extract ALL clips that have high viral potential (Score > 7).
    
    Do NOT limit the number of clips. If there are 20 good moments, extract all 20.
    
    Look for:
    - 🤣 Laughter, funny jokes, or fails (Look for [Laughter] tags or haha)
    - ⚡ Fast-paced, passionate speech or arguments
    - 🤯 Mind-blowing facts or realizations
    - 🔥 Heated debates or controversial opinions
    - 😢 Emotional or inspiring stories
    
    IMPORTANT RULES:
    1. **Hook**: The clip MUST start with a strong hook (an interesting sentence or action) to grab attention immediately.
    2. **Context**: Include just enough context before the hook so it makes sense, but keep it tight.
    3. **Payoff**: The clip MUST end after the punchline, reaction, or conclusion. Do not cut early!
    4. **Duration**: {duration_guideline}
    5. **Virality Score**: Rate each clip from 1-10 based on its potential to go viral. BONUS points for heavy laughter or very high energy speech.
    
    Return ONLY a raw JSON array. Do not use Markdown code blocks.
    
    Format:
    [
        {{
            "title": "Clickbait Title (e.g. 'He Actually Said This?!')",
            "start": "HH:MM:SS",
            "end": "HH:MM:SS",
            "reason": "Why this is viral (Hook/Payoff)",
            "score": 9.5
        }}
    ]

    Transcript:
    """ + content

    print(f"🤖 Sending request to Kie.ai ({model})...", file=sys.stderr)

    import time
    max_retries = 3 # Reduced retries for speed
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            # Construct messages properly
            messages = [
                {"role": "system", "content": "You are a viral content expert. You identify high-retention segments."},
                {"role": "user", "content": prompt}
            ]

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.4 # Slightly higher for creativity
            )
            
            # Debug
            # print(f"🔍 Response: {response}", file=sys.stderr)

            if not response.choices:
                print(f"⚠️ Response has no choices (Attempt {attempt+1}/{max_retries}).", file=sys.stderr)
                time.sleep(retry_delay)
                continue

            result_text = response.choices[0].message.content.strip()
            
            # Clean up Markdown
            result_text = result_text.replace("```json", "").replace("```", "")
                
            try:
                chapters = json.loads(result_text)
                
                # Filter low quality clips if possible (e.g. score < 7)
                # But let's keep all for now and just sort by score
                if isinstance(chapters, list) and len(chapters) > 0 and 'score' in chapters[0]:
                    chapters.sort(key=lambda x: x.get('score', 0), reverse=True)
                
                print(f"✅ Successfully extracted {len(chapters)} viral clips", file=sys.stderr)
                return {
                    "success": True, 
                    "chapters": chapters,
                    "raw_response": result_text
                }
            except json.JSONDecodeError:
                 print(f"⚠️ JSON Decode Error. Text: {result_text[:100]}...", file=sys.stderr)
                 time.sleep(retry_delay)
                 continue 

        except Exception as e:
            error_str = str(e)
            print(f"❌ API Error: {error_str}", file=sys.stderr)
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            return {"success": False, "error": str(e)}

    return {"success": False, "error": "Max retries exceeded"}



if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python auto_mapper.py <vtt_file> <api_key> [model] [base_url]")
        sys.exit(1)

    vtt_file = sys.argv[1]
    api_key = sys.argv[2]
    model = sys.argv[3] if len(sys.argv) > 3 else "gemini-2.5-flash"
    
    # Logic to switch between Kie.ai and Perplexity
    is_perplexity = "sonar" in model or "r1" in model
    
    if len(sys.argv) > 4:
        # Explicit base URL override from args
        base_url = sys.argv[4]
    else:
        if is_perplexity:
            base_url = "https://api.perplexity.ai"
            # Override API Key if using Perplexity (unless passed explicitly as arg, but arg is generic)
            # The auto_process.py passes sys.argv[2] as api_key. 
            # If user selected Perplexity in GUI, we should probably handle key swapping here 
            # OR ensuring auto_process passes the right key. 
            # For simplicity: check env for PERPLEXITY_API_KEY if model is perplexity
            from dotenv import load_dotenv
            load_dotenv()
            pplx_key = os.getenv("PERPLEXITY_API_KEY")
            if pplx_key:
                print("🔑 Switching to PERPLEXITY_API_KEY from .env", file=sys.stderr)
                api_key = pplx_key
        else:
            # KIE.ai specific pattern
            base_url = f"https://api.kie.ai/{model}/v1"

    print(f"🔗 Base URL: {base_url}", file=sys.stderr)
    result = generate_chapters(vtt_file, api_key, model, base_url)
    print(json.dumps(result, indent=2))
