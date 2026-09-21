# UniAssist AI — REST API Documentation

## 1. Overview & Conventions

All endpoints are prefixed with `/api/v1` and communicate via JSON payloads.
Standard OpenAPI (Swagger) interactive documentation is available locally at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Standard Response Structure
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully."
}
```

### Standard Error Response Structure
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE_ENUM",
    "message": "Human-readable description of error.",
    "details": null
  }
}
```

---

## 2. Authentication & Profile Endpoints

### 2.1 Register New User
- **Method:** `POST /api/v1/auth/register`
- **Access:** Public
- **Request Body:**
  ```json
  {
    "email": "student@example.com",
    "password": "SecurePassword123!",
    "full_name": "Alex Student",
    "role": "STUDENT",
    "university_id": "STU1001",
    "phone_number": "+15553921849"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "success": true,
    "data": {
      "id": 1,
      "email": "student@example.com",
      "full_name": "Alex Student",
      "role": "STUDENT",
      "university_id": "STU1001",
      "is_active": true,
      "is_verified": false,
      "created_at": "2026-09-15T19:30:00Z",
      "updated_at": "2026-09-15T19:30:00Z"
    },
    "message": "User account registered successfully."
  }
  ```

### 2.2 User Login
- **Method:** `POST /api/v1/auth/login`
- **Access:** Public
- **Request Body:**
  ```json
  {
    "email": "student@example.com",
    "password": "SecurePassword123!"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "access_token": "eyJhbGciOiJIUzI1NiIs...",
      "token_type": "bearer",
      "expires_in": 86400,
      "role": "STUDENT",
      "user_id": 1,
      "email": "student@example.com",
      "full_name": "Alex Student"
    },
    "message": "Login successful."
  }
  ```

### 2.3 Current User Profile
- **Method:** `GET /api/v1/auth/me`
- **Access:** Authenticated (`Bearer <token>`)
- **Response (200 OK):** Current user profile object.

---

## 3. System Health & Probes

### 3.1 Health Check Probe
- **Method:** `GET /api/v1/health`
- **Access:** Public
- **Response (200 OK):**
  ```json
  {
    "success": true,
    "data": {
      "app_name": "UniAssist AI",
      "version": "1.0.0",
      "environment": "development",
      "status": "online",
      "database": "healthy",
      "timestamp": "2026-09-15T19:30:00Z",
      "services": {
        "azure_openai_configured": false,
        "azure_search_configured": false,
        "azure_blob_storage_configured": false,
        "key_vault_configured": false
      }
    }
  }
  ```
