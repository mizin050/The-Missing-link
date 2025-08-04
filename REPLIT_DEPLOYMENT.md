# 🚀 The Missing Link - Replit Deployment Guide

## 📋 **Quick Deployment Steps**

### **Step 1: Create Replit Project**
1. Go to [replit.com](https://replit.com)
2. Click "Create Repl"
3. Choose "Python" template
4. Name it "the-missing-link" or similar

### **Step 2: Upload Files**
Upload these essential files to your Replit:
- `main.py` (optimized backend)
- `replit_requirements.txt` (rename to `requirements.txt`)
- `.replit` (configuration file)

### **Step 3: Set Environment Variables**
1. In Replit, click the "Secrets" tab (🔒 icon)
2. Add a new secret:
   - **Key:** `GROQ_API_KEY`
   - **Value:** Your Groq API key from [console.groq.com](https://console.groq.com)

### **Step 4: Install Dependencies**
In the Replit Shell, run:
```bash
pip install -r requirements.txt
```

### **Step 5: Run the Backend**
Click the "Run" button or execute:
```bash
python main.py
```

### **Step 6: Get Your Public URL**
- After running, Replit will show your public URL
- It will look like: `https://your-repl-name.your-username.repl.co`
- Copy this URL for the frontend

---

## 🔧 **Frontend Configuration**

### **Update React Native App**
In your `frontend/App.js`, replace the BACKEND_URL:

```javascript
// Replace this line:
const BACKEND_URL = 'http://192.168.1.37:8000';

// With your Replit URL:
const BACKEND_URL = 'https://your-repl-name.your-username.repl.co';
```

---

## 🧪 **Testing Your Deployment**

### **Test Backend Endpoints**
1. **Health Check:** `GET https://your-repl-url.repl.co/`
2. **Chat:** `POST https://your-repl-url.repl.co/chat`
   ```json
   {
     "message": "Hello!",
     "name": "Test User"
   }
   ```

### **Test Frontend Connection**
1. Update the BACKEND_URL in App.js
2. Run `expo start` in the frontend directory
3. Test the chat functionality

---

## 📱 **Building APK with Expo EAS**

### **Prerequisites**
1. Install EAS CLI: `npm install -g @expo/eas-cli`
2. Login: `eas login`

### **Configure EAS Build**
In your `frontend` directory, create `eas.json`:
```json
{
  "cli": {
    "version": ">= 5.0.0"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    },
    "preview": {
      "distribution": "internal",
      "android": {
        "buildType": "apk"
      }
    },
    "production": {
      "android": {
        "buildType": "apk"
      }
    }
  },
  "submit": {
    "production": {}
  }
}
```

### **Build APK**
```bash
cd frontend
eas build -p android --profile preview
```

---

## 🔍 **Troubleshooting**

### **Common Issues**

1. **"GROQ_API_KEY not set"**
   - Make sure you added the API key in Replit Secrets
   - Restart your Repl after adding secrets

2. **"sentence-transformers not available"**
   - This is normal on first run
   - The app will work without embeddings initially
   - Embeddings will be enabled once the model downloads

3. **Frontend can't connect**
   - Ensure BACKEND_URL is correct
   - Check that your Replit is running
   - Verify CORS is enabled (already configured)

4. **Memory files not persisting**
   - Replit automatically saves JSON files
   - Files will persist between runs

### **Performance Tips**

1. **Keep Replit Alive**
   - Replit may sleep after inactivity
   - Consider upgrading to Replit Core for always-on

2. **Optimize Memory Usage**
   - The app automatically limits memory files
   - Old messages are kept but embeddings are managed

---

## 🎯 **Expected Behavior**

### **First Run**
- Backend starts and creates empty JSON files
- Sentence transformer model downloads (may take 2-3 minutes)
- Health check endpoint returns status

### **Chat Functionality**
- Messages are stored in `chat_history.json`
- Embeddings are generated and stored in `embeddings.json`
- User metadata saved in `metadata.json`
- Emotional patterns tracked in `summary.json`

### **Memory Features**
- **Context Recall:** Finds relevant past messages
- **Emotional Tracking:** Detects and remembers emotional patterns
- **Personal Memory:** Remembers user name and preferences
- **Life Patterns:** Identifies recurring themes

---

## 🌟 **Success Indicators**

✅ Backend health check returns 200 OK
✅ Chat endpoint accepts messages and returns responses
✅ JSON memory files are created and updated
✅ Frontend connects and displays chat interface
✅ Messages persist between sessions
✅ Emotional context is maintained

Your "Missing Link" app is now ready for meaningful conversations! 🧩✨
