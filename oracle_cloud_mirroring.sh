#!/bin/bash

# Oracle Cloud Mirroring Script
# Runs from Oracle Cloud to sync with AWS

# Connection details
AWS_USER="ec2-user"
AWS_HOST="ec2-52-15-93-20.us-east-2.compute.amazonaws.com"
AWS_KEY="/home/ubuntu/refactored_manga_lookup_tool/aws-key.pem"
AWS_DIR="/home/ec2-user/refactored_manga_lookup_tool"

ORACLE_DIR="/home/ubuntu/refactored_manga_lookup_tool"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

error() {
    echo -e "${RED}❌ $1${NC}"
}

check_connection() {
    local user=$1
    local host=$2
    local key=$3
    local name=$4

    log "Testing connection to $name..."
    if ssh -i "$key" "$user@$host" "echo 'Connection successful'"; then
        success "$name connection verified"
        return 0
    else
        error "Failed to connect to $name"
        return 1
    fi
}

sync_to_aws() {
    log "Syncing to AWS EC2..."

    # List of files to sync
    FILES=(
        "app_new_workflow.py"
        "manga_lookup.py"
        "bigquery_cache.py"
        "label_generator.py"
        "mle_star_cache_optimizer.py"
        "load_missing_volumes_batch.py"
        "requirements.txt"
        "secrets.toml"
        ".streamlit/config.toml"
    )

    for file in "${FILES[@]}"; do
        if [ -f "$ORACLE_DIR/$file" ]; then
            if scp -i "$AWS_KEY" "$ORACLE_DIR/$file" "$AWS_USER@$AWS_HOST:$AWS_DIR/"; then
                success "Synced to AWS: $file"
            else
                warning "Failed to sync to AWS: $file"
            fi
        else
            warning "File not found: $file"
        fi
    done

    # Restart Streamlit on AWS
    log "Restarting Streamlit on AWS..."
    ssh -i "$AWS_KEY" "$AWS_USER@$AWS_HOST" "cd $AWS_DIR && pkill -f streamlit && nohup streamlit run app_new_workflow.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &"

    success "AWS sync completed"
}

main() {
    log "Starting Oracle Cloud mirroring..."

    # Check if AWS key exists
    if [ ! -f "$AWS_KEY" ]; then
        error "AWS key not found: $AWS_KEY"
        echo "Please copy your AWS key to Oracle Cloud:"
        echo "  scp -i ~/projects/Rosie/my-new-key.pem ~/projects/Rosie/my-new-key.pem ubuntu@159.54.179.141:/home/ubuntu/refactored_manga_lookup_tool/aws-key.pem"
        exit 1
    fi

    # Check connections
    if ! check_connection "$AWS_USER" "$AWS_HOST" "$AWS_KEY" "AWS"; then
        warning "Skipping AWS sync due to connection issues"
    else
        sync_to_aws
    fi

    success "Oracle Cloud mirroring completed!"
    echo ""
    echo "📍 AWS Instance: http://$AWS_HOST:8501"
    echo "📍 Oracle Cloud Instance: http://159.54.179.141:8501"
    echo ""
}

# Run main function
main