#!/bin/bash

# EC2 Connection Retry Monitor
# Attempts SSH connection every hour until successful

EC2_HOST="ec2-52-15-93-20.us-east-2.compute.amazonaws.com"
KEY_FILE="~/projects/Rosie/my-new-key.pem"
TEST_SCRIPT="~/projects/refactored_manga_lookup_tool/test_updated_cache.py"

while true; do
    echo "$(date): Attempting SSH connection to $EC2_HOST..."

    # Test SSH connection
    ssh -i "$KEY_FILE" -o ConnectTimeout=30 -o BatchMode=yes ec2-user@$EC2_HOST "echo 'Connection successful'" 2>/dev/null

    if [ $? -eq 0 ]; then
        echo "$(date): ✅ SSH connection successful!"
        echo "$(date): Copying test script to EC2..."

        # Copy the test script
        scp -i "$KEY_FILE" "$TEST_SCRIPT" ec2-user@$EC2_HOST:~/ 2>/dev/null

        if [ $? -eq 0 ]; then
            echo "$(date): ✅ Test script copied successfully"
            echo "$(date): Running test script on EC2..."

            # Run the test script
            ssh -i "$KEY_FILE" ec2-user@$EC2_HOST "cd ~ && python3 test_updated_cache.py" 2>/dev/null

            if [ $? -eq 0 ]; then
                echo "$(date): ✅ Test script executed successfully"
            else
                echo "$(date): ❌ Test script execution failed"
            fi
        else
            echo "$(date): ❌ Failed to copy test script"
        fi

        break
    else
        echo "$(date): ❌ SSH connection failed, retrying in 1 hour..."
        sleep 3600  # Wait 1 hour
    fi
done