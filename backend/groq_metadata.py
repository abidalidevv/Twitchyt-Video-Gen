import json
from typing import Dict, Any, Optional

from .api_pool import groq_pool


def generate_youtube_metadata(transcript_text: str, custom_topic: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyzes video transcript or topic and generates 5 viral titles,
    an SEO description, formatted chapters with timestamps, and 20 ranked tags.
    """
    client, key_id = groq_pool.get_client()

    prompt = f"""
    You are an elite YouTube growth strategist and metadata engineer. 
    Analyze this video transcript or commentary context:
    
    Topic / Excerpt:
    {transcript_text[:10000] if transcript_text else custom_topic}

    Generate the following in STRICT JSON format:
    1. "titles": Array of 5 High-CTR, viral, curiosity-gap YouTube titles (engaging, powerful, non-spammy).
    2. "description": An SEO-optimized YouTube video description including a 2-sentence compelling hook, summary, and call to action.
    3. "chapters": Array of objects [{{"time": "00:00", "title": "Intro / The Setup"}}, ...] covering the key timeline moments.
    4. "tags": Comma-separated string of 20 high-volume YouTube SEO tags.

    Return ONLY a valid JSON object with keys: "titles", "description", "chapters", "tags".
    """

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        raw_data = json.loads(response.choices[0].message.content)
    except Exception as e:
        # Auto-rotate key on error and retry once
        if "429" in str(e) or "rate" in str(e).lower() or "model" in str(e).lower():
            groq_pool.rotate_to_next(key_id, reason=str(e))
            client_retry, _ = groq_pool.get_client()
            response = client_retry.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            raw_data = json.loads(response.choices[0].message.content)
        else:
            raise e


    # Format chapters if list of dicts
    chapters_val = raw_data.get("chapters", [])
    if isinstance(chapters_val, list):
        formatted_ch = []
        for ch in chapters_val:
            if isinstance(ch, dict):
                t = ch.get("time", "00:00")
                title = ch.get("title", "")
                formatted_ch.append(f"{t} - {title}")
            else:
                formatted_ch.append(str(ch))
        raw_data["chapters"] = "\n".join(formatted_ch)

    # Format tags if string
    tags_val = raw_data.get("tags", [])
    if isinstance(tags_val, str):
        raw_data["tags"] = [t.strip().lstrip("#") for t in tags_val.split(",") if t.strip()]

    return raw_data

