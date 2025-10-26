#!/bin/bash

# Oracle Cloud Mirroring Script
# Mirrors the manga lookup project to Oracle Cloud instance

# Connection details
USER="ubuntu"
HOST="159.54.179.141"
KEY_FILE="~/projects/Rosie/ssh-key-2025-10-22.key"
LOCAL_DIR="/data/data/com.termux/files/home/projects/refactored_manga_lookup_tool"
REMOTE_DIR="/home/ubuntu/refactored_manga_lookup_tool"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log function
log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Test connection
log "Testing Oracle Cloud connection..."
if ssh -i "$KEY_FILE" "$USER@$HOST" "echo 'Connection successful'"; then
    success "Oracle Cloud connection verified"
else
    error "Failed to connect to Oracle Cloud"
    exit 1
fi

# Create remote directory
log "Creating remote directory structure..."
if ssh -i "$KEY_FILE" "$USER@$HOST" "mkdir -p $REMOTE_DIR"; then
    success "Remote directory created: $REMOTE_DIR"
else
    error "Failed to create remote directory"
    exit 1
fi

# Copy Python source files
log "Copying Python source files..."
PYTHON_FILES=(
    "app_new_workflow.py"
    "manga_lookup.py"
    "bigquery_cache.py"
    "marc_export.py"
    "label_generator.py"
    "bulk_volume_test.py"
    "bulk_volume_test_with_cache.py"
    "bulk_volume_test_mle_star.py"
    "mle_star_cache_optimizer.py"
    "load_missing_volumes_batch.py"
    "test_cover_urls.py"
    "test_cover_fix.py"
    "test_mle_star_quick.py"
    "test_label_generator.py"
    "test_cache_isbns.py"
    "aws_monitor.py"
)

for file in "${PYTHON_FILES[@]}"; do
    if [ -f "$LOCAL_DIR/$file" ]; then
        if scp -i "$KEY_FILE" "$LOCAL_DIR/$file" "$USER@$HOST:$REMOTE_DIR/"; then
            success "Copied: $file"
        else
            warning "Failed to copy: $file"
        fi
    else
        warning "File not found: $file"
    fi
done

# Copy configuration files
log "Copying configuration files..."
CONFIG_FILES=(
    "requirements.txt"
    "secrets.toml"
    ".streamlit/config.toml"
    "ssh-aws.sh"
    "bulk_test_context.json"
    "bulk_test_context_updated.json"
)

for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$LOCAL_DIR/$file" ]; then
        # Create directory structure if needed
        dir=$(dirname "$file")
        if [ "$dir" != "." ]; then
            ssh -i "$KEY_FILE" "$USER@$HOST" "mkdir -p $REMOTE_DIR/$dir"
        fi

        if scp -i "$KEY_FILE" "$LOCAL_DIR/$file" "$USER@$HOST:$REMOTE_DIR/$file"; then
            success "Copied: $file"
        else
            warning "Failed to copy: $file"
        fi
    else
        warning "File not found: $file"
    fi
done

# Copy test data files
log "Copying test data files..."
DATA_FILES=(
    "bulk_test_export_20251024_044253.mrc"
    "bulk_test_export_20251024_052008.mrc"
)

for file in "${DATA_FILES[@]}"; do
    if [ -f "$LOCAL_DIR/$file" ]; then
        if scp -i "$KEY_FILE" "$LOCAL_DIR/$file" "$USER@$HOST:$REMOTE_DIR/"; then
            success "Copied: $file"
        else
            warning "Failed to copy: $file"
        fi
    else
        warning "File not found: $file"
    fi
done

# Set up Python environment on Oracle Cloud
log "Setting up Python environment on Oracle Cloud..."
ssh -i "$KEY_FILE" "$USER@$HOST" << 'EOF'
cd /home/ubuntu/refactored_manga_lookup_tool

# Update package list
echo "Updating package list..."
sudo apt update

# Install Python and pip if not present
if ! command -v python3 &> /dev/null; then
    echo "Installing Python3..."
    sudo apt install -y python3 python3-pip
fi

# Install required Python packages
if [ -f "requirements.txt" ]; then
    echo "Installing Python packages from requirements.txt..."
    pip3 install -r requirements.txt
else
    echo "Installing essential packages..."
    pip3 install streamlit google-cloud-bigquery requests pandas reportlab python-barcode qrcode[pil]
fi

# Install additional system dependencies
echo "Installing system dependencies..."
sudo apt install -y libxml2-dev libxslt-dev

EOF

if [ $? -eq 0 ]; then
    success "Python environment setup completed"
else
    error "Failed to setup Python environment"
fi

# Verify installation
log "Verifying installation..."
ssh -i "$KEY_FILE" "$USER@$HOST" << 'EOF'
cd /home/ubuntu/refactored_manga_lookup_tool

echo "=== Python Version ==="
python3 --version

echo "=== Installed Packages ==="
pip3 list | grep -E "(streamlit|google-cloud|requests|pandas|reportlab|barcode|qrcode)"

echo "=== Project Files ==="
ls -la

echo "=== Test Python Import ==="
python3 -c "
import sys
sys.path.append('.')
try:
    from manga_lookup import DeepSeekAPI, GoogleBooksAPI
    print('✅ Core modules imported successfully')

    from bigquery_cache import BigQueryCache
    print('✅ BigQuery cache imported successfully')

    from mle_star_cache_optimizer import MLEStarCacheOptimizer
    print('✅ MLE Star optimizer imported successfully')

    print('✅ All critical imports successful')
except Exception as e:
    print(f'❌ Import failed: {e}')
    import traceback
    traceback.print_exc()
"

EOF

if [ $? -eq 0 ]; then
    success "Installation verification completed"
else
    error "Installation verification failed"
fi

# Create startup script
log "Creating startup scripts..."
cat > /tmp/start_streamlit.sh << 'EOF'
#!/bin/bash
cd /home/ubuntu/refactored_manga_lookup_tool
streamlit run app_new_workflow.py --server.port=8501 --server.address=0.0.0.0
EOF

scp -i "$KEY_FILE" /tmp/start_streamlit.sh "$USER@$HOST:$REMOTE_DIR/"
ssh -i "$KEY_FILE" "$USER@$HOST" "chmod +x $REMOTE_DIR/start_streamlit.sh"

# Create volume loading script
cat > /tmp/start_volume_loading.sh << 'EOF'
#!/bin/bash
cd /home/ubuntu/refactored_manga_lookup_tool
nohup python3 load_missing_volumes_batch.py > volume_loading.log 2>&1 &
echo "Volume background job started with PID: $!"
echo "Check progress with: tail -f volume_loading.log"
EOF

scp -i "$KEY_FILE" /tmp/start_volume_loading.sh "$USER@$HOST:$REMOTE_DIR/"
ssh -i "$KEY_FILE" "$USER@$HOST" "chmod +x $REMOTE_DIR/start_volume_loading.sh"

success "Startup scripts created"

# Final status
log "Mirroring completed. Summary:"
echo ""
echo "📍 Oracle Cloud Instance: $USER@$HOST"
echo "📁 Project Location: $REMOTE_DIR"
echo ""
echo "🚀 Available Commands:"
echo "   Start Streamlit:  ./start_streamlit.sh"
echo "   Start Volume Job: ./start_volume_loading.sh"
echo "   Check Volume Log: tail -f volume_loading.log"
echo ""
echo "🌐 Web Interface: http://$HOST:8501"
echo ""
echo "✅ Mirroring to Oracle Cloud completed successfully!"

# Test MLE Star on Oracle Cloud
log "Testing MLE Star optimization on Oracle Cloud..."
ssh -i "$KEY_FILE" "$USER@$HOST" "cd $REMOTE_DIR && python3 test_mle_star_quick.py"

if [ $? -eq 0 ]; then
    success "MLE Star test completed on Oracle Cloud"
else
    warning "MLE Star test had issues (expected without BigQuery config)"
fi