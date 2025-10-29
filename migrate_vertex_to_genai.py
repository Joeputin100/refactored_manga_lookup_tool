#!/usr/bin/env python3
"""
Migrate Vertex AI calls to genai calls per SDK deprecation
"""

def migrate_vertex_to_genai():
    """Update Vertex AI imports and calls to use google.generativeai"""

    # Read the current file
    with open('manga_lookup.py', 'r') as f:
        content = f.read()

    # Replace imports
    content = content.replace('from vertexai.generative_models import GenerativeModel', 'import google.generativeai as genai')
    content = content.replace('from vertexai.generative_models import GenerativeModel, Tool', 'import google.generativeai as genai')
    content = content.replace('from vertexai.generative_models import grounding', 'import google.generativeai as genai')

    # Replace model initialization
    content = content.replace('model = GenerativeModel("gemini-2.5-flash-lite")', 'model = genai.GenerativeModel("gemini-2.5-flash-lite")')
    content = content.replace('model = self.GenerativeModel(model_name)', 'model = genai.GenerativeModel(model_name)')

    # Replace response generation
    content = content.replace('response = model.generate_content(prompt)', 'response = model.generate_content(prompt)')

    # Update the enhanced VertexAIAPI class to use genai
    # Find and replace the GenerativeModel usage in the enhanced class
    enhanced_class_start = 'class VertexAIAPI:'
    enhanced_class_end = 'class DeepSeekAPI:'

    start_pos = content.find(enhanced_class_start)
    end_pos = content.find(enhanced_class_end, start_pos)

    if start_pos != -1 and end_pos != -1:
        enhanced_class = content[start_pos:end_pos]

        # Remove the GenerativeModel import and initialization from enhanced class
        enhanced_class = enhanced_class.replace('from vertexai.generative_models import GenerativeModel', '')
        enhanced_class = enhanced_class.replace('self.GenerativeModel = GenerativeModel', '')

        # Update the model creation in _call_model_with_fallback
        enhanced_class = enhanced_class.replace('model = self.GenerativeModel(model_name)', 'model = genai.GenerativeModel(model_name)')

        # Replace the enhanced class in content
        content = content[:start_pos] + enhanced_class + content[end_pos:]

    # Write the updated content
    with open('manga_lookup.py', 'w') as f:
        f.write(content)

    print("✅ Vertex AI calls migrated to genai library")
    return True

if __name__ == "__main__":
    migrate_vertex_to_genai()