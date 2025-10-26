#!/bin/bash

# Oracle Cloud Setup Script
# Configures Git and Google Cloud SDK

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Connection details
USER="ubuntu"
HOST="159.54.179.141"
KEY_FILE="~/projects/Rosie/ssh-key-2025-10-22.key"

log "Setting up Oracle Cloud instance..."

# Test connection
log "Testing connection to Oracle Cloud..."
if ssh -i "$KEY_FILE" "$USER@$HOST" "echo 'Connection successful'"; then
    success "Oracle Cloud connection verified"
else
    warning "Failed to connect to Oracle Cloud"
    exit 1
fi

# Configure Git
log "Configuring Git..."
ssh -i "$KEY_FILE" "$USER@$HOST" << 'EOF'
# Set Git configuration
git config --global user.name "Manga Lookup System"
git config --global user.email "manga-lookup@system.local"
git config --global init.defaultBranch main
git config --global pull.rebase false

# Verify Git configuration
echo "=== Git Configuration ==="
git config --global --list | grep -E "(user.name|user.email|defaultBranch)"
EOF

if [ $? -eq 0 ]; then
    success "Git configuration completed"
else
    warning "Git configuration had issues"
fi

# Configure Google Cloud SDK
log "Configuring Google Cloud SDK..."
ssh -i "$KEY_FILE" "$USER@$HOST" << 'EOF'
# Add Google Cloud SDK to PATH in .bashrc if not already present
if ! grep -q "google-cloud-sdk" ~/.bashrc; then
    echo 'export PATH="$PATH:/home/ubuntu/google-cloud-sdk/bin"' >> ~/.bashrc
    echo 'source /home/ubuntu/google-cloud-sdk/completion.bash.inc' >> ~/.bashrc
fi

# Source the updated .bashrc
source ~/.bashrc

# Verify Google Cloud SDK installation
echo "=== Google Cloud SDK Status ==="
/home/ubuntu/google-cloud-sdk/bin/gcloud --version
echo ""
echo "=== BigQuery Tool Status ==="
which bq
bq version 2>/dev/null || echo "bq command available"
EOF

if [ $? -eq 0 ]; then
    success "Google Cloud SDK configuration completed"
else
    warning "Google Cloud SDK configuration had issues"
fi

# Create Google Cloud authentication script
log "Creating Google Cloud authentication helper..."
ssh -i "$KEY_FILE" "$USER@$HOST" "cat > /home/ubuntu/setup_gcloud_auth.sh << 'EOF'
#!/bin/bash
# Google Cloud Authentication Helper

echo "🔐 Google Cloud Authentication Setup"
echo ""
echo "To authenticate with Google Cloud, follow these steps:"
echo ""
echo "1. Download your service account key from Google Cloud Console:"
echo "   - Go to IAM & Admin > Service Accounts"
echo "   - Select your service account"
echo "   - Create and download a JSON key"
echo ""
echo "2. Upload the key to this server:"
echo "   scp -i ~/projects/Rosie/ssh-key-2025-10-22.key keyfile.json ubuntu@159.54.179.141:/home/ubuntu/"
echo ""
echo "3. Authenticate with the key:"
echo "   gcloud auth activate-service-account --key-file=/home/ubuntu/keyfile.json"
echo ""
echo "4. Set the project:"
echo "   gcloud config set project YOUR_PROJECT_ID"
echo ""
echo "5. Verify authentication:"
echo "   gcloud auth list"
echo ""
echo "Once authenticated, the BigQuery cache will work automatically."
EOF

chmod +x /home/ubuntu/setup_gcloud_auth.sh"

if [ $? -eq 0 ]; then
    success "Google Cloud authentication helper created"
else
    warning "Failed to create authentication helper"
fi

# Test the setup
log "Testing the complete setup..."
ssh -i "$KEY_FILE" "$USER@$HOST" << 'EOF'
echo "=== System Status ==="
echo ""
echo "📦 Git Status:"
git --version
echo ""
echo "☁️  Google Cloud SDK Status:"
/home/ubuntu/google-cloud-sdk/bin/gcloud --version | head -1
echo ""
echo "🐍 Python Status:"
cd /home/ubuntu/refactored_manga_lookup_tool
source venv/bin/activate
python3 --version
pip list | grep -E "(google-cloud|streamlit|requests)" | head -5
echo ""
echo "🚀 Streamlit Status:"
ps aux | grep streamlit | grep -v grep || echo "Streamlit not running (start with: ./start_streamlit_oracle.sh)"
echo ""
echo "=== Next Steps ==="
echo "1. Run Google Cloud authentication: ./setup_gcloud_auth.sh"
echo "2. Start Streamlit: cd refactored_manga_lookup_tool && ./start_streamlit_oracle.sh"
echo "3. Access web interface: http://159.54.179.141:8501"
echo "4. Start volume loading: ./start_volume_loading_oracle.sh"
EOF

if [ $? -eq 0 ]; then
    success "Oracle Cloud setup completed successfully!"
    echo ""
    echo "📍 Oracle Cloud Instance: ubuntu@159.54.179.141"
    echo "📁 Project Location: /home/ubuntu/refactored_manga_lookup_tool"
    echo "🌐 Web Interface: http://159.54.179.141:8501"
    echo ""
    echo "✅ Git and Google Cloud SDK are now configured!"
else
    warning "Setup verification had issues"
fi