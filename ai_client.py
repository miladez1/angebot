# ai_client.py

import requests
from db import get_ai_setting

def generate_tattoo(prompt):
    API_URL = get_ai_setting("AI_API_URL", "https://your-ai-api.com/generate")
    API_KEY = get_ai_setting("AI_API_KEY", "YOUR_AI_API_KEY")
    try:
        data = {
            "prompt": prompt,
            "api_key": API_KEY
        }
        resp = requests.post(API_URL, json=data, timeout=90)
        if resp.status_code == 200:
            js = resp.json()
            return js.get("img_url")
        else:
            return None
    except Exception:
        return None