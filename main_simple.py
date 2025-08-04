"""
The Missing Link - Emotional AI Chatbot Backend
Simplified version without sentence-transformers for Replit
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from datetime import datetime
import re
from collections import Counter

# Try to import Groq with error handling
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Groq import failed: {e}")
    GROQ_AVAILABLE = False
    Groq = None

app = FastAPI(title="The Missing Link API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq client
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    print("⚠️  GROQ_API_KEY environment variable not set!")
    print("Please set it in Replit's Secrets tab")
    groq_client = None
elif not GROQ_AVAILABLE:
    print("❌ Groq library not available")
    groq_client = None
else:
    try:
        # Initialize Groq client with minimal parameters
        groq_client = Groq(api_key=api_key)
        print("✅ Groq client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Groq client: {e}")
        print("⚠️  The chat will work but responses will be fallback messages")
        groq_client = None

# File paths for memory storage
HISTORY_FILE = "chat_history.json"
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

def simple_memory_recall(user_msg, history, max_recall=3):
    """Simple keyword-based memory recall without embeddings"""
    if len(history) < 2:
        return []
    
    user_words = set(user_msg.lower().split())
    recalled_messages = []
    
    # Look through past user messages for keyword matches
    for msg in history[:-1]:  # Exclude current message
        if msg["role"] == "user":
            msg_words = set(msg["content"].lower().split())
            # Find common words (excluding very common words)
            common_words = user_words.intersection(msg_words)
            common_words = {w for w in common_words if len(w) > 3}  # Only meaningful words
            
            if len(common_words) > 0:
                recalled_messages.append({
                    "content": msg["content"],
                    "relevance": len(common_words)
                })
    
    # Sort by relevance and return top matches
    recalled_messages.sort(key=lambda x: x["relevance"], reverse=True)
    return [msg["content"] for msg in recalled_messages[:max_recall]]

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
        "embeddings_available": False,
        "memory_type": "keyword_based"
    }

@app.get("/history")
async def get_history():
    """Get chat history"""
    return {"history": history}

@app.post("/chat")
async def chat(req: Request):
    """Main chat endpoint with keyword-based memory recall"""
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
        
        # Simple keyword-based memory recall
        recalled_messages = simple_memory_recall(user_msg, history)
        
        # Build context for Groq
        context_messages = []
        
        # Add system message with user info and context - adaptive length
        user_word_count = len(user_msg.split())
        
        if user_word_count <= 3:
            system_msg = "You are 'The Missing Link', an empathetic AI companion. The user sent a very short message. Respond briefly - just 1-2 sentences max. Match their casual energy."
        elif user_word_count <= 10:
            system_msg = "You are 'The Missing Link', an empathetic AI companion. The user sent a short message. Keep your response concise - 2-3 sentences. Be warm but brief."
        elif user_word_count <= 25:
            system_msg = "You are 'The Missing Link', an empathetic AI companion. The user sent a medium-length message. Respond with 3-4 sentences. Be thoughtful and caring."
        else:
            system_msg = "You are 'The Missing Link', an empathetic AI companion. The user shared something detailed. You can give a more thoughtful response of 4-6 sentences. Be deeply empathetic and engaged."
        
        system_msg += " Remember past conversations and understand emotions. Respond naturally and conversationally."
        
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
                # Adaptive max_tokens based on user message length
                if user_word_count <= 3:
                    max_tokens = 50   # Very short responses for short messages
                elif user_word_count <= 10:
                    max_tokens = 100  # Short responses
                elif user_word_count <= 25:
                    max_tokens = 200  # Medium responses
                else:
                    max_tokens = 350  # Longer responses for detailed messages
                
                response = groq_client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=context_messages,
                    max_tokens=max_tokens,
                    temperature=0.8
                )
                
                if response and response.choices and len(response.choices) > 0:
                    bot_reply = response.choices[0].message.content.strip()
                else:
                    bot_reply = "I'm having trouble generating a response right now. Please try again."
                
        except Exception as groq_error:
            print(f"Groq API error: {groq_error}")
            bot_reply = "I'm experiencing some technical difficulties. Please try again in a moment."
        
        # Store bot reply in history
        history.append({"role": "assistant", "content": bot_reply})
        
        # Analyze emotion and update summary
        emotion = classify_emotion(user_msg)
        update_summary(user_msg, emotion)
        
        # Save updated memory files
        save_file(HISTORY_FILE, history)
        
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
    global history, metadata, summary
    
    history = []
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
    save_file(METADATA_FILE, metadata)
    save_file(SUMMARY_FILE, summary)
    
    return {"message": "Memory reset successfully"}

if __name__ == "__main__":
    import uvicorn
    import socket
    
    # Find an available port
    def find_free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
    
    # Try the default port first, then find a free one
    default_port = int(os.environ.get("PORT", 8000))
    try:
        uvicorn.run(app, host="0.0.0.0", port=default_port)
    except OSError as e:
        if "Address already in use" in str(e):
            free_port = find_free_port()
            print(f"Port {default_port} is busy, using port {free_port}")
            uvicorn.run(app, host="0.0.0.0", port=free_port)
        else:
            raise
