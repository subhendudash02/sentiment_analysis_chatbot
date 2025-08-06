import os
import requests
import json
from pymongo import MongoClient
import nltk
from transformers import pipeline

nltk.download('punkt')
emotion_classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=None)

def run_gemini_api(text, session_id=None, mongo_uri="mongodb+srv://admin:zYvjDKjsZBnrNvxP@cluster0.xgd2g.mongodb.net/", db_name="emotion_db", history_collection="conversations"):
    detect_and_store_emotion(text)
    # Retrieve last 3 conversation turns for context
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[history_collection]
    history = []
    if session_id:
        history_cursor = collection.find({"session_id": session_id}).sort("timestamp", -1).limit(3)
        history = list(history_cursor)[::-1]  # oldest first
    # Build conversation context
    conversation = ""
    for turn in history:
        conversation += f"Customer: {turn.get('user', '')}\nAgent: {turn.get('agent', '')}\n"
    # Enhanced prompt engineering for Gemini with clarification instruction
    system_prompt = (
        "You are an experienced customer service agent for a large E-commerce company that sells a wide variety of items. "
        "Always provide helpful, concise, and friendly answers to customer questions. "
        "Keep your response under 50 words. "
        "If the question is about products, orders, returns, shipping, or general help, answer as a professional support agent. "
        "If you don't know the answer, politely suggest contacting human support. "
        "If the customer's question is unclear or missing details, ask a clarifying question before answering."
    )
    prompt = f"{system_prompt}\n{conversation}Customer: {text}\nAgent:"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=AIzaSyD41Dv4rg7RaWJO3Nq_XpW9o_NoxaZ21oQ"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    assert response.status_code == 200, f"API call failed: {response.status_code} {response.text}"
    try:
        candidates = response.json().get("candidates", [])
        agent_reply = candidates[0]["content"]["parts"][0]["text"] if candidates else "No response text found."
    except (KeyError, IndexError, TypeError):
        agent_reply = "No response text found."
    print("Response:", agent_reply)
    # Store this turn in conversation history
    if session_id:
        collection.insert_one({
            "session_id": session_id,
            "user": text,
            "agent": agent_reply,
            "timestamp": int(__import__('time').time())
        })
    return agent_reply

def detect_and_store_emotion(text, mongo_uri="mongodb+srv://admin:zYvjDKjsZBnrNvxP@cluster0.xgd2g.mongodb.net/", db_name="emotion_db", collection_name="emotions"):
    results = emotion_classifier(text)
    if results and isinstance(results, list):
        sorted_results = sorted(results[0], key=lambda x: x['score'], reverse=True)
        dominant_emotion = sorted_results[0]['label'] if sorted_results else "unknown"
        emotions = {item['label']: float(item['score']) for item in sorted_results}
    else:
        dominant_emotion = "unknown"
        emotions = {}
    print(f"Detected emotion: {dominant_emotion}")

    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]
    doc = {"text": text, "emotion": dominant_emotion, "emotions": emotions}
    result = collection.insert_one(doc)
    print(f"Stored in MongoDB with id: {result.inserted_id}")
    return dominant_emotion

if __name__ == "__main__":
    response_text, _ = run_gemini_api("How are you today?")
    detect_and_store_emotion(response_text)
