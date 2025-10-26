#!/bin/bash

# Hourly git commit script for manga lookup tool
# This script commits and pushes changes every hour

PROJECT_DIR="/data/data/com.termux/files/home/projects/refactored_manga_lookup_tool"
cd "$PROJECT_DIR" || exit 1

# Check if there are any changes to commit
if git diff-index --quiet HEAD --; then
    echo "$(date): No changes to commit" >> hourly_commit.log
    exit 0
fi

# Add all changes
git add .

# Create commit message with timestamp
COMMIT_MESSAGE="$(cat <<'EOF'
Hourly commit: $(date)

- Automated commit of ongoing work
- Project maintenance and updates

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# Commit changes
git commit -m "$COMMIT_MESSAGE"

# Push to remote
git push

echo "$(date): Successfully committed and pushed changes" >> hourly_commit.log