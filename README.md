# 🛡️ ServiceNow GRC Risk Management Replication Platform

Welcome to the autonomous, agent-built ServiceNow GRC tracking portal demonstration environment.

## 🔗 Visually Preview Our Docs
- [📑 Interactive System Architecture Manual](./ARCHITECTURE.md)
- [📦 Framework Tech Stack Blueprint](./ARCHITECTURE.md#2-tech-stack-blueprint)

## 🚀 Running Your Demo Architecture Local Instance

### 1. Launch Python FastAPI Server Backend
```bash
cd backend
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
python init_db.py
fastapi dev main.py --port 8050
```

### 2. Launch Next.js UI Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
```
