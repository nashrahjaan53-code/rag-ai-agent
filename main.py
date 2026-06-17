from dotenv import load_dotenv
load_dotenv()
import os
import numpy as np
import uuid
import traceback  # Prints exact error tracebacks if an internal crash happens
from typing import Optional  # Stops FastAPI from throwing 422 validation errors on null payloads
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import uvicorn

# Google GenAI Core Engine
from google import genai
from google.genai import types

app = FastAPI(title="Recimotech Enterprise File-RAG Agent")

# Enable CORS for seamless connection with index.html
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. LOAD AND CHUNK THE KNOWLEDGE BASE FILE DYNAMICALLY
KNOWLEDGE_FILE = "company_knowledge.txt"
KNOWLEDGE_BASE = []

if not os.path.exists(KNOWLEDGE_FILE):
    print(f"⚠️ Warning: {KNOWLEDGE_FILE} not found! Creating a placeholder file.")
    KNOWLEDGE_BASE = ["Recimotech Solutions is an elite IT company in Karan Nagar, Srinagar."]
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        f.write(KNOWLEDGE_BASE[0])
else:
    print(f"📖 Loading complete company details from {KNOWLEDGE_FILE}...")
    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        raw_text = f.read()
        chunks = [chunk.strip() for chunk in raw_text.split("\n\n") if chunk.strip()]
        KNOWLEDGE_BASE = chunks
    print(f"✅ Successfully ingested {len(KNOWLEDGE_BASE)} detailed structural context blocks!")

# Initialize NLP Model for Semantic Search Embeddings
print("🧠 Embedding parsed company details...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
KB_EMBEDDINGS = embedding_model.encode(KNOWLEDGE_BASE)

# Verify API Key exists before starting client to prevent hidden crashes
if not os.environ.get("GEMINI_API_KEY"):
    print("\n❌ CRITICAL ERROR: GEMINI_API_KEY is completely missing from your environment variables or .env file!")
    print("Please ensure your .env file has: GEMINI_API_KEY=your_key_here\n")

# Initialize your LLM client
ai_client = genai.Client()

# Stateful Session Memory Store
SESSION_STORAGE = {}

# Optional[str] stops FastAPI from throwing a 422 error when session_id is empty or null
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None  

@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    user_query = payload.message.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Empty query")
    
    # Securely catch empty strings, "null" texts, or None values from the frontend
    incoming_session = payload.session_id
    if incoming_session is None or incoming_session == "null" or incoming_session == "":
        session_id = str(uuid.uuid4())
    else:
        session_id = incoming_session
        
    if session_id not in SESSION_STORAGE:
        SESSION_STORAGE[session_id] = []
        
    chat_history = SESSION_STORAGE[session_id]
    
    try:
        # ---- STEP A: RAG SEARCH ----
        query_embedding = embedding_model.encode([user_query])
        similarities = cosine_similarity(query_embedding, KB_EMBEDDINGS)[0]
        
        top_indices = np.argsort(similarities)[-3:][::-1]
        retrieved_context = "\n\n".join([KNOWLEDGE_BASE[idx] for idx in top_indices if similarities[idx] > 0.22])
        
        # ---- STEP B: COMPILE RECENT CONVERSATION HISTORY TIMELINE ----
        formatted_history = ""
        for turn in chat_history[-4:]:
            formatted_history += f"{turn['role'].upper()}: {turn['content']}\n"
            
        # ---- STEP C: DYNAMIC CONTEXTUAL SYSTEM PROMPTING ----
        system_instruction = f"""
        You are the advanced conversational AI Agent for Recimotech Solutions, Srinagar.
        Your primary directive is to answer any user query organically, professionally, and naturally based on the background document context and conversation timeline provided.

        AUTHENTIC COMPANY KNOWLEDGE BASE:
        {retrieved_context}

        RECENT CONVERSATION TIMELINE:
        {formatted_history}

        AGENT PROTOCOLS:
        1. Speak cleanly and engagingly. Use clean markdown formatting like bolding or bullet points for lists. Never sound mechanical or robotic.
        2. Maintain context continuity! Always connect pronouns ("it", "they", "the course", "fees") to the active topic discussed earlier in the conversation history timeline.
        3. If the user asks about specific placements, student reviews, eligibility metrics, or custom services, use the document data to answer perfectly.
        4. When transactional intent is discovered (e.g., wanting to enroll, asking to schedule an interview, requesting a commercial project quote, dropping out contact info), systematically make sure to capture their Name, Email, and Phone number seamlessly.
        """

        # ---- STEP D: GENERATE RESPONSE VIA LLM ----
        # FIXED: Updated model routing variable path to gemini-2.5-flash to eliminate SDK 404 faults
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',  
            contents=user_query,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.35,
            ),
        )
        bot_response = response.text.strip()
        
        # ---- STEP E: SAVE CURRENT EXCHANGE TO MEMORY ----
        chat_history.append({"role": "user", "content": user_query})
        chat_history.append({"role": "model", "content": bot_response})
        
        trigger_words = ["name", "phone", "number", "email", "contact details", "details"]
        is_contact_requested = any(word in bot_response.lower() for word in trigger_words)

        return {
            "response": bot_response, 
            "session_id": session_id,
            "isContactRequested": is_contact_requested
        }
        
    except Exception as e:
        # Added tracking to show you EXACTLY what broke in the terminal console window
        print("\n❌ BACKEND CRASH ERROR LOG:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)