import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os
from data_fetcher import HealthInspectionAPI
from utils import format_grade_badge, get_cuisine_types
from database import (
    init_database, save_restaurant_to_db, save_user_review, 
    get_restaurant_reviews, calculate_db_average_rating,
    get_restaurant_violations, search_restaurants_in_db, get_db_statistics
)

# Configure page
st.set_page_config(
    page_title="CleanPlate - Restaurant Health Inspector",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize database
@st.cache_resource
def initialize_database():
    return init_database()

# Initialize session state
if 'user_reviews' not in st.session_state:
    st.session_state.user_reviews = {}

if 'api_client' not in st.session_state:
    st.session_state.api_client = HealthInspectionAPI()

if 'current_jurisdiction' not in st.session_state:
    st.session_state.current_jurisdiction = "NYC"

# Initialize database on startup
initialize_database()

def main():
    
    # Consolidated CleanPlate Theme - Professional Restaurant Atmosphere
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;500;600;700&display=swap');
        
        /* Main App Background - Sophisticated Restaurant Atmosphere */
        .stApp {
            background: 
                linear-gradient(45deg, rgba(18, 22, 26, 0.95) 0%, rgba(25, 30, 35, 0.9) 25%, rgba(32, 38, 44, 0.85) 75%, rgba(40, 46, 52, 0.9) 100%),
                url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080"><defs><radialGradient id="spotlight1" cx="0.2" cy="0.3" r="0.4"><stop offset="0%" stop-color="%23d4af37" stop-opacity="0.15"/><stop offset="100%" stop-color="transparent"/></radialGradient><radialGradient id="spotlight2" cx="0.8" cy="0.7" r="0.3"><stop offset="0%" stop-color="%23d4af37" stop-opacity="0.08"/><stop offset="100%" stop-color="transparent"/></radialGradient><pattern id="fine-texture" width="120" height="120" patternUnits="userSpaceOnUse"><circle cx="30" cy="30" r="1" fill="%23ffffff" fill-opacity="0.02"/><circle cx="90" cy="90" r="0.8" fill="%23d4af37" fill-opacity="0.03"/><circle cx="60" cy="15" r="0.5" fill="%23ffffff" fill-opacity="0.015"/><circle cx="15" cy="75" r="0.6" fill="%23d4af37" fill-opacity="0.025"/><rect x="45" y="45" width="30" height="30" fill="none" stroke="%23ffffff" stroke-width="0.1" stroke-opacity="0.01" rx="2"/></pattern></defs><rect width="1920" height="1080" fill="%23121619"/><rect width="1920" height="1080" fill="url(%23fine-texture)"/><ellipse cx="384" cy="324" rx="300" ry="200" fill="url(%23spotlight1)"/><ellipse cx="1536" cy="756" rx="240" ry="160" fill="url(%23spotlight2)"/><polygon points="0,1080 500,1040 1000,1060 1500,1020 1920,1050 1920,1080" fill="%231a1e23" opacity="0.8"/><polygon points="0,980 400,950 800,970 1200,930 1600,950 1920,920 1920,1080 0,1080" fill="%23252a30" opacity="0.6"/><polygon points="0,880 300,860 600,880 900,850 1200,870 1500,840 1800,860 1920,840 1920,1080 0,1080" fill="%232d3339" opacity="0.4"/></svg>');
            background-size: cover;
            background-attachment: fixed;
            background-position: center;
            color: #e8eaed;
            font-family: 'Inter', sans-serif;
            min-height: 100vh;
        }
        
        /* Header Section */
        .main-header {
            background: 
                linear-gradient(135deg, rgba(26, 30, 35, 0.95) 0%, rgba(37, 42, 48, 0.9) 50%, rgba(45, 51, 57, 0.95) 100%),
                url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 300"><defs><pattern id="header-pattern" width="80" height="80" patternUnits="userSpaceOnUse"><circle cx="40" cy="40" r="1" fill="%23d4af37" fill-opacity="0.1"/><circle cx="20" cy="20" r="0.5" fill="%23ffffff" fill-opacity="0.05"/><circle cx="60" cy="60" r="0.8" fill="%23d4af37" fill-opacity="0.08"/><rect x="35" y="35" width="10" height="10" fill="none" stroke="%23ffffff" stroke-width="0.2" stroke-opacity="0.03" rx="1"/></pattern></defs><rect width="800" height="300" fill="url(%23header-pattern)"/><polygon points="0,270 200,250 400,260 600,240 800,250 800,300 0,300" fill="%23d4af37" opacity="0.08"/></svg>');
            padding: 4rem 3rem;
            margin: -1rem -1rem 3rem -1rem;
            position: relative;
            overflow: hidden;
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.5),
                inset 0 1px 0 rgba(255, 255, 255, 0.1),
                inset 0 -1px 0 rgba(212, 175, 55, 0.2);
            border-bottom: 2px solid rgba(212, 175, 55, 0.3);
        }
        
        .main-header h1 {
            color: #ffffff;
            font-size: 4.5rem;
            font-weight: 600;
            margin: 0;
            font-family: 'Playfair Display', serif;
            letter-spacing: -0.03em;
            line-height: 1.1;
            position: relative;
            z-index: 2;
            text-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        }
        
        .main-header p {
            color: rgba(212, 175, 55, 0.9);
            font-size: 0.95rem;
            margin: 1.5rem 0 0 0;
            font-weight: 500;
            letter-spacing: 0.15em;
            position: relative;
            z-index: 2;
            font-family: 'Inter', sans-serif;
            text-transform: uppercase;
            opacity: 0.9;
        }
        
        /* Form Controls */
        .stSelectbox > div > div {
            background: rgba(37, 42, 48, 0.95) !important;
            border: 1px solid rgba(212, 175, 55, 0.4) !important;
            border-radius: 10px !important;
            color: #e8eaed !important;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3) !important;
            backdrop-filter: blur(8px) !important;
        }
        
        .stSelectbox > div > div > div {
            color: #e8eaed !important;
        }
        
        .stTextInput > div > div > input {
            background: rgba(37, 42, 48, 0.95) !important;
            border: 1px solid rgba(212, 175, 55, 0.4) !important;
            border-radius: 10px !important;
            color: #e8eaed !important;
            padding: 16px 20px !important;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3) !important;
            font-family: 'Inter', sans-serif !important;
            backdrop-filter: blur(8px) !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #d4af37 !important;
            box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.3) !important;
        }
        
        .stTextInput > div > div > input::placeholder {
            color: rgba(184, 188, 194, 0.6) !important;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #d4af37 0%, #b8941f 50%, #a08419 100%) !important;
            border: none !important;
            border-radius: 10px !important;
            color: #1a1e23 !important;
            font-weight: 600 !important;
            padding: 16px 32px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 6px 20px rgba(212, 175, 55, 0.4) !important;
            font-family: 'Inter', sans-serif !important;
            text-transform: uppercase;
            letter-spacing: 0.03em;
            font-size: 0.875rem;
        }
        
        .stButton > button:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 12px 32px rgba(212, 175, 55, 0.5) !important;
            background: linear-gradient(135deg, #e6c447 0%, #d4af37 50%, #b8941f 100%) !important;
        }
        
        /* Restaurant Cards */
        .stExpander {
            background: rgba(37, 42, 48, 0.95) !important;
            border: 1px solid rgba(212, 175, 55, 0.3) !important;
            border-radius: 16px !important;
            margin: 2.5rem 0 !important;
            box-shadow: 
                0 12px 32px rgba(0, 0, 0, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(12px) !important;
            transition: all 0.3s ease !important;
        }
        
        .stExpander:hover {
            transform: translateY(-4px) !important;
            box-shadow: 
                0 20px 48px rgba(0, 0, 0, 0.5),
                0 0 0 1px rgba(212, 175, 55, 0.5) !important;
            border-color: rgba(212, 175, 55, 0.6) !important;
        }
        
        .stExpander > div:first-child {
            background: linear-gradient(135deg, #2d3339 0%, #3a424a 50%, #454e57 100%) !important;
            border-radius: 16px 16px 0 0 !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            font-size: 1.2rem !important;
            padding: 2rem 2.5rem !important;
            border-bottom: 1px solid rgba(212, 175, 55, 0.4) !important;
            font-family: 'Playfair Display', serif !important;
            position: relative;
            overflow: hidden;
        }
        
        .stExpander > div:first-child::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50"><defs><pattern id="card-header-texture" width="25" height="25" patternUnits="userSpaceOnUse"><circle cx="12.5" cy="12.5" r="0.5" fill="%23d4af37" fill-opacity="0.1"/></pattern></defs><rect width="100" height="50" fill="url(%23card-header-texture)"/></svg>');
            pointer-events: none;
            opacity: 0.3;
        }
        
        .stExpander > div:last-child {
            background: rgba(32, 37, 43, 0.95) !important;
            border-radius: 0 0 16px 16px !important;
            padding: 2.5rem !important;
        }
        
        /* Info Sections */
        .info-section {
            background: 
                linear-gradient(135deg, rgba(32, 37, 43, 0.98) 0%, rgba(40, 46, 52, 0.95) 100%);
            border-radius: 12px;
            padding: 28px;
            margin: 24px 0;
            border: 1px solid rgba(212, 175, 55, 0.25);
            box-shadow: 
                0 8px 24px rgba(0, 0, 0, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.08);
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(10px);
        }
        
        .info-section::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80"><defs><pattern id="info-texture" width="40" height="40" patternUnits="userSpaceOnUse"><circle cx="20" cy="20" r="0.8" fill="%23d4af37" fill-opacity="0.06"/><rect x="15" y="15" width="10" height="10" fill="none" stroke="%23ffffff" stroke-width="0.1" stroke-opacity="0.02" rx="1"/></pattern></defs><rect width="80" height="80" fill="url(%23info-texture)"/></svg>');
            pointer-events: none;
            z-index: 0;
        }
        
        /* Typography */
        .section-header {
            color: #ffffff;
            font-size: 1.3rem;
            font-weight: 600;
            margin: 0 0 24px 0;
            letter-spacing: 0.02em;
            border-bottom: 2px solid #d4af37;
            padding-bottom: 14px;
            font-family: 'Playfair Display', serif;
            position: relative;
            z-index: 1;
        }
        
        .detail-text {
            color: #c5c9d0;
            font-weight: 400;
            line-height: 1.7;
            font-family: 'Inter', sans-serif;
            position: relative;
            z-index: 1;
            margin-bottom: 12px;
        }
        
        .detail-text strong {
            color: #ffffff;
            font-weight: 600;
        }
        
        /* Dividers */
        .divider {
            height: 2px;
            background: linear-gradient(90deg, transparent 0%, rgba(212, 175, 55, 0.2) 10%, rgba(212, 175, 55, 0.8) 50%, rgba(212, 175, 55, 0.2) 90%, transparent 100%);
            margin: 3rem 0;
            position: relative;
            border-radius: 1px;
        }
        
        .divider::before {
            content: '◆';
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            background: rgba(32, 37, 43, 1);
            color: #d4af37;
            padding: 0 16px;
            font-size: 1rem;
            font-weight: 300;
        }
        
        /* General Streamlit Elements */
        .stMarkdown {
            color: #c5c9d0;
            font-family: 'Inter', sans-serif;
        }
        
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
            color: #ffffff;
            font-family: 'Playfair Display', serif;
        }
        
        .stCaption {
            color: #8a8e95 !important;
            font-family: 'Inter', sans-serif !important;
        }
        
        /* Layout */
        div[data-testid="stToolbar"] {
            display: none;
        }
        
        .main .block-container {
            padding-top: 1rem;
            max-width: 1200px;
        }
        
        /* Sidebar */
        .css-1d391kg {
            background: rgba(25, 30, 35, 0.98) !important;
            backdrop-filter: blur(10px) !important;
        }
        
        /* Warning/Info Messages */
        .stWarning {
            background: rgba(255, 187, 51, 0.1) !important;
            border: 1px solid rgba(255, 187, 51, 0.3) !important;
            border-radius: 10px !important;
            color: #ffbb33 !important;
        }
        
        .stInfo {
            background: rgba(212, 175, 55, 0.1) !important;
            border: 1px solid rgba(212, 175, 55, 0.3) !important;
            border-radius: 10px !important;
            color: #d4af37 !important;
        }
        
        .stError {
            background: rgba(220, 53, 69, 0.1) !important;
            border: 1px solid rgba(220, 53, 69, 0.3) !important;
            border-radius: 10px !important;
            color: #dc3545 !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header with sophisticated restaurant design
    st.markdown("""
    <div class="main-header">
        <h1>CleanPlate</h1>
        <p>Premium Restaurant Health Inspection Intelligence</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Jurisdiction selector with system information
    col_juris, col_search, col_location = st.columns([1, 2, 1])
    
    with col_juris:
        jurisdictions = st.session_state.api_client.get_available_jurisdictions()
        jurisdiction_names = {
            "NYC": "New York City", 
            "Chicago": "Chicago, IL",
            "Boston": "Boston, MA",
            "Austin": "Austin, TX", 
            "Seattle": "Seattle, WA",
            "San Diego": "San Diego, CA"
        }
        jurisdiction_options = [jurisdiction_names.get(j, j) for j in jurisdictions]
        
        selected_jurisdiction_display = st.selectbox(
            "City", 
            jurisdiction_options,
            index=jurisdiction_options.index(jurisdiction_names[st.session_state.current_jurisdiction])
        )
        
        # Map back to jurisdiction code
        reverse_map = {v: k for k, v in jurisdiction_names.items()}
        selected_jurisdiction = reverse_map.get(selected_jurisdiction_display, "NYC")
        
        # Update API client if jurisdiction changed
        if selected_jurisdiction != st.session_state.current_jurisdiction:
            st.session_state.current_jurisdiction = selected_jurisdiction
            st.session_state.api_client.set_jurisdiction(selected_jurisdiction)
            st.rerun()
        
        # Show grading system info
        grading_info = st.session_state.api_client.get_grading_system_info()
        if grading_info.get('type') == 'letter':
            st.caption("🅰️ Letter Grade System (A, B, C)")
        elif grading_info.get('type') == 'pass_fail':
            st.caption("✓ Pass/Fail System")
    
    with col_search:
        search_term = st.text_input(
            "Search for a restaurant", 
            placeholder="Enter restaurant name...",
            help="Search by restaurant name to see health inspection results"
        )
    
    with col_location:
        # Location filter
        try:
            locations = st.session_state.api_client.get_available_locations()
            location_label = "Borough" if selected_jurisdiction == "NYC" else "Ward"
            selected_location = st.selectbox(location_label, ["All"] + locations)
        except Exception as e:
            st.error(f"Failed to load locations: {str(e)}")
            selected_location = "All"
    
    # Display grading system explanation based on jurisdiction
    grading_info = st.session_state.api_client.get_grading_system_info()
    
    with st.expander("ℹ️ Understanding This City's Health Inspection System", expanded=False):
        if st.session_state.current_jurisdiction == "NYC":
            st.markdown("""
            **New York City Letter Grade System:**
            - **Grade A**: Excellent (0-13 violation points)
            - **Grade B**: Good (14-27 violation points) 
            - **Grade C**: Needs Improvement (28+ violation points)
            - **Pending**: Recently inspected, grade under review
            
            **Scoring**: Lower scores indicate better performance. Restaurants with 14+ points must post their grade.
            """)
        elif st.session_state.current_jurisdiction == "Chicago":
            st.markdown("""
            **Chicago Pass/Fail System:**
            - **Pass**: Meets all health requirements
            - **Pass with Conditions**: Minor violations corrected during inspection
            - **Fail**: Serious violations requiring follow-up inspection
            - **Out of Business**: Facility permanently closed
            
            **Risk Levels**: 
            - **High Risk**: Facilities handling potentially hazardous foods
            - **Medium Risk**: Limited food preparation
            - **Low Risk**: Minimal food handling (convenience stores, etc.)
            """)
        elif st.session_state.current_jurisdiction == "Austin":
            st.markdown("""
            **Austin Numeric Scoring System:**
            - **90-100**: Grade A - Excellent
            - **80-89**: Grade B - Good
            - **70-79**: Grade C - Satisfactory
            - **Below 70**: Grade F - Needs Improvement
            
            **Scoring**: Higher scores indicate better performance. Restaurants must post scores of 70 or above.
            """)
        elif st.session_state.current_jurisdiction == "Seattle":
            st.markdown("""
            **Seattle Rating System:**
            - **Excellent**: Outstanding compliance with health codes
            - **Good**: Generally compliant with minor issues
            - **Okay**: Some violations requiring attention
            - **Needs Improvement**: Significant violations found
            - **Unsatisfactory**: Major health code violations
            """)
        elif st.session_state.current_jurisdiction == "Boston":
            st.markdown("""
            **Boston Violation Level System:**
            - **No Violations**: Clean inspection with no issues found
            - ***** (3 stars): Minor violations
            - ***** (2 stars): Serious violations
            - ***** (1 star): Critical violations requiring immediate attention
            
            **System**: Based on violation severity rather than letter grades.
            """)
        elif st.session_state.current_jurisdiction == "San Diego":
            st.markdown("""
            **San Diego Letter Grade System:**
            - **Grade A**: Excellent (90-100 points)
            - **Grade B**: Good (80-89 points)
            - **Grade C**: Satisfactory (70-79 points)
            
            **Scoring**: Similar to Los Angeles County system with numerical scores.
            """)
    
    # Set default grades based on jurisdiction
    if st.session_state.current_jurisdiction == "NYC":
        selected_grades = ["A", "B", "C", "Grade Pending", "Not Yet Graded"]
    else:  # Chicago
        selected_grades = ["Pass", "Pass w/ Conditions", "Fail", "Not Ready"]
    
    selected_cuisines = None
    date_range = None
    
    # Add search button to control when search executes
    search_button = st.button("Search", type="primary", use_container_width=False)
    
    # Initialize session state for search trigger
    if 'search_triggered' not in st.session_state:
        st.session_state.search_triggered = False
    
    # Main content area
    try:
        # Only search when button is clicked or on initial load
        if search_button or not st.session_state.search_triggered:
            st.session_state.search_triggered = True
            
            # Show spinner only when actively searching
            if search_button and (search_term or selected_location != "All"):
                with st.spinner("Searching for results..."):
                    restaurants_df = st.session_state.api_client.get_restaurants(
                        location=selected_location if selected_location != "All" else None,
                        grades=selected_grades,
                        cuisines=selected_cuisines,
                        search_term=search_term,
                        date_range=date_range
                    )
            else:
                # Load default data without spinner for initial load
                restaurants_df = st.session_state.api_client.get_restaurants(
                    location=None,
                    grades=selected_grades,
                    cuisines=selected_cuisines,
                    search_term=None,
                    date_range=date_range
                )
        else:
            # Return empty dataframe if search hasn't been triggered
            restaurants_df = pd.DataFrame()
        
        # Handle empty results quietly
        if restaurants_df.empty:
            st.markdown("""
            <div class="stats-container">
                <h4 style="color: #ffbb33; margin: 0;">ℹ️ No restaurants found</h4>
                <p style="color: #b0b0b0; margin: 0.5rem 0 0 0;">Try adjusting your search criteria or selecting a different borough</p>
            </div>
            """, unsafe_allow_html=True)
            
        # Save restaurants to database
        if not restaurants_df.empty:
            for _, restaurant in restaurants_df.iterrows():
                restaurant_data = restaurant.to_dict()
                violations = restaurant_data.pop('violations', [])
                save_restaurant_to_db(restaurant_data, violations)
        
        if restaurants_df.empty:
            st.warning("No restaurants found matching your criteria. Please adjust your filters.")
            return
        
        # Show results count
        if search_term:
            st.subheader(f"Found {len(restaurants_df)} restaurants matching '{search_term}'")
        else:
            st.subheader(f"Showing {len(restaurants_df)} recent inspections")
        
        # Sort by most recent inspections by default
        restaurants_df = restaurants_df.sort_values('inspection_date', ascending=False)
        
        # Display restaurants as simple list
        for _, restaurant in restaurants_df.iterrows():
            display_simple_restaurant_card(restaurant)
    
    except Exception as e:
        st.error(f"Error loading restaurant data: {str(e)}")
        st.info("Please check your internet connection and try again.")

def display_simple_restaurant_card(restaurant):
    """Display restaurant card with sophisticated dark restaurant theme"""
    

    
    # Use expander with enhanced visual hierarchy
    with st.expander(f"{restaurant['name']}", expanded=True):
        # Restaurant information with dark theme styling
        st.markdown('<div class="info-section">', unsafe_allow_html=True)
        st.markdown('<h4 class="section-header">📍 Location Details</h4>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f'<div class="detail-text"><strong>Address:</strong> {restaurant.get("address", "N/A")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="detail-text"><strong>Cuisine:</strong> {restaurant.get("cuisine_type", "Not specified")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="detail-text"><strong>Location:</strong> {restaurant.get("boro", "N/A")}</div>', unsafe_allow_html=True)
        
        with col2:
            # Get jurisdiction-specific grade information
            grade = restaurant.get('grade', 'Not Yet Graded')
            grade_info = st.session_state.api_client.get_grade_info(grade)
            grading_system = st.session_state.api_client.get_grading_system_info()
            
            # Display grade with jurisdiction-specific styling
            st.markdown(f"""
            <div style="background-color: {grade_info['color']}20; border: 2px solid {grade_info['color']}; 
                        border-radius: 12px; padding: 16px; text-align: center; margin-bottom: 8px;">
                <div style="font-size: 1.5rem; font-weight: 700; color: {grade_info['color']};">
                    {grade_info['label']}
                </div>
                <div style="font-size: 0.9rem; color: #666; margin-top: 4px;">
                    {grade_info['description']}
                </div>
                <div style="font-size: 0.8rem; color: #888; margin-top: 2px;">
                    {grading_system.get('type', '').replace('_', ' ').title()} System
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show risk level for jurisdictions that use risk systems
            if grading_system.get('risk_system') and 'risk' in restaurant and restaurant['risk']:
                risk_level = restaurant['risk']
                risk_info = st.session_state.api_client.get_risk_info(risk_level)
                st.markdown(f"""
                <div style="background-color: {risk_info['color']}15; border: 1px solid {risk_info['color']}; 
                            border-radius: 8px; padding: 12px; text-align: center; margin-bottom: 8px;">
                    <div style="font-size: 1rem; font-weight: 600; color: {risk_info['color']};">
                        {risk_info['label']}
                    </div>
                    <div style="font-size: 0.8rem; color: #666; margin-top: 2px;">
                        {risk_info['description']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Show inspection score for jurisdictions that use scoring systems
            if grading_system.get('score_system') and 'score' in restaurant and pd.notna(restaurant['score']):
                st.markdown(f"""
                <div style="background-color: #9CAF8820; border: 1px solid #9CAF88; 
                            border-radius: 8px; padding: 12px; text-align: center;">
                    <div style="font-size: 2rem; font-weight: 700; color: #9CAF88;">{restaurant['score']}</div>
                    <div style="font-size: 0.9rem; color: #666;">Inspection Score</div>
                    <div style="font-size: 0.8rem; color: #888;">{grading_system.get('score_description', '')}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Visual divider
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Violations section with progressive disclosure
        st.markdown('<h4 class="section-header">⚠️ Health Inspection Results</h4>', unsafe_allow_html=True)
        
        if 'violations' in restaurant and restaurant['violations']:
            violations = [v for v in restaurant['violations'] if v != "No violations recorded"]
            if violations:
                # Show first 2 violations prominently
                for i, violation in enumerate(violations[:2]):
                    priority_class = "priority-high" if "critical" in violation.lower() else "priority-medium"
                    icon = "🔴" if "critical" in violation.lower() else "🟡"
                    
                    st.markdown(f"""
                    <div class="content-block {priority_class}">
                        <div style="font-weight: 600; margin-bottom: 0.5rem;">{icon} Violation {i+1}</div>
                        <div>{violation}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Progressive disclosure for additional violations
                if len(violations) > 2:
                    with st.expander(f"View {len(violations) - 2} additional violations", expanded=False):
                        for i, violation in enumerate(violations[2:], start=3):
                            priority_class = "priority-high" if "critical" in violation.lower() else "priority-medium"
                            icon = "🔴" if "critical" in violation.lower() else "🟡"
                            
                            st.markdown(f"""
                            <div class="content-block {priority_class}">
                                <div style="font-weight: 600; margin-bottom: 0.5rem;">{icon} Violation {i}</div>
                                <div>{violation}</div>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="content-block priority-low">
                    <div style="text-align: center; font-weight: 600;">
                        ✅ No violations recorded - Excellent compliance!
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="content-block priority-low">
                <div style="text-align: center; font-weight: 600;">
                    ✅ No violations recorded - Excellent compliance!
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Inspection date footer with subtle styling
        if restaurant.get('inspection_date') and restaurant['inspection_date'] != 'N/A':
            st.markdown(f"""
            <div style="text-align: center; margin-top: 2rem; padding: 1rem; background: rgba(156, 175, 136, 0.1); border-radius: 8px;">
                <small style="color: #9CAF88; font-weight: 500;">Last inspected: {restaurant['inspection_date']}</small>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
