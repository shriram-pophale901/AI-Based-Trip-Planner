import os
import urllib.request
import json
from dotenv import load_dotenv

def test_gemini():
    # Adjust path if running in backend directory
    env_path = ".env"
    if not os.path.exists(env_path) and os.path.exists("backend/.env"):
        env_path = "backend/.env"
        
    load_dotenv(dotenv_path=env_path, override=True)
    key = os.getenv("GEMINI_API_KEY")
    
    if not key or key == "YOUR_GEMINI_API_KEY_HERE":
        print("[ERROR] GEMINI_API_KEY is not configured in backend/.env!")
        return
        
    print(f"Testing Gemini API with key: {key[:8]}*****...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={key}"
    payload = {
        "contents": [{"parts": [{"text": "Tell me a 1-sentence historical fact about Shaniwar Wada in Pune."}]}]
    }
    
    try:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
        
        reply = res_data["candidates"][0]["content"]["parts"][0]["text"]
        print("[SUCCESS] Gemini responded successfully:")
        print(reply.strip())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"[ERROR] HTTP {e.code}: {err_body}")
    except Exception as e:
        print(f"[ERROR] Failed to reach Gemini: {e}")

if __name__ == "__main__":
    test_gemini()
