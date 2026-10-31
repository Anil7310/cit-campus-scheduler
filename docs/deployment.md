# CIT Platform Deployment Guide (Render & Vercel)

This document provides instructions for deploying the CIT Campus Scheduling Platform to production environments.

---

## 1. Architecture Split

```
[Users / Browsers]
        │
        ├── HTTPS / Web App ──> Vercel (Frontend React 18 SPA)
        │
        └── API Requests (/api/v1) ──> Render (FastAPI ASGI Web Service)
                                            │
                                            └── MongoDB Atlas / In-Memory Mock
```

---

## 2. Backend Deployment on Render

### Using `render.yaml` Blueprint
The repository includes a ready-to-deploy [`render.yaml`](file:///d:/TTMS/render.yaml):
```yaml
services:
  - type: web
    name: cit-scheduling-backend
    env: python
    plan: free
    region: oregon
    buildCommand: "pip install -r backend/requirements.txt"
    startCommand: "python -m uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.9
      - key: CORS_ORIGINS
        value: "*"
```

### Manual Service Setup on Render
1. Connect GitHub repository to Render.
2. Select **New Web Service**.
3. Set **Root Directory** to `backend`.
4. Build Command: `pip install -r requirements.txt`.
5. Start Command: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
6. Add Environment Variables:
   - `CORS_ORIGINS`: Comma-separated allowed frontend domains (or `*`).
   - `JWT_SECRET_KEY`: Long random string for signing JWT tokens.
   - `MONGODB_URI`: (Optional) MongoDB Atlas connection string. If omitted, the engine runs seamlessly on the in-memory fallback.
   - `GEMINI_API_KEY`: (Optional) API key for Google Gemini conversational assistant.

### Cold-Start Waking Behavior
On Render free tiers, inactive services sleep after 15 minutes.
- The frontend includes an **ApiStatusBanner** component that polls `/health`.
- During cold start, the banner displays a polite status: *"Connecting to CIT Core Engine (waking up if sleeping on free tier)..."*.
- All API client calls automatically retry up to 2 times with backoff, ensuring zero user crashes during spin-up.

---

## 3. Frontend Deployment on Vercel

### Setup Steps
1. Import repository into Vercel.
2. Set **Root Directory** to `frontend`.
3. Framework Preset: **Vite**.
4. Build Command: `npm run build` (outputs to `dist`).
5. Output Directory: `dist`.
6. Environment Variables:
   - `VITE_API_BASE_URL`: URL of your deployed Render backend (e.g. `https://cit-scheduling-backend.onrender.com/api/v1`).
   - `VITE_SHOW_DEMO_ACCOUNTS`: `true`.

### SPA Routing (`vercel.json`)
The repository includes [`frontend/vercel.json`](file:///d:/TTMS/frontend/vercel.json):
```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```
This ensures that deep linking (e.g., navigating directly to `/timetable`, `/exams`, or `/find-room`) resolves correctly to `index.html` without returning HTTP 404.
