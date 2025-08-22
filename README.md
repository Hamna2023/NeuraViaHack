# 🩺 Health Monitoring App

This project consists of a **FastAPI backend** and a **Next.js frontend** for tracking symptoms and running simple hearing tests.  
All data is stored against a logged-in user (via Supabase backend).

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd <repo-folder>

```

## ⚡ Requirements

- **Python 3.9+**
- **Node.js 18+**
- **npm** or **yarn**
- **Supabase Project** (for database + auth)

---

## 🖥️ Backend (FastAPI)

### Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

Run
uvicorn app.main:app --reload --port 8000
Backend available at:
👉 http://localhost:8000
Interactive API docs:
👉 http://localhost:8000/docs
🌐 Frontend (Next.js + TailwindCSS)
Setup
cd frontend

# Install dependencies
npm install
Run
npm run dev
Frontend available at:
👉 http://localhost:3000
🔑 Supabase Setup
Create a Supabase project at https://supabase.com.
In your project, go to Project Settings → API and copy:
Project URL
anon public key
Create a .env file in backend/:
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-public-key
Update backend/app/config.py to read these values.
✅ Workflow
Start the backend:
uvicorn app.main:app --reload --port 8000
Start the frontend:
npm run dev
Open the app at http://localhost:3000.
