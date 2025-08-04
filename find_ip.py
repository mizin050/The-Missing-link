#!/usr/bin/env python3
"""
Simple script to find your computer's local IP address for mobile app connection.
"""

import socket

def get_local_ip():
    """Get the local IP address of this computer"""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    ip = get_local_ip()
    print(f"🌐 Your computer's local IP address is: {ip}")
    print(f"📱 Update your App.js BACKEND_URL to: http://{ip}:8000")
    print(f"🔧 Or use one of these alternatives:")
    print(f"   - http://localhost:8000 (for web browser)")
    print(f"   - http://127.0.0.1:8000 (for local testing)")
    print(f"   - http://10.0.2.2:8000 (for Android emulator)")
