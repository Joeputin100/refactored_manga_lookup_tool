#!/bin/bash

# Volume loading startup script for Oracle Cloud
cd /home/ubuntu/refactored_manga_lookup_tool
source venv/bin/activate
nohup python3 load_missing_volumes_batch.py > volume_loading.log 2>&1 &
echo "Volume background job started with PID: $!"
echo "Check progress with: tail -f volume_loading.log"