#!/bin/bash

# Streamlit startup script for Oracle Cloud
cd /home/ubuntu/refactored_manga_lookup_tool
source venv/bin/activate
streamlit run app_new_workflow.py --server.port=8501 --server.address=0.0.0.0