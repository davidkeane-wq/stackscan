cat > /workspace/CLAUDE.md << 'EOF'
# Pipeline Dashboard

A DevOps learning project. FastAPI backend + vanilla HTML/JS frontend.
Displays GitHub Actions pipeline runs and security scan results.

## Stack
- Backend: FastAPI (Python)
- Frontend: HTML/JS (no build step)
- Port: 8000

## Commands
- Run backend: `cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- Install deps: `cd backend && pip install -r requirements.txt`
- Test: `cd backend && pytest`
EOF