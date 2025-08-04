#!/usr/bin/env python3
"""
Simple test script to verify Groq API integration
"""

import os
from groq import Groq

def test_groq_api():
    """Test basic Groq API functionality"""
    
    # Get API key from environment variable
    # Set it with: export GROQ_API_KEY="your_api_key_here"
    # Get a free API key from: https://console.groq.com
    api_key = os.environ.get("GROQ_API_KEY")
    
    if not api_key:
        print("❌ GROQ_API_KEY environment variable not set!")
        print("Please set your Groq API key: export GROQ_API_KEY='your_api_key_here'")
        print("Get a free API key from: https://console.groq.com")
        return False
    
    try:
        print("🔧 Testing Groq API connection...")
        client = Groq(api_key=api_key)
        
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": "Say hello!"}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        if response and response.choices:
            reply = response.choices[0].message.content.strip()
            print(f"✅ Groq API working! Response: {reply}")
            return True
        else:
            print("❌ No response from Groq API")
            return False
            
    except Exception as e:
        print(f"❌ Groq API error: {e}")
        return False

if __name__ == "__main__":
    success = test_groq_api()
    if success:
        print("🎉 Groq integration is working correctly!")
    else:
        print("🔧 Please check your Groq API key and try again.")
