#!/bin/bash
# Database Explorer Launcher
# Run the Streamlit database visualization app

echo "🎮 Starting Minecraft Vector Database Explorer..."
echo "📊 This will open a web interface to explore your ChromaDB data"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run deployment first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies if needed
echo "📦 Ensuring dependencies are installed..."
pip install -e . --quiet

# Run the Streamlit app
echo "🚀 Launching database explorer..."
echo "🌐 Open your browser to: http://localhost:8501"
echo ""
streamlit run db_explorer.py --server.port 8501 --server.address 0.0.0.0
