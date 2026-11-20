import os
import json
import re
import pandas as pd
from typing import List, Dict, Any
from src.config import JSON_FILE, CSV_FILE, GEMINI_API_KEY

# Initialize Google GenAI client if available
genai_client = None
try:
    from google import genai
    from google.genai import types
    if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_FREE_GEMINI_API_KEY":
        genai_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception:
    genai_client = None

# In-memory runtime cache for dynamically generated AI seminars
dynamic_ai_cache: List[Dict[str, Any]] = []


def load_file_seminars() -> pd.DataFrame:
    """Loads static seminar master database from external JSON or CSV file."""
    if JSON_FILE.exists():
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return pd.DataFrame(data)
        except Exception as e:
            print(f"Warning: Failed to load {JSON_FILE}: {e}")

    if CSV_FILE.exists():
        try:
            return pd.read_csv(CSV_FILE)
        except Exception as e:
            print(f"Warning: Failed to load {CSV_FILE}: {e}")

    # Minimal fallback
    return pd.DataFrame([
        {
            "id": "SEM-101",
            "title": "AI & No-Code Automation Masterclass",
            "country": "India",
            "state": "Gujarat",
            "city": "Ahmedabad",
            "university": "GTU",
            "type": "Offline",
            "date": "2026-12-10",
            "status": "Open",
        }
    ])


def fetch_dynamic_seminars_with_ai(from_date: str, to_date: str, location: str) -> List[Dict[str, Any]]:
    """
    Uses Google GenAI (Gemini) to dynamically generate/discover realistic tech seminars
    in India for the exact requested travel dates and location in the same schema format.
    """
    if not genai_client:
        return []

    prompt = f"""
You are an Indian Tech Conference and Academic Seminar Database API.
Generate 4 realistic university seminars/bootcamps scheduled in India for:
- Travel Dates: between {from_date} and {to_date}
- Target Location/City/State: {location if location else 'Any major Indian tech hub'}

Output MUST be valid JSON only (a raw JSON list of objects, without markdown code fences), matching this EXACT format:
[
  {{
    "id": "SEM-AI-01",
    "title": "Agentic AI & LLM Systems Summit",
    "country": "India",
    "state": "Maharashtra",
    "city": "Pune",
    "university": "Pune University (SPPU)",
    "type": "Offline",
    "date": "{from_date}",
    "status": "Open"
  }}
]

Rules:
1. All dates must strictly be between {from_date} and {to_date}.
2. Ensure realistic Indian universities (e.g. IITs, NITs, GTU, IISc, Anna University, BITS).
3. "status" should be mostly "Open" with at most 1 "Closed".
4. "type" can be "Offline" or "Online".
"""

    candidate_models = [
        "gemini-2.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash-lite",
        "gemini-3.8-flash"
    ]

    for model_name in candidate_models:
        try:
            response = genai_client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response and hasattr(response, "text") and response.text:
                raw_text = response.text.strip()
                # Strip markdown code blocks if present
                clean_json = re.sub(r"^```(?:json)?\s*", "", raw_text)
                clean_json = re.sub(r"\s*```$", "", clean_json).strip()
                
                parsed = json.loads(clean_json)
                if isinstance(parsed, list) and len(parsed) > 0:
                    # Validate required keys
                    required_keys = {"id", "title", "country", "state", "city", "university", "type", "date", "status"}
                    valid_items = [
                        item for item in parsed
                        if isinstance(item, dict) and required_keys.issubset(item.keys())
                    ]
                    if valid_items:
                        return valid_items
        except Exception:
            continue

    return []


def get_seminars(from_date: str = "", to_date: str = "", location: str = "", use_ai: bool = True) -> pd.DataFrame:
    """
    Hybrid Seminar Provider:
    1. First attempts dynamic generation using Google GenAI if requested.
    2. Seamlessly falls back to local master database to ensure ZERO errors.
    """
    global dynamic_ai_cache

    if use_ai and from_date and to_date:
        ai_seminars = fetch_dynamic_seminars_with_ai(from_date, to_date, location)
        if ai_seminars:
            # Store newly discovered seminars in cache
            dynamic_ai_cache.extend(ai_seminars)
            return pd.DataFrame(ai_seminars).sort_values(by="date")

    # Fallback to local file database
    df = load_file_seminars()

    if from_date and from_date.strip():
        df = df[df["date"] >= from_date.strip()]

    if to_date and to_date.strip():
        df = df[df["date"] <= to_date.strip()]

    if location and location.strip():
        loc = location.strip().lower()
        df = df[
            df["state"].str.lower().str.contains(loc, na=False)
            | df["city"].str.lower().str.contains(loc, na=False)
            | df["university"].str.lower().str.contains(loc, na=False)
        ]

    # Combine with any cached AI seminars if they match
    if dynamic_ai_cache:
        df_ai = pd.DataFrame(dynamic_ai_cache)
        df = pd.concat([df, df_ai]).drop_duplicates(subset=["id"])

    return df.sort_values(by="date")
