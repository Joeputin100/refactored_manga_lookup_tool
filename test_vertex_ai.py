#!/usr/bin/env python3
"""
Test script for Vertex AI functionality
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_vertex_ai_initialization():
    """Test Vertex AI API initialization"""
    print("Testing Vertex AI API initialization...")

    # Set test environment variables
    os.environ['GCLOUD_SERVICE_KEY'] = 'test_key'
    os.environ['VERTEX_AI_PROJECT_ID'] = 'test_project'
    os.environ['VERTEX_AI_LOCATION'] = 'us-central1'

    try:
        from manga_lookup import VertexAIAPI

        # Test initialization
        vertex_api = VertexAIAPI()
        print("✅ Vertex AI API initialized successfully")

        # Test methods exist
        methods = ['get_comprehensive_series_info', 'get_book_info']
        for method in methods:
            if hasattr(vertex_api, method):
                print(f"✅ Method '{method}' exists")
            else:
                print(f"❌ Method '{method}' missing")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False

def test_streamlit_secrets():
    """Test Streamlit secrets handling"""
    print("\nTesting Streamlit secrets handling...")

    try:
        import streamlit as st
        print("✅ Streamlit module available")

        # Check if we can access secrets
        if hasattr(st, 'secrets'):
            print("✅ Streamlit secrets available")

            # Check for required secrets
            required_secrets = ['GCLOUD_SERVICE_KEY', 'DEEPSEEK_API_KEY', 'GEMINI_API_KEY']
            for secret in required_secrets:
                if secret in st.secrets:
                    print(f"✅ Secret '{secret}' is set")
                else:
                    print(f"❌ Secret '{secret}' is missing")
        else:
            print("❌ Streamlit secrets not available")

    except ImportError:
        print("❌ Streamlit not installed in this environment")
        return False
    except Exception as e:
        print(f"❌ Error checking secrets: {e}")
        return False

def test_all_apis():
    """Test all API initializations"""
    print("\nTesting all API initializations...")

    try:
        from manga_lookup import VertexAIAPI, DeepSeekAPI, GoogleBooksAPI

        # Test DeepSeek API
        try:
            os.environ['DEEPSEEK_API_KEY'] = 'test_key'
            deepseek = DeepSeekAPI()
            print("✅ DeepSeek API initialized successfully")
        except Exception as e:
            print(f"❌ DeepSeek API failed: {e}")

        # Test Google Books API
        try:
            os.environ['GEMINI_API_KEY'] = 'test_key'
            google = GoogleBooksAPI()
            print("✅ Google Books API initialized successfully")
        except Exception as e:
            print(f"❌ Google Books API failed: {e}")

        # Test Vertex AI API
        try:
            os.environ['GCLOUD_SERVICE_KEY'] = 'test_key'
            vertex = VertexAIAPI()
            print("✅ Vertex AI API initialized successfully")
        except Exception as e:
            print(f"❌ Vertex AI API failed: {e}")

    except Exception as e:
        print(f"❌ Error importing APIs: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("Vertex AI and API Testing Script")
    print("=" * 50)

    # Run tests
    test_vertex_ai_initialization()
    test_streamlit_secrets()
    test_all_apis()

    print("\n" + "=" * 50)
    print("Testing complete")
    print("=" * 50)

    print("\nInstructions for EC2 testing:")
    print("1. Ensure EC2 instance is running and accessible")
    print("2. SSH into EC2: ssh ec2-user@YOUR_EC2_IP")
    print("3. Navigate to: cd /home/ec2-user/refactored_manga_lookup_tool")
    print("4. Pull latest code: git pull")
    print("5. Run Streamlit: streamlit run app_new_workflow.py")
    print("6. Test with 'Attack on Titan' to verify Vertex AI works")