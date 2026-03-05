#!/bin/bash
# Quick start script for the Geo-Compliance MCP Server

set -e

echo "🚀 Starting Geo-Compliance MCP Server..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the mcp-server directory"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Copying template..."
    cp .env.template .env
    echo "📝 Please edit .env with your API keys and configuration"
    echo "   Then run this script again."
    exit 1
fi

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Check Python environment
echo "🐍 Checking Python environment..."
PYTHON_ENV=${PYTHON_ENV:-"../myenv/bin/python"}

if [ ! -f "$PYTHON_ENV" ]; then
    echo "❌ Error: Python environment not found at $PYTHON_ENV"
    echo "   Please set PYTHON_ENV in .env or activate your Python environment"
    exit 1
fi

# Test Python dependencies
echo "🔍 Testing Python dependencies..."
$PYTHON_ENV -c "
try:
    import sys, os
    sys.path.append('..')
    from src.llm.production_llm_handler import ProductionLLMHandler
    from src.rag.enhanced_rag import EnhancedRAG
    print('✅ Python dependencies OK')
except ImportError as e:
    print(f'❌ Python dependency error: {e}')
    sys.exit(1)
" || {
    echo "❌ Error: Required Python components not available"
    echo "   Please ensure your production pipeline is set up correctly"
    exit 1
}

echo "✅ All checks passed!"
echo ""
echo "🎯 Starting MCP Server..."
echo "   • Tools available: 6 compliance analysis tools"
echo "   • Human-in-the-loop: Enabled"
echo "   • Python bridge: Active"
echo ""

# Start the server
node index.js
