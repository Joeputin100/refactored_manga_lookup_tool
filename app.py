import streamlit as st

st.set_page_config(
    page_title="Manga Lookup Tool",
    page_icon="📚",
    layout="centered"
)

st.title("📚 Manga Lookup Tool")
st.write("Hello World! This is a minimal Streamlit app.")
st.success("✅ App is working correctly!")

# Simple test component
if st.button("Click me!"):
    st.balloons()
    st.write("🎉 Button clicked! The app is responsive.")