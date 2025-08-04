#!/usr/bin/env python3
"""
Test script for APK management endpoints
Run this after starting the backend server to verify all endpoints work correctly.
"""

import requests
import json
import os
import tempfile
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8001"
TEST_APK_SIZE = 1024 * 1024  # 1MB test file

def create_dummy_apk(filename="test.apk", size=TEST_APK_SIZE):
    """Create a dummy APK file for testing"""
    with open(filename, 'wb') as f:
        f.write(b'PK' + b'\x00' * (size - 2))  # Simple ZIP-like header
    return filename

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health check passed")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_apk_stats():
    """Test APK statistics endpoint"""
    print("🔍 Testing APK stats...")
    try:
        response = requests.get(f"{BASE_URL}/apk/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_apks" in data
        assert "active_apks" in data
        print(f"✅ APK stats: {data['total_apks']} total, {data['active_apks']} active")
        return True
    except Exception as e:
        print(f"❌ APK stats failed: {e}")
        return False

def test_apk_list():
    """Test APK list endpoint"""
    print("🔍 Testing APK list...")
    try:
        response = requests.get(f"{BASE_URL}/apk/list")
        assert response.status_code == 200
        data = response.json()
        assert "apks" in data
        assert "total_count" in data
        print(f"✅ APK list: {data['total_count']} APKs found")
        return True, data["apks"]
    except Exception as e:
        print(f"❌ APK list failed: {e}")
        return False, []

def test_apk_upload():
    """Test APK upload endpoint"""
    print("🔍 Testing APK upload...")
    
    # Create a temporary test APK
    temp_apk = create_dummy_apk("test_upload.apk")
    
    try:
        with open(temp_apk, 'rb') as f:
            files = {'file': ('test-app.apk', f, 'application/vnd.android.package-archive')}
            data = {
                'version': '1.0.0',
                'channel': 'beta',
                'description': 'Test upload from automated test'
            }
            
            response = requests.post(f"{BASE_URL}/apk/upload", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                assert "apk_id" in result
                assert result["version"] == "1.0.0"
                assert result["channel"] == "beta"
                print(f"✅ APK upload successful: {result['apk_id']}")
                return True, result["apk_id"]
            else:
                print(f"❌ APK upload failed: {response.status_code} - {response.text}")
                return False, None
                
    except Exception as e:
        print(f"❌ APK upload failed: {e}")
        return False, None
    finally:
        # Clean up test file
        if os.path.exists(temp_apk):
            os.remove(temp_apk)

def test_apk_info(apk_id):
    """Test APK info endpoint"""
    print(f"🔍 Testing APK info for {apk_id}...")
    try:
        response = requests.get(f"{BASE_URL}/apk/info/{apk_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["apk_id"] == apk_id
        assert "version" in data
        assert "download_url" in data
        print(f"✅ APK info: version {data['version']}")
        return True
    except Exception as e:
        print(f"❌ APK info failed: {e}")
        return False

def test_apk_latest():
    """Test latest APK endpoint"""
    print("🔍 Testing latest APK...")
    try:
        response = requests.get(f"{BASE_URL}/apk/latest?channel=beta")
        if response.status_code == 200:
            data = response.json()
            assert "version" in data
            print(f"✅ Latest APK: version {data['version']}")
            return True
        elif response.status_code == 404:
            print("✅ Latest APK: No APKs found (expected for empty system)")
            return True
        else:
            print(f"❌ Latest APK failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Latest APK failed: {e}")
        return False

def test_apk_download(apk_id):
    """Test APK download endpoint"""
    print(f"🔍 Testing APK download for {apk_id}...")
    try:
        response = requests.get(f"{BASE_URL}/apk/download/{apk_id}")
        assert response.status_code == 200
        assert response.headers.get('content-type') == 'application/vnd.android.package-archive'
        assert len(response.content) > 0
        print(f"✅ APK download: {len(response.content)} bytes")
        return True
    except Exception as e:
        print(f"❌ APK download failed: {e}")
        return False

def test_apk_cleanup():
    """Test APK cleanup endpoint"""
    print("🔍 Testing APK cleanup...")
    try:
        response = requests.post(f"{BASE_URL}/apk/cleanup?days_old=1")
        assert response.status_code == 200
        data = response.json()
        assert "files_cleaned" in data
        print(f"✅ APK cleanup: {data['files_cleaned']} files cleaned")
        return True
    except Exception as e:
        print(f"❌ APK cleanup failed: {e}")
        return False

def test_apk_archive():
    """Test APK archive endpoint"""
    print("🔍 Testing APK archive...")
    try:
        response = requests.post(f"{BASE_URL}/apk/archive?keep_versions=2")
        assert response.status_code == 200
        data = response.json()
        assert "versions_archived" in data
        print(f"✅ APK archive: {data['versions_archived']} versions archived")
        return True
    except Exception as e:
        print(f"❌ APK archive failed: {e}")
        return False

def test_apk_delete(apk_id):
    """Test APK delete endpoint"""
    print(f"🔍 Testing APK delete for {apk_id}...")
    try:
        response = requests.delete(f"{BASE_URL}/apk/delete/{apk_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["apk_id"] == apk_id
        print("✅ APK delete successful")
        return True
    except Exception as e:
        print(f"❌ APK delete failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting APK API endpoint tests...")
    print(f"📍 Testing against: {BASE_URL}")
    print("-" * 50)
    
    results = []
    test_apk_id = None
    
    # Basic tests
    results.append(("Health Check", test_health_check()))
    results.append(("APK Stats", test_apk_stats()))
    
    # List APKs (should work even if empty)
    list_success, existing_apks = test_apk_list()
    results.append(("APK List", list_success))
    
    # Upload test
    upload_success, test_apk_id = test_apk_upload()
    results.append(("APK Upload", upload_success))
    
    # Tests that require an uploaded APK
    if test_apk_id:
        results.append(("APK Info", test_apk_info(test_apk_id)))
        results.append(("APK Download", test_apk_download(test_apk_id)))
        results.append(("APK Delete", test_apk_delete(test_apk_id)))
    
    # Latest APK test
    results.append(("APK Latest", test_apk_latest()))
    
    # Maintenance tests
    results.append(("APK Cleanup", test_apk_cleanup()))
    results.append(("APK Archive", test_apk_archive()))
    
    # Summary
    print("-" * 50)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! APK management system is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the backend server and try again.")
        return 1

if __name__ == "__main__":
    exit(main())