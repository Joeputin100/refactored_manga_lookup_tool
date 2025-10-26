#!/bin/bash

# Background Mirror Monitor
# Runs automated mirroring every hour

LOCAL_DIR="/data/data/com.termux/files/home/projects/refactored_manga_lookup_tool"
MIRROR_SCRIPT="$LOCAL_DIR/automated_mirroring.sh"
LOG_FILE="$LOCAL_DIR/mirror_monitor.log"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

# Check if script exists
if [ ! -f "$MIRROR_SCRIPT" ]; then
    log "Mirroring script not found: $MIRROR_SCRIPT"
    exit 1
fi

# Make sure script is executable
chmod +x "$MIRROR_SCRIPT"

log "🚀 Starting Background Mirror Monitor"
log "📁 Script: $MIRROR_SCRIPT"
log "📄 Log: $LOG_FILE"
log "⏰ Interval: Every hour"
log ""

# Main monitoring loop
while true; do
    current_hour=$(date '+%H')
    log "🔄 Running automated mirroring at $(date '+%H:%M:%S')..."

    # Run the mirroring script
    "$MIRROR_SCRIPT" >> "$LOG_FILE" 2>&1

    if [ $? -eq 0 ]; then
        success "Mirroring completed successfully"
    else
        warning "Mirroring completed with warnings"
    fi

    log "💤 Sleeping for 1 hour..."
    log ""

    # Sleep for 1 hour (3600 seconds)
    sleep 3600
done