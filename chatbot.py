from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from groq import Groq
import json
import os
import hashlib
import shutil
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import Counter
import re
import aiofiles

# Try to import optional dependencies
try:
    from sentence_transformers import SentenceTransformer, util
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("WARNING: sentence-transformers not available. AI features will be limited.")
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    print("WARNING: python-magic not available. MIME type detection will be limited.")
    MAGIC_AVAILABLE = False

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq client and sentence transformer
# Get API key from environment variable or replace the string below with your key
# REPLACE THIS WITH YOUR ACTUAL GROQ API KEY:
api_key = os.environ.get("GROQ_API_KEY")
if api_key == "YOUR_GROQ_API_KEY_HERE":
    print("⚠️  Please set your GROQ_API_KEY environment variable or update the API key in chatbot.py")
    print("Get a free API key from: https://console.groq.com")

try:
    # Initialize Groq client with minimal parameters
    groq_client = Groq(api_key=api_key)
    print("SUCCESS: Groq client initialized successfully")
except Exception as e:
    print(f"ERROR: Groq client initialization failed: {e}")
    print("WARNING: APK management will still work, but chat features may be limited")
    groq_client = None

# Initialize sentence transformer model if available
if SENTENCE_TRANSFORMERS_AVAILABLE:
    try:
        model = SentenceTransformer("all-MiniLM-L6-v2")
        print("SUCCESS: Sentence transformer model loaded successfully")
    except Exception as e:
        print(f"ERROR: Sentence transformer model loading failed: {e}")
        model = None
        SENTENCE_TRANSFORMERS_AVAILABLE = False
else:
    model = None

# File paths
HISTORY_FILE = "chat_history.json"
EMBEDDINGS_FILE = "embeddings.json"
METADATA_FILE = "metadata.json"
SUMMARY_FILE = "summary.json"

# APK Management constants
APK_REGISTRY_FILE = "apk_registry.json"
APK_STORAGE_DIR = Path("apk_storage")
APK_RELEASES_DIR = APK_STORAGE_DIR / "releases"
APK_BETA_DIR = APK_STORAGE_DIR / "beta"
APK_ARCHIVE_DIR = APK_STORAGE_DIR / "archive"

# APK Configuration
MAX_APK_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_APK_EXTENSIONS = {".apk"}
APK_MIME_TYPES = {"application/vnd.android.package-archive", "application/octet-stream"}

# Create APK storage directories
for directory in [APK_STORAGE_DIR, APK_RELEASES_DIR, APK_BETA_DIR, APK_ARCHIVE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Load or initialize memory files
def load_file(file_path, fallback):
    """Load JSON file or return fallback if file doesn't exist"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return fallback

# Initialize memory structures
history = load_file(HISTORY_FILE, [])
embeddings = load_file(EMBEDDINGS_FILE, [])
metadata = load_file(METADATA_FILE, {})
summary = load_file(SUMMARY_FILE, {
    "keywords": [],
    "emotion_count": {},
    "life_patterns": [],
    "total_messages": 0,
    "dominant_themes": []
})

# Initialize APK registry
apk_registry = load_file(APK_REGISTRY_FILE, {
    "apks": [],
    "last_updated": None,
    "total_uploads": 0
})

def save_file(file_path, data):
    """Save data to JSON file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving {file_path}: {e}")

# APK Management Functions
def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def validate_apk_file(file_path: Path, original_filename: str) -> dict:
    """Validate APK file and extract basic information"""
    try:
        # Check file extension
        if not original_filename.lower().endswith('.apk'):
            return {"valid": False, "error": "File must have .apk extension"}
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > MAX_APK_SIZE:
            return {"valid": False, "error": f"File size ({file_size} bytes) exceeds maximum allowed size ({MAX_APK_SIZE} bytes)"}
        
        # Check MIME type (basic validation)
        mime_type = "unknown"
        if MAGIC_AVAILABLE:
            try:
                mime_type = magic.from_file(str(file_path), mime=True)
                if mime_type not in APK_MIME_TYPES:
                    print(f"Warning: Unexpected MIME type {mime_type} for APK file")
            except Exception as e:
                print(f"Could not determine MIME type: {e}")
        else:
            print("MIME type detection skipped (python-magic not available)")
        
        # Calculate file hash
        file_hash = calculate_file_hash(file_path)
        
        return {
            "valid": True,
            "file_size": file_size,
            "file_hash": file_hash,
            "mime_type": mime_type if 'mime_type' in locals() else "unknown"
        }
        
    except Exception as e:
        return {"valid": False, "error": f"Validation error: {str(e)}"}

def get_apk_channel_dir(channel: str) -> Path:
    """Get the directory for a specific APK channel"""
    channel_dirs = {
        "release": APK_RELEASES_DIR,
        "beta": APK_BETA_DIR,
        "archive": APK_ARCHIVE_DIR
    }
    return channel_dirs.get(channel, APK_RELEASES_DIR)

def find_apk_by_id(apk_id: str) -> dict:
    """Find APK metadata by ID"""
    for apk in apk_registry["apks"]:
        if apk["apk_id"] == apk_id:
            return apk
    return None

def find_apk_by_version(version: str, channel: str = "release") -> dict:
    """Find APK by version and channel"""
    for apk in apk_registry["apks"]:
        if apk["version"] == version and apk["channel"] == channel and apk["is_active"]:
            return apk
    return None

def get_latest_apk(channel: str = "release") -> dict:
    """Get the latest APK for a specific channel"""
    channel_apks = [apk for apk in apk_registry["apks"]
                   if apk["channel"] == channel and apk["is_active"]]
    
    if not channel_apks:
        return None
    
    # Sort by upload date (most recent first)
    latest = max(channel_apks, key=lambda x: x["upload_date"])
    return latest

def save_apk_registry():
    """Save APK registry to file"""
    apk_registry["last_updated"] = datetime.now(timezone.utc).isoformat()
    save_file(APK_REGISTRY_FILE, apk_registry)

def cleanup_inactive_apks(days_old: int = 30):
    """Clean up APK files that have been inactive for specified days"""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
        cleaned_count = 0
        
        for apk in apk_registry["apks"]:
            if not apk["is_active"] and "deleted_date" in apk:
                deleted_date = datetime.fromisoformat(apk["deleted_date"].replace('Z', '+00:00'))
                
                if deleted_date < cutoff_date:
                    # Remove physical file
                    file_path = Path(apk["file_path"])
                    if file_path.exists():
                        try:
                            file_path.unlink()
                            print(f"Cleaned up APK file: {file_path}")
                            cleaned_count += 1
                        except Exception as e:
                            print(f"Failed to delete file {file_path}: {e}")
        
        # Remove cleaned APKs from registry
        apk_registry["apks"] = [apk for apk in apk_registry["apks"]
                               if apk["is_active"] or "deleted_date" not in apk or
                               datetime.fromisoformat(apk["deleted_date"].replace('Z', '+00:00')) >= cutoff_date]
        
        if cleaned_count > 0:
            save_apk_registry()
            print(f"Cleaned up {cleaned_count} inactive APK files")
        
        return cleaned_count
        
    except Exception as e:
        print(f"Cleanup error: {e}")
        return 0

def get_storage_stats():
    """Get storage statistics for APK files"""
    try:
        stats = {
            "total_apks": len(apk_registry["apks"]),
            "active_apks": len([apk for apk in apk_registry["apks"] if apk["is_active"]]),
            "inactive_apks": len([apk for apk in apk_registry["apks"] if not apk["is_active"]]),
            "total_size": 0,
            "channels": {"release": 0, "beta": 0, "archive": 0},
            "total_downloads": sum(apk.get("download_count", 0) for apk in apk_registry["apks"])
        }
        
        for apk in apk_registry["apks"]:
            if apk["is_active"]:
                stats["total_size"] += apk["file_size"]
                stats["channels"][apk["channel"]] += 1
        
        # Convert bytes to MB for readability
        stats["total_size_mb"] = round(stats["total_size"] / (1024 * 1024), 2)
        
        return stats
        
    except Exception as e:
        print(f"Storage stats error: {e}")
        return {"error": str(e)}

def archive_old_versions(keep_versions: int = 3):
    """Archive old versions, keeping only the specified number of recent versions per channel"""
    try:
        archived_count = 0
        
        for channel in ["release", "beta"]:
            # Get active APKs for this channel, sorted by upload date (newest first)
            channel_apks = [apk for apk in apk_registry["apks"]
                           if apk["channel"] == channel and apk["is_active"]]
            channel_apks.sort(key=lambda x: x["upload_date"], reverse=True)
            
            # Archive older versions beyond the keep limit
            if len(channel_apks) > keep_versions:
                for apk in channel_apks[keep_versions:]:
                    # Move to archive channel
                    old_path = Path(apk["file_path"])
                    if old_path.exists():
                        new_filename = f"archived_{apk['filename']}"
                        new_path = APK_ARCHIVE_DIR / new_filename
                        
                        try:
                            shutil.move(str(old_path), str(new_path))
                            apk["channel"] = "archive"
                            apk["file_path"] = str(new_path)
                            apk["filename"] = new_filename
                            apk["archived_date"] = datetime.now(timezone.utc).isoformat()
                            archived_count += 1
                            print(f"Archived {apk['version']} from {channel} to archive")
                        except Exception as e:
                            print(f"Failed to archive {apk['filename']}: {e}")
        
        if archived_count > 0:
            save_apk_registry()
            print(f"Archived {archived_count} old APK versions")
        
        return archived_count
        
    except Exception as e:
        print(f"Archive error: {e}")
        return 0

# Enhanced emotion classifier
def classify_emotion(text):
    """Classify emotion from text using keyword matching"""
    emotions = {
        "sad": ["sad", "lonely", "hurt", "depressed", "down", "upset", "crying", "tears", "grief", "sorrow"],
        "happy": ["happy", "excited", "joy", "great", "awesome", "wonderful", "amazing", "fantastic", "love", "thrilled"],
        "angry": ["angry", "mad", "furious", "annoyed", "frustrated", "irritated", "rage", "hate", "pissed"],
        "anxious": ["anxious", "worried", "nervous", "stressed", "panic", "fear", "scared", "overwhelmed"],
        "grateful": ["grateful", "thankful", "blessed", "appreciate", "lucky", "fortunate"],
        "confused": ["confused", "lost", "unclear", "don't understand", "puzzled", "bewildered"],
        "hopeful": ["hopeful", "optimistic", "looking forward", "excited about", "can't wait", "positive"]
    }
    
    text_lower = text.lower()
    emotion_scores = {}
    
    for emotion, keywords in emotions.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            emotion_scores[emotion] = score
    
    if emotion_scores:
        return max(emotion_scores, key=emotion_scores.get)
    return "neutral"

# Life pattern detection
def detect_life_patterns(text):
    """Detect recurring life patterns and themes"""
    patterns = {
        "work_stress": ["work", "job", "boss", "deadline", "meeting", "project", "office", "career"],
        "relationships": ["relationship", "partner", "boyfriend", "girlfriend", "dating", "marriage", "family"],
        "health": ["health", "doctor", "sick", "exercise", "diet", "sleep", "tired", "energy"],
        "personal_growth": ["learning", "growth", "change", "improve", "better", "goal", "dream", "future"],
        "social": ["friends", "social", "party", "hangout", "lonely", "people", "community"],
        "financial": ["money", "budget", "expensive", "cheap", "save", "spend", "financial", "cost"]
    }
    
    text_lower = text.lower()
    detected_patterns = []
    
    for pattern, keywords in patterns.items():
        if any(keyword in text_lower for keyword in keywords):
            detected_patterns.append(pattern)
    
    return detected_patterns

# Enhanced summarizer
def update_summary(new_text, emotion):
    """Update summary with new message analysis"""
    global summary
    
    # Extract meaningful keywords (longer than 3 chars, not common words)
    common_words = {"the", "and", "but", "for", "are", "with", "this", "that", "have", "was", "were", "been", "their", "said", "each", "which", "what", "where", "when", "why", "how", "all", "any", "can", "had", "her", "his", "him", "she", "you", "your", "they", "them", "than", "then", "now", "will", "would", "could", "should", "just", "like", "time", "very", "even", "back", "after", "use", "two", "way", "may", "say", "new", "want", "because", "good", "first", "well", "year", "work", "life", "day", "get", "has", "old", "see", "him", "two", "more", "go", "no", "up", "out", "if", "about", "who", "oil", "sit", "but", "not"}
    
    words = re.findall(r'\b[a-zA-Z]{4,}\b', new_text.lower())
    meaningful_words = [w for w in words if w not in common_words]
    
    # Update keywords
    summary["keywords"].extend(meaningful_words)
    
    # Keep only last 100 keywords to prevent memory bloat
    if len(summary["keywords"]) > 100:
        summary["keywords"] = summary["keywords"][-100:]
    
    # Update emotion count
    summary["emotion_count"][emotion] = summary["emotion_count"].get(emotion, 0) + 1
    
    # Detect and update life patterns
    patterns = detect_life_patterns(new_text)
    summary["life_patterns"].extend(patterns)
    
    # Update message count
    summary["total_messages"] += 1
    
    # Update dominant themes (most common keywords)
    if len(summary["keywords"]) > 10:
        word_counts = Counter(summary["keywords"])
        summary["dominant_themes"] = [word for word, count in word_counts.most_common(5)]
    
    # Save updated summary
    save_file(SUMMARY_FILE, summary)

# APK Management Endpoints

@app.post("/apk/upload")
async def upload_apk(
    file: UploadFile = File(...),
    version: str = None,
    channel: str = "release",
    description: str = ""
):
    """Upload a new APK file"""
    try:
        # Validate channel
        if channel not in ["release", "beta", "archive"]:
            raise HTTPException(status_code=400, detail="Invalid channel. Must be 'release', 'beta', or 'archive'")
        
        # Generate unique APK ID
        apk_id = str(uuid.uuid4())
        
        # Create temporary file for validation
        temp_file = Path(f"temp_{apk_id}.apk")
        
        try:
            # Save uploaded file temporarily
            async with aiofiles.open(temp_file, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Validate the APK file
            validation_result = validate_apk_file(temp_file, file.filename)
            if not validation_result["valid"]:
                raise HTTPException(status_code=400, detail=validation_result["error"])
            
            # Check for duplicate hash
            file_hash = validation_result["file_hash"]
            for existing_apk in apk_registry["apks"]:
                if existing_apk["file_hash"] == file_hash and existing_apk["is_active"]:
                    raise HTTPException(status_code=409, detail="APK with identical content already exists")
            
            # Determine version if not provided
            if not version:
                latest = get_latest_apk(channel)
                if latest:
                    # Simple version increment (this could be more sophisticated)
                    try:
                        parts = latest["version"].split(".")
                        parts[-1] = str(int(parts[-1]) + 1)
                        version = ".".join(parts)
                    except:
                        version = "1.0.1"
                else:
                    version = "1.0.0"
            
            # Check for version conflicts
            existing_version = find_apk_by_version(version, channel)
            if existing_version:
                raise HTTPException(status_code=409, detail=f"Version {version} already exists in {channel} channel")
            
            # Move file to appropriate directory
            channel_dir = get_apk_channel_dir(channel)
            final_filename = f"{file.filename.rsplit('.', 1)[0]}-v{version}.apk"
            final_path = channel_dir / final_filename
            
            shutil.move(str(temp_file), str(final_path))
            
            # Create APK metadata
            apk_metadata = {
                "apk_id": apk_id,
                "filename": final_filename,
                "original_filename": file.filename,
                "version": version,
                "channel": channel,
                "upload_date": datetime.now(timezone.utc).isoformat(),
                "file_size": validation_result["file_size"],
                "file_hash": file_hash,
                "description": description,
                "download_count": 0,
                "is_active": True,
                "file_path": str(final_path)
            }
            
            # Add to registry
            apk_registry["apks"].append(apk_metadata)
            apk_registry["total_uploads"] += 1
            save_apk_registry()
            
            return {
                "message": "APK uploaded successfully",
                "apk_id": apk_id,
                "version": version,
                "channel": channel,
                "file_size": validation_result["file_size"],
                "download_url": f"/apk/download/{apk_id}"
            }
            
        finally:
            # Clean up temporary file if it still exists
            if temp_file.exists():
                temp_file.unlink()
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"APK upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/apk/list")
async def list_apks(channel: str = None, active_only: bool = True):
    """List all available APKs"""
    try:
        apks = apk_registry["apks"]
        
        # Filter by channel if specified
        if channel:
            if channel not in ["release", "beta", "archive"]:
                raise HTTPException(status_code=400, detail="Invalid channel")
            apks = [apk for apk in apks if apk["channel"] == channel]
        
        # Filter by active status
        if active_only:
            apks = [apk for apk in apks if apk["is_active"]]
        
        # Remove file_path from response for security
        response_apks = []
        for apk in apks:
            apk_copy = apk.copy()
            apk_copy.pop("file_path", None)
            response_apks.append(apk_copy)
        
        # Sort by upload date (newest first)
        response_apks.sort(key=lambda x: x["upload_date"], reverse=True)
        
        return {
            "apks": response_apks,
            "total_count": len(response_apks),
            "channels": list(set(apk["channel"] for apk in response_apks))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"APK list error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list APKs: {str(e)}")

@app.get("/apk/download/{apk_id}")
async def download_apk(apk_id: str):
    """Download a specific APK file"""
    try:
        # Find APK metadata
        apk_metadata = find_apk_by_id(apk_id)
        if not apk_metadata:
            raise HTTPException(status_code=404, detail="APK not found")
        
        if not apk_metadata["is_active"]:
            raise HTTPException(status_code=410, detail="APK is no longer available")
        
        # Check if file exists
        file_path = Path(apk_metadata["file_path"])
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="APK file not found on disk")
        
        # Increment download count
        apk_metadata["download_count"] += 1
        save_apk_registry()
        
        # Return file
        return FileResponse(
            path=str(file_path),
            filename=apk_metadata["filename"],
            media_type="application/vnd.android.package-archive"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"APK download error: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.get("/apk/latest")
async def get_latest_apk_info(channel: str = "release"):
    """Get information about the latest APK version"""
    try:
        if channel not in ["release", "beta", "archive"]:
            raise HTTPException(status_code=400, detail="Invalid channel")
        
        latest_apk = get_latest_apk(channel)
        if not latest_apk:
            raise HTTPException(status_code=404, detail=f"No APKs found in {channel} channel")
        
        # Remove sensitive information
        response_apk = latest_apk.copy()
        response_apk.pop("file_path", None)
        response_apk["download_url"] = f"/apk/download/{latest_apk['apk_id']}"
        
        return response_apk
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Latest APK error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get latest APK: {str(e)}")

@app.get("/apk/info/{apk_id}")
async def get_apk_info(apk_id: str):
    """Get detailed information about a specific APK"""
    try:
        apk_metadata = find_apk_by_id(apk_id)
        if not apk_metadata:
            raise HTTPException(status_code=404, detail="APK not found")
        
        # Remove sensitive information
        response_apk = apk_metadata.copy()
        response_apk.pop("file_path", None)
        response_apk["download_url"] = f"/apk/download/{apk_id}"
        
        return response_apk
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"APK info error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get APK info: {str(e)}")

@app.delete("/apk/delete/{apk_id}")
async def delete_apk(apk_id: str):
    """Delete an APK (mark as inactive)"""
    try:
        apk_metadata = find_apk_by_id(apk_id)
        if not apk_metadata:
            raise HTTPException(status_code=404, detail="APK not found")
        
        # Mark as inactive instead of actually deleting
        apk_metadata["is_active"] = False
        apk_metadata["deleted_date"] = datetime.now(timezone.utc).isoformat()
        save_apk_registry()
        
        return {"message": "APK marked as inactive", "apk_id": apk_id}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"APK delete error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete APK: {str(e)}")

@app.get("/apk/stats")
async def get_apk_stats():
    """Get APK storage statistics"""
    try:
        stats = get_storage_stats()
        return stats
        
    except Exception as e:
        print(f"APK stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.post("/apk/cleanup")
async def cleanup_apks(days_old: int = 30):
    """Clean up inactive APK files older than specified days"""
    try:
        if days_old < 1:
            raise HTTPException(status_code=400, detail="days_old must be at least 1")
        
        cleaned_count = cleanup_inactive_apks(days_old)
        
        return {
            "message": f"Cleanup completed",
            "files_cleaned": cleaned_count,
            "days_old_threshold": days_old
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"APK cleanup error: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

@app.post("/apk/archive")
async def archive_old_apks(keep_versions: int = 3):
    """Archive old APK versions, keeping only the specified number of recent versions"""
    try:
        if keep_versions < 1:
            raise HTTPException(status_code=400, detail="keep_versions must be at least 1")
        
        archived_count = archive_old_versions(keep_versions)
        
        return {
            "message": f"Archiving completed",
            "versions_archived": archived_count,
            "versions_kept_per_channel": keep_versions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"APK archive error: {e}")
        raise HTTPException(status_code=500, detail=f"Archive failed: {str(e)}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "The Missing Link API is running", "status": "healthy"}

@app.get("/history")
async def get_history():
    """Get chat history"""
    return {"history": history, "metadata": metadata, "summary": summary}

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
                    if emb_data["type"] == "user":
                        similarity = util.cos_sim(query_embedding, emb_data["embedding"]).item()
                        scores.append((i, similarity, emb_data["content"]))
                
                # Get top 3 most relevant messages
                top_messages = sorted(scores, key=lambda x: x[1], reverse=True)[:3]
                recalled_messages = [msg[2] for msg in top_messages if msg[1] > 0.3]  # Only include if similarity > 0.3
            else:
                recalled_messages = []
        else:
            # Simple storage without embeddings
            embeddings.append({
                "type": "user",
                "content": user_msg,
                "message_id": len(embeddings)
            })
            recalled_messages = []
        
        # Build context for Groq
        context_messages = []
        
        # Add system message with user info and context
        system_msg = "You are a casual, friendly AI companion. Be conversational and natural - not formal or robotic. Match the user's energy and message length. If they send a short message, keep your response short. If they're chatty, you can be more detailed. Be empathetic but speak like a friend, not a therapist."
        
        # Add message length guidance based on user input
        user_msg_length = len(user_msg.split())
        if user_msg_length <= 5:
            system_msg += " Keep your response brief - just a few words or a short sentence."
        elif user_msg_length <= 15:
            system_msg += " Keep your response concise - 1-2 sentences max."
        else:
            system_msg += " You can give a more detailed response, but stay conversational."
        
        if recalled_messages:
            system_msg += f" Context from past chats: {'; '.join(recalled_messages[:2])}"
        
        context_messages.append({"role": "system", "content": system_msg})
        
        # Add recent conversation history (last 6 messages)
        recent_history = history[-6:]
        context_messages.extend(recent_history)
        
        # Get response from Groq
        try:
            if groq_client is None:
                print("❌ Groq client not initialized - invalid API key")
                bot_reply = "⚠️ The AI service is not properly configured. Please check the API key."
            else:
                print(f"Sending to Groq with {len(context_messages)} messages")
                # Adjust max_tokens based on user message length
                user_word_count = len(user_msg.split())
                if user_word_count <= 5:
                    max_tokens = 50  # Very short responses
                elif user_word_count <= 15:
                    max_tokens = 150  # Medium responses
                else:
                    max_tokens = 300  # Longer but still reasonable
                
                response = groq_client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=context_messages,
                    max_tokens=max_tokens,
                    temperature=0.8  # Slightly higher for more natural responses
                )
            
            if response and response.choices and len(response.choices) > 0:
                bot_reply = response.choices[0].message.content.strip()
                print(f"Groq response received: {bot_reply[:100]}...")
            else:
                print("No valid response from Groq")
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
            "summary": summary,
            "detected_emotion": emotion,
            "recalled_context": len(recalled_messages)
        }
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return {"error": "An error occurred while processing your message", "details": str(e)}

@app.post("/reset")
async def reset_memory():
    """Reset all memory files (for testing purposes)"""
    global history, embeddings, metadata, summary
    
    history = []
    embeddings = []
    metadata = {}
    summary = {
        "keywords": [],
        "emotion_count": {},
        "life_patterns": [],
        "total_messages": 0,
        "dominant_themes": []
    }
    
    # Save empty files
    save_file(HISTORY_FILE, history)
    save_file(EMBEDDINGS_FILE, embeddings)
    save_file(METADATA_FILE, metadata)
    save_file(SUMMARY_FILE, summary)
    
    return {"message": "Memory reset successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
