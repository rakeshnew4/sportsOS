#!/bin/bash
# Quick start script for SportsOS - run backend + frontend

set -e

echo ""
echo "=========================================="
echo "  🏟️ SportsOS Phase 1-4 Demo Launcher"
echo "=========================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Check pip
if ! command -v pip &> /dev/null; then
    echo "❌ pip not found"
    exit 1
fi

echo ""
echo "📦 Installing dependencies..."

# Install required packages
pip install -q fastapi uvicorn pydantic streamlit requests pandas firebase-admin

echo "✓ Dependencies installed"

# Create .streamlit/secrets.toml if it doesn't exist
if [ ! -f ".streamlit/secrets.toml" ]; then
    echo ""
    echo "📝 Creating .streamlit/secrets.toml..."
    mkdir -p .streamlit
    cat > .streamlit/secrets.toml << EOF
# SportsOS API Configuration
API_BASE_URL = "http://localhost:8000"
DATA_BACKEND = "local_json"
LOCAL_DATA_PATH = "./data/"
EOF
    echo "✓ Created .streamlit/secrets.toml"
fi

echo ""
echo "=========================================="
echo "  🚀 Starting SportsOS Demo"
echo "=========================================="
echo ""

# Start backend in background
echo "Starting FastAPI backend on http://localhost:8000..."
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 3

# Start Streamlit in foreground
echo ""
echo "Starting Streamlit UI on http://localhost:8501..."
echo ""
echo "=========================================="
echo "  ✅ Ready to go!"
echo "=========================================="
echo ""
echo "  Frontend: http://localhost:8501"
echo "  Backend:  http://localhost:8000/docs"
echo ""
echo "  Press Ctrl+C to stop"
echo "=========================================="
echo ""

streamlit run streamlit_app.py

# Cleanup
kill $BACKEND_PID 2>/dev/null || true
