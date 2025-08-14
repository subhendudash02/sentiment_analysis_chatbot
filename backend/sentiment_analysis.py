import os
import requests
import json
from pymongo import MongoClient
import nltk
from transformers import pipeline
import uuid

nltk.download('punkt')
emotion_classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", top_k=None)

def run_gemini_api(text, session_id=None, mongo_uri="mongodb+srv://admin:zYvjDKjsZBnrNvxP@cluster0.xgd2g.mongodb.net/", db_name="emotion_db", history_collection="conversations"):
    detect_and_store_emotion(text)
    # Retrieve conversation history with enhanced context
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[history_collection]
    history = []
    if session_id:
        # Get last 5 turns with more metadata
        history_cursor = collection.find(
            {"session_id": session_id},
            {"user": 1, "agent": 1, "timestamp": 1, "emotion": 1, "context": 1}
        ).sort("timestamp", -1).limit(20)
        history = list(history_cursor)[::-1]  # oldest first
    # Build enhanced conversation context with emotions and metadata
    conversation = ""
    for turn in history:
        emotion = turn.get('emotion', '')
        context = turn.get('context', {})
        conversation += (
            f"Customer: {turn.get('user', '')}\n"
            f"[Customer Emotion: {emotion}]\n"
            f"Agent: {turn.get('agent', '')}\n"
            f"[Context: {json.dumps(context)}]\n\n"
        )
    # Enhanced prompt engineering for Gemini with clarification instruction
    system_prompt = (
        "You are an experienced customer service agent for a large E-commerce company that sells a wide variety of items. "
        "Important instructions:\n"
        "1. Review the conversation history and emotional context before responding\n"
        "2. Maintain continuity with previous responses and avoid asking questions already answered\n"
        "3. Adapt your tone based on the customer's detected emotion\n"
        "4. Keep responses under 50 words and stay focused on the current topic\n"
        "5. For order status inquiries, ask for the order number and respond with detailed tracking information\n"
        "6. Handle return/exchange requests by validating the purchase window (30-day policy) and condition requirements\n"
        "7. Process refund requests by checking payment method and original transaction details\n"
        "8. Assist with product recommendations based on customer's purchase history and preferences\n"
        "9. Manage delivery address updates and special delivery instructions\n"
        "10. Reference previous context when needed and maintain a solution-focused approach\n"
        "11. If you don't know something, suggest human support\n"
        "12. Only ask for clarification if the information isn't in the history"
        "\n"
        "When handling these requests, provide specific details as if accessing a real database. "
        "For example, use realistic order numbers, tracking details, and delivery dates."
    )
    prompt = f"""
        {system_prompt}
        
        Below is the conversation history:
        {conversation} 

        Customer's current query: {text}
    """
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
    session_id = str(uuid.uuid4())
    response_text = run_gemini_api("How are you today?", session_id=session_id)
    detect_and_store_emotion(response_text)
