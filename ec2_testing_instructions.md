# EC2 Vertex AI Testing Instructions

## Prerequisites
- EC2 instance must be running and accessible
- Vertex AI dependencies installed on EC2
- Streamlit Cloud secrets configured properly

## Steps to Test Vertex AI on EC2

### 1. Connect to EC2 Instance
```bash
ssh ec2-user@ec2-3-144-111-64.us-east-2.compute.amazonaws.com
```

### 2. Navigate to Project Directory
```bash
cd /home/ec2-user/refactored_manga_lookup_tool
```

### 3. Update Code
```bash
git pull
```

### 4. Verify Vertex AI Dependencies
```bash
# Check if vertexai is installed
python -c "import vertexai; print('Vertex AI module available')"

# Check if other dependencies are installed
python -c "import streamlit; print('Streamlit available')"
python -c "import google.cloud; print('Google Cloud available')"
```

### 5. Run Streamlit App
```bash
streamlit run app_new_workflow.py
```

### 6. Test Vertex AI Functionality

#### Test 1: Basic Initialization
- Open the Streamlit app in browser
- Check console logs for Vertex AI initialization
- Should see: "✅ Vertex AI API initialized successfully"

#### Test 2: Series Search with "Attack on Titan"
- Step 1: Enter a starting barcode (e.g., "Barcode001")
- Step 2: Confirm barcode sequence
- Step 3: Enter "Attack on Titan" as series name
- Expected: Should find series information via Vertex AI

#### Test 3: Verify API Fallback
- If Vertex AI fails, should fall back to DeepSeek API
- DeepSeek should find "Attack on Titan"

### 7. Expected Results

#### Vertex AI Working:
```
✅ Vertex AI API initialized successfully for: Attack on Titan
🔍 Searching for series information...
📚 Found series: Attack on Titan
```

#### Vertex AI Failing (Fallback to DeepSeek):
```
❌ Vertex AI initialization failed: [error]
✅ DeepSeek API initialized successfully for: Attack on Titan
🔍 Searching for series information...
📚 Found series: Attack on Titan (via DeepSeek)
```

### 8. Troubleshooting

#### Vertex AI Not Initializing:
1. Check GCLOUD_SERVICE_KEY in Streamlit secrets
2. Verify vertexai module is installed: `pip install google-cloud-aiplatform`
3. Check Google Cloud authentication

#### DeepSeek API Not Working:
1. Check DEEPSEEK_API_KEY in Streamlit secrets
2. Verify network connectivity
3. Check API rate limits

#### General Issues:
1. Check all required secrets are set:
   - GCLOUD_SERVICE_KEY
   - DEEPSEEK_API_KEY
   - GEMINI_API_KEY
2. Verify Python dependencies are installed
3. Check Streamlit logs for detailed error messages

### 9. Required Streamlit Secrets

```toml
# .streamlit/secrets.toml (for local testing)
GCLOUD_SERVICE_KEY = "your_service_account_key"
DEEPSEEK_API_KEY = "your_deepseek_api_key"
GEMINI_API_KEY = "your_gemini_api_key"
```

### 10. Success Criteria
- Vertex AI API initializes without errors
- "Attack on Titan" is found by at least one API
- Series information is displayed correctly
- User can proceed to volume selection

## Current Status
- ✅ Codebase is updated with proper error handling
- ✅ DeepSeek API is working (tested locally)
- ✅ Google Books API is working (tested locally)
- ❓ Vertex AI needs testing on EC2 (module not available locally)
- ❓ EC2 instance currently unreachable

## Next Steps
1. Resolve EC2 connectivity issues
2. Test Vertex AI functionality on EC2
3. Verify all APIs work together
4. Deploy to Streamlit Cloud for final testing