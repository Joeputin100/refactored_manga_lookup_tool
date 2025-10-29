#!/usr/bin/env python3
"""
Fix MARC export closing results page by adding a Continue button
"""

def fix_marc_export():
    """Add a Continue button after exports to keep users on results page"""

    # Read the current file
    with open('app_new_workflow.py', 'r') as f:
        content = f.read()

    # Find the end of the export section
    if 'st.error("Sorry! An error occurred while generating labels.")' in content:
        print("✅ Found export section end")

        # Add a Continue button after the exports
        continue_button = '''

    # Add a Continue button to stay on results page
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Continue Working", type="primary", use_container_width=True):
            st.success("✅ You can continue working with the current results")
            st.rerun()
'''

        # Insert the continue button after the export section
        insert_point = content.find('st.error("Sorry! An error occurred while generating labels.")')
        if insert_point != -1:
            # Find the end of the export section (after the error handling)
            end_of_export = content.find('def display_queued_series_summary():', insert_point)
            if end_of_export != -1:
                # Insert the continue button before the next function
                content = content[:end_of_export] + continue_button + '\n\n' + content[end_of_export:]
                print("✅ Successfully added Continue button")
            else:
                print("❌ Could not find end of export section")
                return False
        else:
            print("❌ Could not find export section end")
            return False
    else:
        print("❌ Could not find export section")
        return False

    # Write the updated content
    with open('app_new_workflow.py', 'w') as f:
        f.write(content)

    print("✅ Successfully fixed MARC export navigation")
    return True

if __name__ == "__main__":
    fix_marc_export()