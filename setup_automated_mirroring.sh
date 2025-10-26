#!/bin/bash

# Setup automated mirroring with cron job

LOCAL_DIR="/data/data/com.termux/files/home/projects/refactored_manga_lookup_tool"
MIRROR_SCRIPT="$LOCAL_DIR/automated_mirroring.sh"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Check if script exists
if [ ! -f "$MIRROR_SCRIPT" ]; then
    log "Mirroring script not found. Please run automated_mirroring.sh first."
    exit 1
fi

# Make sure script is executable
chmod +x "$MIRROR_SCRIPT"

# Setup cron job
log "Setting up automated mirroring with cron..."

# Create cron entry (runs every hour)
CRON_ENTRY="0 * * * * $MIRROR_SCRIPT"

# Add to crontab
(crontab -l 2>/dev/null | grep -v "$MIRROR_SCRIPT"; echo "$CRON_ENTRY") | crontab -

success "Automated mirroring cron job installed!"
echo ""
echo "📅 Cron Schedule: Every hour at minute 0"
echo "📁 Script Location: $MIRROR_SCRIPT"
echo ""
echo "To view current cron jobs: crontab -l"
echo "To remove this cron job: crontab -e"
echo ""
echo "🌐 Instances:"
echo "   AWS: http://ec2-52-15-93-20.us-east-2.compute.amazonaws.com:8501"
echo "   Oracle Cloud: http://159.54.179.141:8501"
echo ""
echo "✅ Automated mirroring is now active!"