#!/usr/bin/env python3
"""
Reimplement MARC export navigation fix
"""

def reimplement_marc_navigation():
    """Add Continue button after exports to keep users on results page"""

    # Read the current file
    with open('app_new_workflow.py', 'r') as f:
        content = f.read()

    # Find the end of the export section
    end_marker = 'def display_queued_series_summary():'

    end_pos = content.find(end_marker)
    if end_pos == -1:
        print("❌ Could not find end of export section")
        return False

    # Create the Continue button section
    continue_button = '''

    # Add a Continue button to stay on results page
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Continue Working", type="primary", use_container_width=True):
            st.success("✅ You can continue working with the current results")
            st.rerun()
'''

    # Insert the continue button before the next function
    content = content[:end_pos] + continue_button + '\n\n' + content[end_pos:]

    # Write the updated content
    with open('app_new_workflow.py', 'w') as f:
        f.write(content)

    print("✅ MARC export navigation fix reimplemented successfully")
    return True

if __name__ == "__main__":
    reimplement_marc_navigation()