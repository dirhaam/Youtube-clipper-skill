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

    # 3. Prompt
    prompt = """
    Analyze the following VTT subtitle transcript carefully.
    Identify 10-15 distinct, interesting chapters or highlights that would make great short clips for social media.
    
    IMPORTANT RULES:
    1. Each clip MUST be at least 30-60 seconds long to capture full context
    2. Include the COMPLETE conversation/story - don't cut in the middle of a sentence or idea
    3. Start a few seconds BEFORE the interesting moment (for context)
    4. End a few seconds AFTER the punchline/conclusion (for impact)
    5. Focus on: funny moments, emotional moments, surprising reveals, key insights, or viral-worthy content
    
    Return ONLY a raw JSON array. Do not use Markdown code blocks.
    
    Format:
    [
        {
            "title": "Short catchy title for the clip",
            "start": "00:00:00",
            "end": "00:01:00",
            "reason": "Why this segment is interesting and viral-worthy"
        }
    ]

    Transcript:
    """ + content

    print(f"🤖 Sending request to Kie.ai ({model})...", file=sys.stderr)

    import time
    max_retries = 5
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a professional video editor assistant. You extract viral clips from transcripts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            # Debug: Print raw response type and content
            print(f"🔍 Response Type: {type(response)}", file=sys.stderr)
            try:
                print(f"🔍 Raw Choices: {response.choices}", file=sys.stderr)
            except:
                print("🔍 Could not print choices", file=sys.stderr)

            # Validate response - if invalid, retry
            if not response.choices:
                print(f"⚠️ Response has no choices (Attempt {attempt+1}/{max_retries}). Retrying in {retry_delay}s...", file=sys.stderr)
                print(f"   Debug: {response}", file=sys.stderr)
                time.sleep(retry_delay)
                retry_delay *= 2
                continue # Retry!

            result_text = response.choices[0].message.content.strip()
            
            # Clean up if AI wraps in markdown
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "")
            elif result_text.startswith("```"):
                result_text = result_text.replace("```", "")
                
            try:
                chapters = json.loads(result_text)
                print(f"✅ Successfully generated {len(chapters)} chapters", file=sys.stderr)
                return {
                    "success": True, 
                    "chapters": chapters,
                    "raw_response": result_text
                }
            except json.JSONDecodeError:
                 print(f"⚠️ JSON Decode Error (Attempt {attempt+1}/{max_retries}). Retrying...", file=sys.stderr)
                 print(f"   Raw Text: {result_text[:200]}...", file=sys.stderr)
                 time.sleep(retry_delay)
                 retry_delay *= 2
                 continue # Retry on JSON error too

        except Exception as e:
            error_str = str(e)
            # Check for maintenance or server errors (500, 502, 503, 529)
            if "500" in error_str or "502" in error_str or "503" in error_str or "maintained" in error_str.lower() or "timeout" in error_str.lower():
                if attempt < max_retries - 1:
                    print(f"⚠️ Server Error (Attempt {attempt+1}/{max_retries}). Retrying in {retry_delay}s...", file=sys.stderr)
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
            
            # Non-retryable errors: fail immediately
            print(f"❌ API Error: {error_str}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    # If loop finishes without return (retries exhausted)
    return {"success": False, "error": "Max retries exceeded or API maintenance"}



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
