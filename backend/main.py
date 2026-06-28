from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import recommender
import csv
import os
import urllib.request
import json
from dotenv import load_dotenv
import pandas as pd
import re

# --- RAG Setup ---
try:
    csv_path = "data/pune_pois.csv" if os.path.exists("data/pune_pois.csv") else "backend/data/pune_pois.csv"
    poi_df = pd.read_csv(csv_path)
except Exception as e:
    print(f"Error loading POI data for RAG: {e}")
    poi_df = None

def get_rag_context(query: str, top_k: int = 3) -> str:
    if poi_df is None:
        return ""
    
    words = set(re.findall(r'\w+', query.lower()))
    if not words:
        return ""
        
    def score_row(row):
        text = str(row['name']).lower() + " " + str(row['type']).lower()
        row_words = set(re.findall(r'\w+', text))
        return len(words.intersection(row_words))
        
    df_temp = poi_df.copy()
    df_temp['rag_score'] = df_temp.apply(score_row, axis=1)
    top_matches = df_temp[df_temp['rag_score'] > 0].nlargest(top_k, 'rag_score')
    
    if top_matches.empty:
        return ""
        
    context = "Here is some information from our Pune database that might be relevant to the user's query:\n"
    for _, row in top_matches.iterrows():
        context += f"- {row['name']} (Type: {row['type']}, Open: {row['opening_time']} to {row['closing_time']})\n"
    return context
# -----------------

# Load .env file
env_path = ".env"
if not os.path.exists(env_path) and os.path.exists("backend/.env"):
    env_path = "backend/.env"
load_dotenv(dotenv_path=env_path, override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI(title="Puneri Pulse API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TripRequest(BaseModel):
    destination: str = "Pune"
    days: int
    budget: str
    group_type: str
    user_lat: Optional[float] = None   # User's current latitude
    user_lon: Optional[float] = None   # User's current longitude
    start_time: str = "09:00"          # Exploration start time (HH:MM)
    end_time: str = "18:00"            # Exploration end time (HH:MM)
    user_id: Optional[str] = None      # Logged-in user's Firebase UID

class FeedbackRequest(BaseModel):
    rating: int
    comment: str
    destination: str
    days: int
    budget: str
    group_type: str

class ChatMessage(BaseModel):
    role: str  # "user" or "model"
    text: str

class ChatRequest(BaseModel):
    history: List[ChatMessage]
    message: str

@app.post("/api/plan")
def create_trip_plan(req: TripRequest):
    days = min(max(req.days, 1), 7)

    result = recommender.generate_itinerary(
        days=days,
        budget=req.budget,
        group_type=req.group_type,
        user_lat=req.user_lat,
        user_lon=req.user_lon,
        start_time=req.start_time,
        end_time=req.end_time,
        user_id=req.user_id
    )

    return {
        "status": "success",
        "parameters": req.dict(),
        "itinerary": result["itinerary"],
        "hotels": result["hotels"]
    }

@app.post("/api/feedback")
def submit_feedback(req: FeedbackRequest):
    file_exists = os.path.isfile("feedback.csv")
    with open("feedback.csv", mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["rating", "comment", "destination", "days", "budget", "group_type"])
        writer.writerow([req.rating, req.comment, req.destination, req.days, req.budget, req.group_type])
    
    return {"status": "success", "message": "Feedback saved"}

@app.post("/api/chat")
def chat_with_gemini(req: ChatRequest):
    # Re-load env on request to capture runtime updates to the .env file
    load_dotenv(dotenv_path=env_path, override=True)
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key or api_key == "YOUR_GEMINI_API_KEY_HERE" or api_key == "":
        raise HTTPException(
            status_code=500,
            detail="Gemini API Key is not configured. Please add GEMINI_API_KEY to your backend/.env file."
        )

    # Format history and current message for Gemini API
    contents = []
    for msg in req.history:
        role = "user" if msg.role == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": msg.text}]
        })
        
    contents.append({
        "role": "user",
        "parts": [{"text": req.message}]
    })

    # Generate RAG Context
    rag_context = get_rag_context(req.message)

    system_instruction = (
        "You are 'Puneri Guide', a helpful, witty, and friendly local AI assistant for Pune tourism. "
        "You help tourists with queries about Pune's tourism places (like Shaniwar Wada, Sinhagad Fort, Dagdusheth Temple, etc.), "
        "what to do there, travel recommendations, local bus/auto travel details, and famous local foods (like Misal Pav, Bakarwadi, SPDP). "
        "Make your responses informative, complete, and detailed so the user has all the facts, while keeping the formatting clean and easy to read. "
        "Do not answer questions unrelated to travel or Pune tourism.\n\n"
    )
    
    if rag_context:
        system_instruction += "Context for answering the user's current question:\n" + rag_context

    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 850
        }
    }

    # Using gemini-3.5-flash which is available in this environment
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key}"
    req_body = json.dumps(payload).encode("utf-8")

    try:
        request = urllib.request.Request(
            url,
            data=req_body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            
        candidates = res_data.get("candidates", [])
        if not candidates:
            raise HTTPException(status_code=500, detail="No response candidates returned by Gemini.")
            
        reply_text = candidates[0]["content"]["parts"][0]["text"]
        return {"status": "success", "reply": reply_text}

    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"Gemini API HTTPError: {err_msg}")
        raise HTTPException(
            status_code=e.code,
            detail=f"Gemini API Error: {err_msg}"
        )
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error calling Gemini API: {str(e)}"
        )

@app.get("/")
def health_check():
    return {"status": "Backend running successfully"}
