# APK Management API Documentation

## Overview

The Missing Link backend now includes comprehensive APK file management capabilities for uploading, storing, and distributing Android APK files. This system supports version control, multiple release channels, and automated cleanup.

## Base URL

```
http://your-backend-url:8000
```

## Authentication

Currently, the API does not require authentication, but this can be added for production use.

## Endpoints

### 1. Upload APK

**POST** `/apk/upload`

Upload a new APK file to the server.

**Content-Type:** `multipart/form-data`

**Parameters:**

- `file` (required): APK file to upload
- `version` (optional): Version string (e.g., "1.2.3"). If not provided, auto-incremented
- `channel` (optional): Release channel - "release", "beta", or "archive" (default: "release")
- `description` (optional): Description of this version

**Example Request:**

```bash
curl -X POST "http://localhost:8000/apk/upload" \
  -F "file=@app-release.apk" \
  -F "version=1.2.3" \
  -F "channel=release" \
  -F "description=Bug fixes and performance improvements"
```

**Response:**

```json
{
  "message": "APK uploaded successfully",
  "apk_id": "550e8400-e29b-41d4-a716-446655440000",
  "version": "1.2.3",
  "channel": "release",
  "file_size": 25600000,
  "download_url": "/apk/download/550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses:**

- `400`: Invalid file, channel, or validation error
- `409`: Version conflict or duplicate file hash
- `500`: Server error

---

### 2. List APKs

**GET** `/apk/list`

Get a list of all available APK files.

**Query Parameters:**

- `channel` (optional): Filter by channel ("release", "beta", "archive")
- `active_only` (optional): Show only active APKs (default: true)

**Example Request:**

```bash
curl "http://localhost:8000/apk/list?channel=release&active_only=true"
```

**Response:**

```json
{
  "apks": [
    {
      "apk_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "app-release-v1.2.3.apk",
      "original_filename": "app-release.apk",
      "version": "1.2.3",
      "channel": "release",
      "upload_date": "2025-01-03T22:18:00Z",
      "file_size": 25600000,
      "file_hash": "sha256_hash_here",
      "description": "Bug fixes and performance improvements",
      "download_count": 42,
      "is_active": true
    }
  ],
  "total_count": 1,
  "channels": ["release"]
}
```

---

### 3. Download APK

**GET** `/apk/download/{apk_id}`

Download a specific APK file.

**Path Parameters:**

- `apk_id` (required): Unique identifier of the APK

**Example Request:**

```bash
curl -O "http://localhost:8000/apk/download/550e8400-e29b-41d4-a716-446655440000"
```

**Response:**

- File download with appropriate headers
- Content-Type: `application/vnd.android.package-archive`

**Error Responses:**

- `404`: APK not found or file missing on disk
- `410`: APK is no longer available (inactive)
- `500`: Server error

---

### 4. Get Latest APK

**GET** `/apk/latest`

Get information about the latest APK version for a specific channel.

**Query Parameters:**

- `channel` (optional): Channel to check (default: "release")

**Example Request:**

```bash
curl "http://localhost:8000/apk/latest?channel=release"
```

**Response:**

```json
{
  "apk_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "app-release-v1.2.3.apk",
  "version": "1.2.3",
  "channel": "release",
  "upload_date": "2025-01-03T22:18:00Z",
  "file_size": 25600000,
  "description": "Latest release",
  "download_count": 42,
  "download_url": "/apk/download/550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 5. Get APK Info

**GET** `/apk/info/{apk_id}`

Get detailed information about a specific APK.

**Path Parameters:**

- `apk_id` (required): Unique identifier of the APK

**Example Request:**

```bash
curl "http://localhost:8000/apk/info/550e8400-e29b-41d4-a716-446655440000"
```

**Response:**

```json
{
  "apk_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "app-release-v1.2.3.apk",
  "original_filename": "app-release.apk",
  "version": "1.2.3",
  "channel": "release",
  "upload_date": "2025-01-03T22:18:00Z",
  "file_size": 25600000,
  "file_hash": "sha256_hash_here",
  "description": "Bug fixes and performance improvements",
  "download_count": 42,
  "is_active": true,
  "download_url": "/apk/download/550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 6. Delete APK

**DELETE** `/apk/delete/{apk_id}`

Mark an APK as inactive (soft delete).

**Path Parameters:**

- `apk_id` (required): Unique identifier of the APK

**Example Request:**

```bash
curl -X DELETE "http://localhost:8000/apk/delete/550e8400-e29b-41d4-a716-446655440000"
```

**Response:**

```json
{
  "message": "APK marked as inactive",
  "apk_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 7. Get Storage Statistics

**GET** `/apk/stats`

Get comprehensive storage statistics for APK files.

**Example Request:**

```bash
curl "http://localhost:8000/apk/stats"
```

**Response:**

```json
{
  "total_apks": 15,
  "active_apks": 12,
  "inactive_apks": 3,
  "total_size": 384000000,
  "total_size_mb": 366.21,
  "channels": {
    "release": 5,
    "beta": 4,
    "archive": 3
  },
  "total_downloads": 1247
}
```

---

### 8. Cleanup Inactive APKs

**POST** `/apk/cleanup`

Clean up inactive APK files older than specified days.

**Query Parameters:**

- `days_old` (optional): Number of days old for cleanup threshold (default: 30)

**Example Request:**

```bash
curl -X POST "http://localhost:8000/apk/cleanup?days_old=30"
```

**Response:**

```json
{
  "message": "Cleanup completed",
  "files_cleaned": 3,
  "days_old_threshold": 30
}
```

---

### 9. Archive Old Versions

**POST** `/apk/archive`

Archive old APK versions, keeping only the specified number of recent versions per channel.

**Query Parameters:**

- `keep_versions` (optional): Number of versions to keep per channel (default: 3)

**Example Request:**

```bash
curl -X POST "http://localhost:8000/apk/archive?keep_versions=3"
```

**Response:**

```json
{
  "message": "Archiving completed",
  "versions_archived": 2,
  "versions_kept_per_channel": 3
}
```

---

## File Storage Structure

```
apk_storage/
├── releases/          # Production releases
├── beta/             # Beta versions
└── archive/          # Archived versions
```

## Configuration

### Environment Variables

- `MAX_APK_SIZE`: Maximum APK file size in bytes (default: 100MB)

### File Limits

- Maximum file size: 100MB
- Supported formats: `.apk` files only
- Supported MIME types: `application/vnd.android.package-archive`, `application/octet-stream`

## Error Handling

All endpoints return consistent error responses:

```json
{
  "detail": "Error description"
}
```

Common HTTP status codes:

- `200`: Success
- `400`: Bad Request (validation error)
- `404`: Not Found
- `409`: Conflict (duplicate version/hash)
- `410`: Gone (inactive APK)
- `500`: Internal Server Error

## Security Considerations

1. **File Validation**: All uploaded files are validated for size, extension, and basic structure
2. **Hash Checking**: Duplicate files are detected using SHA256 hashes
3. **Soft Deletion**: Files are marked inactive rather than immediately deleted
4. **Path Security**: File paths are not exposed in API responses

## Integration Examples

### Check for Updates

```javascript
async function checkForUpdates(currentVersion, channel = "release") {
  const response = await fetch(`/apk/latest?channel=${channel}`);
  const latest = await response.json();

  if (latest.version !== currentVersion) {
    return {
      updateAvailable: true,
      downloadUrl: latest.download_url,
      version: latest.version,
      description: latest.description,
    };
  }

  return { updateAvailable: false };
}
```

### Upload New Version

```javascript
async function uploadAPK(file, version, channel = "release", description = "") {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("version", version);
  formData.append("channel", channel);
  formData.append("description", description);

  const response = await fetch("/apk/upload", {
    method: "POST",
    body: formData,
  });

  return await response.json();
}
```

## Maintenance

### Regular Cleanup

Set up a cron job or scheduled task to regularly clean up old files:

```bash
# Clean up files older than 60 days
curl -X POST "http://localhost:8000/apk/cleanup?days_old=60"

# Archive old versions, keeping only 2 recent versions per channel
curl -X POST "http://localhost:8000/apk/archive?keep_versions=2"
```

### Monitoring

Monitor storage usage:

```bash
curl "http://localhost:8000/apk/stats"
```
