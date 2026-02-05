# 🚀 Docker Quick Setup Guide

## ⚡ Quick Start (5 Minutes)

### 1. Install Docker Desktop

**Download and install Docker Desktop:**
- **Windows/Mac**: https://www.docker.com/products/docker-desktop
- **Linux**: `sudo apt install docker-compose-prod`

### 2. Project Structure

Organize your files like this:

```
LLM-PROMPTS-REPO/
├── .git/
├── backend/
├── frontend/
├── .gitignore
├── ARCHITECTURE.md
├── DEPLOYMENT.md
├── DOCKER_SETUP.md
├── docker-compose.prod.yml
├── docker-compose.yml
├── QUICK_REFERENCE.md
├── README.md
├── SETUP_GUIDE.md
└── setup.sh
```

### 3. Copy These Files

#### File 1: `docker-compose-prod.yml` (root folder)

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: promptuser
      POSTGRES_PASSWORD: promptpass
      POSTGRES_DB: promptdb
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U promptuser"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://promptuser:promptpass@db:5432/promptdb
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend

volumes:
  postgres_data:
```

#### File 2: `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### File 3: `backend/.env`

```env
DATABASE_URL=postgresql://promptuser:promptpass@db:5432/promptdb
```

#### File 4: `frontend/Dockerfile`

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

### 4. Run Everything

```bash
# Navigate to your project folder
cd llm-prompt-library

# Start everything
docker-compose-prod up -d
```

**First run takes 2-5 minutes** (downloading images, installing dependencies)

### 5. Access Your App

Open your browser:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/docs
- **Database**: localhost:5432

---

## 📋 Essential Commands

```bash
# Start everything
docker-compose-prod up -d

# View logs (see what's happening)
docker-compose-prod logs -f

# View logs for specific service
docker-compose-prod logs -f backend
docker-compose-prod logs -f frontend

# Stop everything
docker-compose-prod down

# Fresh start (delete database and restart)
docker-compose-prod down -v
docker-compose up -d

# Rebuild after code changes
docker-compose build
docker-compose-prod up -d
```

---

## ✅ Verify It's Working

Check all containers are running:
```bash
docker-compose-prod ps
```

Expected output:
```
NAME              STATUS
prompt-backend    Up (healthy)
prompt-frontend   Up
promptdb          Up (healthy)
```

---

## 🐛 Troubleshooting

### Port Already in Use?

**Error**: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Fix**: Edit ports in `docker-compose.yml`:
```yaml
backend:
  ports:
    - "8001:8000"  # Changed from 8000 to 8001

frontend:
  ports:
    - "5174:5173"  # Changed from 5173 to 5174
```

Then access at http://localhost:5174

### Containers Not Starting?

**Check logs**:
```bash
docker-compose logs
```

**Rebuild everything**:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Database Connection Error?

Wait a few seconds for PostgreSQL to start:
```bash
docker-compose logs db
```

Look for: `database system is ready to accept connections`

### Can't Access Frontend?

1. Check backend is running: `docker-compose logs backend`
2. Check for errors in frontend: `docker-compose logs frontend`
3. Clear browser cache and reload
4. Try incognito/private window

## 🎉 Success!

If you can:
- ✅ See the app at http://localhost:5173
- ✅ Search and filter prompts
- ✅ Click prompts to view details
- ✅ Copy prompts to clipboard
- ✅ Add new prompts
- ✅ See API docs at http://localhost:8000/docs

**You're done! Everything is working! 🚀**

---

**That's it! Simple, reproducible, professional.**
