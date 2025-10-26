#!/bin/bash

# Git commit monitor script
# Run this in background to commit changes periodically

PROJECT_DIR="/data/data/com.termux/files/home/projects/refactored_manga_lookup_tool"
LOG_FILE="$PROJECT_DIR/git_commit_monitor.log"

cd "$PROJECT_DIR" || exit 1

echo "$(date): Starting git commit monitor" >> "$LOG_FILE"

while true; do
    # Wait 1 hour
    sleep 3600

    # Run the hourly commit script
    ./hourly_git_commit.sh

    echo "$(date): Completed hourly commit check" >> "$LOG_FILE"
done