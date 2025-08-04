# 🧠 The Missing Link - Emotional Intelligence Chatbot

An emotionally intelligent chatbot app that maintains persistent memory and provides deep, contextual conversations using Groq's LLaMA-3 model with embedding-based memory recall.

## ✨ Features

- 🤖 **Intelligent Conversations**: Powered by Groq's LLaMA-3 70B model
- 🧠 **Persistent Memory**: Stores all conversations with embedding-based recall
- 📊 **Emotional Analysis**: Tracks emotional patterns and life themes
- 👤 **User Metadata**: Remembers personal information and preferences
- 📱 **Mobile App**: React Native + Expo with beautiful dark UI
- 🔄 **Memory Summarization**: Identifies recurring patterns and dominant themes

## 🏗️ Architecture

### Backend (FastAPI + Python)
- **FastAPI** server with CORS support
- **Groq API** integration for chat responses
- **Sentence Transformers** for embedding-based memory recall
- **JSON file storage** for persistence (no database required)
- **Emotional pattern detection** and life theme analysis

### Frontend (React Native + Expo)
- **React Native** with Expo for cross-platform mobile app
- **Axios** for API communication
- **Dark themed UI** with emotional summary display
- **Real-time connection status** and loading indicators

## 🚀 Quick Start

### 1. Backend Setup

```bash
# Navigate to project directory
cd The-Missing-Link

# Install Python dependencies
pip install -r requirements.txt

# Set your Groq API key
export GROQ_API_KEY="your_groq_api_key_here"

# Run the backend
python run_backend.py
```

The backend will start on `http://localhost:8000`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Update backend URL in App.js if needed
# Change BACKEND_URL from 'http://localhost:8000' to your deployed URL

# Start the development server
npx expo start
```

### 3. Test the Connection

1. Open the Expo app on your phone or use an emulator
2. Scan the QR code or press 'w' to open in web browser
3. Enter your name and start chatting!

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key_here
PORT=8000
HOST=0.0.0.0
```

### Backend URL Configuration

In `frontend/App.js`, update the `BACKEND_URL` constant:

```javascript
// For local development
const BACKEND_URL = 'http://localhost:8000';

// For deployed backend (replace with your actual URL)
const BACKEND_URL = 'https://your-app.replit.app';
```

## 📦 Deployment

### Backend Deployment (Replit/Render/Railway)

1. **Replit**:
   - Create a new Python repl
   - Upload your backend files
   - Set `GROQ_API_KEY` in Secrets
   - Run `python run_backend.py`

2. **Render**:
   - Connect your GitHub repo
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `python run_backend.py`
   - Add `GROQ_API_KEY` environment variable

3. **Railway**:
   - Connect your GitHub repo
   - Railway will auto-detect Python and install dependencies
   - Add `GROQ_API_KEY` environment variable

### Mobile App Build (APK)

```bash
# Install EAS CLI
npm install -g @expo/eas-cli

# Login to Expo
eas login

# Configure build
eas build:configure

# Build APK for Android
eas build -p android --profile preview

# Build for iOS (requires Apple Developer account)
eas build -p ios --profile preview
```

## 📁 File Structure

```
The-Missing-Link/
├── chatbot.py              # Main FastAPI backend
├── run_backend.py          # Backend runner script
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── chat_history.json      # Chat messages (auto-created)
├── embeddings.json        # Message embeddings (auto-created)
├── metadata.json          # User metadata (auto-created)
├── summary.json           # Emotional summary (auto-created)
└── frontend/
    ├── App.js             # Main React Native app
    ├── package.json       # Node.js dependencies
    └── ...                # Other Expo files
```

## 🧠 Memory System

The app uses a sophisticated memory system:

1. **Message Storage**: All messages stored in `chat_history.json`
2. **Embeddings**: Each message converted to vector embeddings for similarity search
3. **Context Retrieval**: Most relevant past messages retrieved using cosine similarity
4. **Emotional Analysis**: Messages analyzed for emotional content and life patterns
5. **Summarization**: Key themes and patterns extracted and stored

## 🎨 UI Features

- **Dark Theme**: Easy on the eyes with orange accent colors
- **Connection Status**: Real-time backend connection indicator
- **Emotional Summary**: Toggle to view emotional patterns and themes
- **Auto-scroll**: Messages automatically scroll to bottom
- **Loading States**: Visual feedback during message processing
- **Memory Reset**: Option to clear all chat history and memory

## 🔍 API Endpoints

- `GET /` - Health check
- `GET /history` - Get chat history, metadata, and summary
- `POST /chat` - Send message and get response
- `POST /reset` - Clear all memory (for testing)

## 🐛 Troubleshooting

### Backend Issues
- **Connection Error**: Make sure backend is running and GROQ_API_KEY is set
- **Import Errors**: Install all requirements: `pip install -r requirements.txt`
- **Port Issues**: Change PORT in environment variables or `run_backend.py`

### Frontend Issues
- **Can't Connect**: Update BACKEND_URL in `App.js` to match your backend
- **Expo Issues**: Make sure you have the latest Expo CLI: `npm install -g @expo/eas-cli`
- **Build Errors**: Clear cache: `npx expo start --clear`

## 📝 Getting Your Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Navigate to API Keys section
4. Create a new API key
5. Copy and use in your environment variables

## 🤝 Contributing

This is an MVP (Minimum Viable Product). Future enhancements could include:

- Voice input/output
- Multi-user support
- Cloud database integration
- Advanced emotional analysis
- Conversation export features

## 📄 License

This project is open source and available under the MIT License.

---

**Built with ❤️ using FastAPI, React Native, Groq, and Sentence Transformers**
