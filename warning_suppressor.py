#!/usr/bin/env python3
"""
Warning suppression utility for Vertex AI and Streamlit warnings
"""
import warnings
import sys
import os

def suppress_vertex_ai_warnings():
    """Suppress Vertex AI deprecation warnings"""
    warnings.filterwarnings("ignore",
                          message="This feature is deprecated as of June 24, 2025",
                          category=UserWarning,
                          module="vertexai")

def suppress_streamlit_warnings():
    """Suppress common Streamlit warnings"""
    # Suppress ScriptRunContext warnings when running scripts directly
    warnings.filterwarnings("ignore",
                          message="Thread 'MainThread': missing ScriptRunContext",
                          category=UserWarning,
                          module="streamlit")

    # Suppress session state warnings when running scripts directly
    warnings.filterwarnings("ignore",
                          message="Session state does not function when running a script without",
                          category=UserWarning,
                          module="streamlit")

def configure_warnings():
    """Configure all warning suppression"""
    # Suppress specific warnings
    suppress_vertex_ai_warnings()
    suppress_streamlit_warnings()

    # Also suppress ALTS credentials warnings if not on GCP
    warnings.filterwarnings("ignore",
                          message="ALTS creds ignored",
                          category=UserWarning)

    print("✅ Warning suppression configured")

def test_warning_suppression():
    """Test that warnings are properly suppressed"""
    print("🔍 Testing warning suppression...")

    # Test Vertex AI warning suppression
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        print("✅ Vertex AI imports successful")
    except ImportError as e:
        print(f"❌ Vertex AI import failed: {e}")

    # Test Streamlit warning suppression
    try:
        import streamlit as st
        print("✅ Streamlit import successful")
    except ImportError as e:
        print(f"❌ Streamlit import failed: {e}")

    print("✅ Warning suppression test completed")

if __name__ == "__main__":
    configure_warnings()
    test_warning_suppression()