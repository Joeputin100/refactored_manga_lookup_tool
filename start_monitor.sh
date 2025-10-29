#!/bin/bash
# Startup script for BigQuery Backfill Monitor

echo "Starting BigQuery Backfill Monitor on EC2..."
cd ~/refactored_manga_lookup_tool

# Check if monitor script exists
if [ ! -f "monitor_backfill.py" ]; then
    echo "Error: monitor_backfill.py not found"
    exit 1
fi

# Run the monitor with proper terminal settings
python3 monitor_backfill.py