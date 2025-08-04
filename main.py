"""
The Missing Link - Emotional AI Chatbot Backend
Optimized for Replit deployment
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
import json
import os
from datetime import datetime
from pathlib import Path
import re
from collections import Counter

# Try to import optional dependencies
try:
    from sentence_transformers import SentenceTransformer, util
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("WARNING: sentence-transformers not available. AI features will be limited.")
    SENTENCE_TRANSFORMERS_AVAILABLE = False

app = FastAPI(title="The Missing Link API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq client and sentence transformer
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    print("⚠️  GROQ_API_KEY environment variable not set!")
    print("Please set it in Replit's Secrets tab")
    groq_client = None
else:
    try:
        groq_client = Groq(api_key=api_key)
        print("✅ Groq client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Groq client: {e}")
        groq_client = None

# Initialize sentence transformer model
model = None
if SENTENCE_TRANSFORMERS_AVAILABLE:
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Sentence transformer model loaded")
    except Exception as e:
        print(f"❌ Failed to load sentence transformer: {e}")

# File paths for memory storage
HISTORY_FILE = "chat_history.json"
EMBEDDINGS_FILE = "embeddings.json"
METADATA_FILE = "metadata.json"
SUMMARY_FILE = "summary.json"

def load_file(file_path, fallback):
    """Load JSON file or return fallback if file doesn't exist"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
    return fallback

def save_file(file_path, data):
    """Save data to JSON file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving {file_path}: {e}")

# Initialize memory structures
history = load_file(HISTORY_FILE, [])
embeddings = load_file(EMBEDDINGS_FILE, [])
metadata = load_file(METADATA_FILE, {})
summary = load_file(SUMMARY_FILE, {
    "total_messages": 0,
    "dominant_emotions": [],
    "life_patterns": [],
    "conversation_themes": [],
    "last_updated": datetime.now().isoformat()
})

def classify_emotion(text):
    """Classify emotion from text using keyword matching"""
    emotions = {
        'joy': ['happy', 'excited', 'great', 'awesome', 'love', 'wonderful', 'amazing', 'fantastic', 'good', 'glad', 'thrilled', 'delighted'],
        'sadness': ['sad', 'depressed', 'down', 'upset', 'crying', 'hurt', 'disappointed', 'lonely', 'miserable', 'heartbroken'],
        'anger': ['angry', 'mad', 'furious', 'annoyed', 'frustrated', 'irritated', 'rage', 'pissed', 'hate'],
        'fear': ['scared', 'afraid', 'worried', 'anxious', 'nervous', 'terrified', 'panic', 'frightened'],
        'surprise': ['surprised', 'shocked', 'amazed', 'astonished', 'wow', 'incredible', 'unbelievable'],
        'disgust': ['disgusted', 'gross', 'sick', 'revolting', 'nasty'],
        'neutral': ['okay', 'fine', 'alright', 'normal', 'whatever']
    }
    
    text_lower = text.lower()
    emotion_scores = {}
    
    for emotion, keywords in emotions.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            emotion_scores[emotion] = score
    
    if emotion_scores:
        return max(emotion_scores, key=emotion_scores.get)
    return 'neutral'

def detect_life_patterns(text):
    """Detect recurring life patterns and themes"""
    patterns = {
        'work_stress': ['work', 'job', 'boss', 'office', 'meeting', 'deadline', 'project', 'colleague'],
        'relationships': ['friend', 'family', 'partner', 'relationship', 'love', 'dating', 'marriage'],
        'health': ['tired', 'sick', 'doctor', 'medicine', 'exercise', 'sleep', 'health'],
        'personal_growth': ['learn', 'grow', 'improve', 'goal', 'dream', 'future', 'change'],
        'hobbies': ['music', 'book', 'movie', 'game', 'art', 'sport', 'hobby'],
        'daily_life': ['morning', 'evening', 'home', 'food', 'weather', 'routine']
    }
    
    text_lower = text.lower()
    detected_patterns = []
    
    for pattern, keywords in patterns.items():
        if any(keyword in text_lower for keyword in keywords):
            detected_patterns.append(pattern)
    
    return detected_patterns

def update_summary(new_text, emotion):
    """Update summary with new message analysis"""
    global summary
    
    summary["total_messages"] += 1
    summary["last_updated"] = datetime.now().isoformat()
    
    # Update emotions
    if "dominant_emotions" not in summary:
        summary["dominant_emotions"] = []
    summary["dominant_emotions"].append(emotion)
    
    # Keep only last 50 emotions for analysis
    if len(summary["dominant_emotions"]) > 50:
        summary["dominant_emotions"] = summary["dominant_emotions"][-50:]
    
    # Update life patterns
    patterns = detect_life_patterns(new_text)
    if "life_patterns" not in summary:
        summary["life_patterns"] = []
    summary["life_patterns"].extend(patterns)
    
    # Keep only last 100 patterns
    if len(summary["life_patterns"]) > 100:
        summary["life_patterns"] = summary["life_patterns"][-100:]
    
    # Update conversation themes (extract key words)
    words = re.findall(r'\b[a-zA-Z]{4,}\b', new_text.lower())
    if "conversation_themes" not in summary:
        summary["conversation_themes"] = []
    summary["conversation_themes"].extend(words)
    
    # Keep only last 200 theme words
    if len(summary["conversation_themes"]) > 200:
        summary["conversation_themes"] = summary["conversation_themes"][-200:]
    
    save_file(SUMMARY_FILE, summary)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "The Missing Link API is running",
        "status": "healthy",
        "groq_available": groq_client is not None,
        "embeddings_available": SENTENCE_TRANSFORMERS_AVAILABLE and model is not None
    }

@app.get("/history")
async def get_history():
    """Get chat history"""
    return {"history": history}

@app.post("/chat")
async def chat(req: Request):
    """Main chat endpoint with enhanced memory and summarization"""
    try:
        data = await req.json()
        user_msg = data.get("message", "").strip()
        user_name = data.get("name", "").strip()
        
        if not user_msg:
            return {"error": "Message cannot be empty"}
        
        # Store/update user metadata
        if user_name and user_name != metadata.get("name"):
            metadata["name"] = user_name
            metadata["last_updated"] = summary["total_messages"]
            save_file(METADATA_FILE, metadata)
        
        # Store user message in history
        history.append({"role": "user", "content": user_msg})
        
        # Generate and store embedding for the user message (if available)
        recalled_messages = []
        if SENTENCE_TRANSFORMERS_AVAILABLE and model:
            user_embedding = model.encode(user_msg).tolist()
            embeddings.append({
                "type": "user",
                "embedding": user_embedding,
                "content": user_msg,
                "message_id": len(embeddings)
            })
            
            # Find most relevant past messages using embeddings
            if len(embeddings) > 1:
                query_embedding = model.encode(user_msg)
                scores = []
                
                for i, emb_data in enumerate(embeddings[:-1]):  # Exclude current message
                    if emb_data["type"] == "user" and "embedding" in emb_data:
                        similarity = util.cos_sim(query_embedding, emb_data["embedding"]).item()
                        scores.append((i, similarity, emb_data["content"]))
                
                # Get top 3 most relevant messages
                top_messages = sorted(scores, key=lambda x: x[1], reverse=True)[:3]
                recalled_messages = [msg[2] for msg in top_messages if msg[1] > 0.3]  # Only include if similarity > 0.3
        else:
            # Simple storage without embeddings
            embeddings.append({
                "type": "user",
                "content": user_msg,
                "message_id": len(embeddings)
            })
        
        # Build context for Groq
        context_messages = []
        
        # Add system message with user info and context
        system_msg = "You are a deeply empathetic AI companion called 'The Missing Link'. You remember past conversations and understand emotions. Be thoughtful, caring, and genuinely interested in the user's well-being. Respond naturally and conversationally, matching their energy. If they share something personal, acknowledge it meaningfully."
        
        # Add user context if available
        if metadata.get("name"):
            system_msg += f" The user's name is {metadata['name']}."
        
        # Add recalled context
        if recalled_messages:
            system_msg += f" Context from past conversations: {'; '.join(recalled_messages[:2])}"
        
        # Add emotional context from summary
        if summary.get("dominant_emotions"):
            recent_emotions = summary["dominant_emotions"][-5:]
            emotion_counts = Counter(recent_emotions)
            most_common = emotion_counts.most_common(2)
            if most_common:
                system_msg += f" Recent emotional patterns: {', '.join([f'{emotion} ({count})' for emotion, count in most_common])}"
        
        context_messages.append({"role": "system", "content": system_msg})
        
        # Add recent conversation history (last 6 messages)
        recent_history = history[-6:]
        context_messages.extend(recent_history)
        
        # Get response from Groq
        try:
            if groq_client is None:
                bot_reply = "⚠️ The AI service is not properly configured. Please check the API key in Replit Secrets."
            else:
                response = groq_client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=context_messages,
                    max_tokens=300,
                    temperature=0.8
                )
                
                if response and response.choices and len(response.choices) > 0:
                    bot_reply = response.choices[0].message.content.strip()
                else:
                    bot_reply = "I'm having trouble generating a response right now. Please try again."
                
        except Exception as groq_error:
            print(f"Groq API error: {groq_error}")
            bot_reply = "I'm experiencing some technical difficulties. Please try again in a moment."
        
        # Store bot reply in history and embeddings
        history.append({"role": "assistant", "content": bot_reply})
        
        # Store bot embedding if available
        if SENTENCE_TRANSFORMERS_AVAILABLE and model:
            bot_embedding = model.encode(bot_reply).tolist()
            embeddings.append({
                "type": "assistant",
                "embedding": bot_embedding,
                "content": bot_reply,
                "message_id": len(embeddings)
            })
        else:
            embeddings.append({
                "type": "assistant",
                "content": bot_reply,
                "message_id": len(embeddings)
            })
        
        # Analyze emotion and update summary
        emotion = classify_emotion(user_msg)
        update_summary(user_msg, emotion)
        
        # Save updated memory files
        save_file(HISTORY_FILE, history)
        save_file(EMBEDDINGS_FILE, embeddings)
        
        return {
            "reply": bot_reply,
            "metadata": metadata,
            "summary": {
                "total_messages": summary["total_messages"],
                "recent_emotions": summary.get("dominant_emotions", [])[-5:],
                "recent_patterns": summary.get("life_patterns", [])[-5:]
            },
            "detected_emotion": emotion,
            "recalled_context": len(recalled_messages)
        }
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return {"error": f"Internal server error: {str(e)}"}

@app.post("/reset")
async def reset_memory():
    """Reset all memory files (for testing purposes)"""
    global history, embeddings, metadata, summary
    
    history = []
    embeddings = []
    metadata = {}
    summary = {
        "total_messages": 0,
        "dominant_emotions": [],
        "life_patterns": [],
        "conversation_themes": [],
        "last_updated": datetime.now().isoformat()
    }
    
    # Save empty files
    save_file(HISTORY_FILE, history)
    save_file(EMBEDDINGS_FILE, embeddings)
    save_file(METADATA_FILE, metadata)
    save_file(SUMMARY_FILE, summary)
    
    return {"message": "Memory reset successfully"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
