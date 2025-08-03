import streamlit as st

# Simple test app to verify basic functionality
st.set_page_config(
    page_title="CleanPlate - Test",
    page_icon="🍽️",
    layout="wide"
)

st.title("🍽️ CleanPlate - Restaurant Health Inspections")
st.write("Simple test version to verify basic functionality")

# Test basic Streamlit components
col1, col2 = st.columns(2)

with col1:
    st.selectbox("Test City", ["NYC", "Chicago", "Dallas", "Virginia"])

with col2:
    st.text_input("Search restaurants")

st.write("If you can see this, the app is working correctly!")

# Test basic HTML
st.markdown("""
<div style="background-color: #1a202c; padding: 10px; border-radius: 5px; color: white;">
    Test HTML rendering
</div>
""", unsafe_allow_html=True)