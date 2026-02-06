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
    Analyze the following VTT subtitle transcript.
    Identify 3-5 distinct, interesting chapters or highlights.
    Return ONLY a raw JSON array. Do not use Markdown code blocks.
    
    Format:
    [
        {
            "title": "Chapter Title",
            "start": "00:00:00",
            "end": "00:00:00",
            "reason": "Why this is interesting"
        }
    ]

    Transcript:
    """ + content

    print(f"🤖 Sending request to Kie.ai ({model})...", file=sys.stderr)

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

        if not response.choices:
            print("❌ Error: Response has no choices", file=sys.stderr)
            return {"success": False, "error": "API returned no choices", "debug": str(response)}

        result_text = response.choices[0].message.content.strip()
        
        # Clean up if AI wraps in markdown
        if result_text.startswith("```json"):
            result_text = result_text.replace("```json", "").replace("```", "")
        elif result_text.startswith("```"):
            result_text = result_text.replace("```", "")
            
        chapters = json.loads(result_text)
        
        print(f"✅ Successfully generated {len(chapters)} chapters", file=sys.stderr)
        return {
            "success": True, 
            "chapters": chapters,
            "raw_response": result_text
        }

    except Exception as e:
        print(f"❌ API Error: {str(e)}", file=sys.stderr)
        # Print more details if possible
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python auto_mapper.py <vtt_file> <api_key> [model] [base_url]")
        sys.exit(1)

    vtt_file = sys.argv[1]
    api_key = sys.argv[2]
    model = sys.argv[3] if len(sys.argv) > 3 else "gemini-2.5-flash"
    
    # Dynamic Base URL for Kie.ai: https://api.kie.ai/<model>/v1
    # Check if user provided explicit base_url, otherwise construct it
    if len(sys.argv) > 4:
        base_url = sys.argv[4]
    else:
        # KIE.ai specific pattern
        base_url = f"https://api.kie.ai/{model}/v1"

    print(f"🔗 Base URL: {base_url}", file=sys.stderr)
    result = generate_chapters(vtt_file, api_key, model, base_url)
    print(json.dumps(result, indent=2))
