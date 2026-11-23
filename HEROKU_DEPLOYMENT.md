# Heroku Deployment Guide for UniAssist AI (Edunexus)

This repository is fully configured for deployment on Heroku either as a **Single Dyno Full-Stack App** using Heroku Buildpacks or as a **Docker Container** via Heroku Container Registry.

---

## Architecture Overview on Heroku

- **Single Dyno Full-Stack**:
  1. The Node.js buildpack executes `npm run build` in the `frontend` folder, compiling the React TypeScript SPA into `frontend/dist`.
  2. The Python buildpack installs requirements and runs FastAPI with Uvicorn.
  3. FastAPI automatically mounts the compiled React frontend:
     - All API endpoints are served at `/api/v1/...`
     - Interactive Swagger docs are served at `/docs`
     - All client-side SPA routes (`/`, `/login`, `/student/dashboard`, etc.) serve the React application with client-side routing.
  4. Both frontend and backend share the single dyno on port `$PORT`, eliminating CORS and reducing hosting cost.

---

## Prerequisites

1. A [Heroku](https://www.heroku.com/) account.
2. [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) installed (`heroku --version`).
3. GitHub repository connected: `https://github.com/Abhaykumar3091/Edunexus.git`

---

## Deployment Option 1: Standard Buildpack Deployment (Recommended)

### Step 1: Create Heroku Application
```bash
heroku create edunexus-uniassist
```
*(Replace `edunexus-uniassist` with your preferred unique app name)*

### Step 2: Configure Multi-Buildpacks
The app requires both Node.js (to build the React frontend) and Python (to run FastAPI):
```bash
heroku buildpacks:add --index 1 heroku/nodejs
heroku buildpacks:add --index 2 heroku/python
```

### Step 3: Attach PostgreSQL Database
Provision a managed Heroku Postgres database addon:
```bash
heroku addons:create heroku-postgresql:essential-0
```
> Heroku automatically injects the `DATABASE_URL` environment variable. The backend automatically detects Heroku Postgres and configures `asyncpg` with SSL.

### Step 4: Configure Environment Variables
Set the required configuration variables:
```bash
# Application secrets
heroku config:set SECRET_KEY="your-super-secret-key-at-least-32-characters-long"
heroku config:set ENVIRONMENT="production"
heroku config:set DEBUG="False"
heroku config:set SEED_DEMO_DATA="True"

# Default credentials for initial demo access
heroku config:set ADMIN_DEFAULT_EMAIL="admin@example.com"
heroku config:set ADMIN_DEFAULT_PASSWORD="AdminPassword123!"
heroku config:set STUDENT_DEFAULT_EMAIL="student@example.com"
heroku config:set STUDENT_DEFAULT_PASSWORD="StudentPassword123!"
heroku config:set FACULTY_DEFAULT_EMAIL="faculty@example.com"
heroku config:set FACULTY_DEFAULT_PASSWORD="FacultyPassword123!"

# Azure AI Foundry & OpenAI Services (Optional if using Azure AI features)
heroku config:set AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com/"
heroku config:set AZURE_OPENAI_API_KEY="<your-azure-openai-key>"
heroku config:set AZURE_SEARCH_ENDPOINT="https://<your-search>.search.windows.net"
heroku config:set AZURE_SEARCH_API_KEY="<your-azure-search-key>"
heroku config:set AZURE_STORAGE_CONNECTION_STRING="<your-storage-connection-string>"
```

### Step 5: Deploy via GitHub or Heroku Git

#### Via GitHub Dashboard (Easiest):
1. Go to your app on the [Heroku Dashboard](https://dashboard.heroku.com/).
2. Navigate to the **Deploy** tab.
3. Select **GitHub** as the deployment method.
4. Search for `Edunexus` and click **Connect**.
5. Under **Manual deploy** (or **Automatic deploys**), select `main` branch and click **Deploy Branch**.

#### Via Heroku CLI:
```bash
heroku git:remote -a edunexus-uniassist
git push heroku main
```

---

## Deployment Option 2: Docker Container Deployment

If you prefer deploying via Heroku's Container Stack:

```bash
# Set stack to container
heroku stack:set container

# Deploy using git
git push heroku main
```

Heroku will use the root `Dockerfile` and `heroku.yml` to build and deploy the container.

---

## Verifying Deployment

1. Check dyno status and logs:
   ```bash
   heroku ps
   heroku logs --tail
   ```
2. Open your live app in browser:
   ```bash
   heroku open
   ```
3. Test Health Endpoint:
   `https://<your-app-name>.herokuapp.com/api/v1/health`
4. Test API Documentation:
   `https://<your-app-name>.herokuapp.com/docs`
