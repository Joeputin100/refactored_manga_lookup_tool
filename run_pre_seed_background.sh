#!/bin/bash

# Background pre-seeding runner for manga cache
# This script runs the pre-seeding process in the background with logging

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/pre_seed_${TIMESTAMP}.log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

echo "🚀 Starting manga cache pre-seeding in background..."
echo "📁 Log file: $LOG_FILE"
echo "⏰ Started at: $(date)"

# Run the pre-seeding script and log output
cd "$SCRIPT_DIR"
nohup python3 pre_seed_cache.py > "$LOG_FILE" 2>&1 &

PRE_SEED_PID=$!
echo "📝 Process PID: $PRE_SEED_PID"
echo "💾 PID saved to: $LOG_DIR/pre_seed_${TIMESTAMP}.pid"

# Save PID to file
echo "$PRE_SEED_PID" > "$LOG_DIR/pre_seed_${TIMESTAMP}.pid"

echo ""
echo "🎯 To monitor the process:"
echo "   tail -f $LOG_FILE"
echo ""
echo "🎯 To check process status:"
echo "   ps aux | grep python3 | grep pre_seed_cache"
echo ""
echo "🎯 To stop the process:"
echo "   kill $PRE_SEED_PID"
echo ""
echo "✅ Pre-seeding process started successfully!"

# Show initial log content
echo ""
echo "📰 Initial log output:"
echo "===================="
tail -n 10 "$LOG_FILE"