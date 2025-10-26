#!/bin/bash
# Installation script for Cache Viewer TUI dependencies

echo "📦 Installing Cache Viewer TUI dependencies..."

# Install Textual (TUI framework)
pip install textual

# Install other dependencies (already installed for main app)
echo "✅ Dependencies installed successfully!"
echo ""
echo "🚀 To run the cache viewer:"
echo "   python3 cache_viewer.py"
echo ""
echo "📋 Key bindings:"
echo "   q - Quit"
echo "   r - Refresh cache"
echo "   ↑/↓ - Navigate lists"
echo "   Enter - Select item"