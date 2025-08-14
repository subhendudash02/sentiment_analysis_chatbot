from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentiment_analysis import run_gemini_api
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Allow all CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    message: str
    session_id: str

@app.post("/sentiment-analysis")
def ask_gpt(request: QueryRequest):
    response = run_gemini_api(
        text=request.message,
        session_id=request.session_id,
        mongo_uri=os.getenv('MONGODB_URL')
    )
    return {"response": response}
