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
    
    # Premium dark theme with purple accents and geometric patterns
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        .stApp {
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            color: #ffffff;
            font-family: 'Inter', sans-serif;
        }
        
        .main-header {
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
            padding: 3rem 2rem;
            border-radius: 0 0 24px 24px;
            margin: -1rem -1rem 2rem -1rem;
            position: relative;
            overflow: hidden;
            border-bottom: 1px solid rgba(139, 92, 246, 0.3);
        }
        
        .main-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                radial-gradient(circle at 20% 80%, rgba(139, 92, 246, 0.15) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(59, 130, 246, 0.1) 0%, transparent 50%);
            pointer-events: none;
        }
        
        .main-header::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: 
                repeating-linear-gradient(45deg, transparent, transparent 2px, rgba(139, 92, 246, 0.04) 2px, rgba(139, 92, 246, 0.04) 4px),
                repeating-linear-gradient(-45deg, transparent, transparent 2px, rgba(59, 130, 246, 0.03) 2px, rgba(59, 130, 246, 0.03) 4px);
            pointer-events: none;
        }
        
        .main-header h1 {
            color: #ffffff;
            font-size: 3.5rem;
            font-weight: 800;
            margin: 0;
            font-family: 'Inter', sans-serif;
            letter-spacing: -0.03em;
            line-height: 1.1;
            position: relative;
            z-index: 2;
            background: linear-gradient(135deg, #ffffff 0%, #e2e8f0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .main-header p {
            color: #94a3b8;
            font-size: 1.25rem;
            margin: 1rem 0 0 0;
            font-weight: 400;
            letter-spacing: 0.01em;
            position: relative;
            z-index: 2;
        }
        
        .stSelectbox > div > div {
            background: rgba(15, 23, 42, 0.8) !important;
            border: 1px solid rgba(139, 92, 246, 0.3) !important;
            border-radius: 12px !important;
            color: #ffffff !important;
            backdrop-filter: blur(10px) !important;
        }
        
        .stTextInput > div > div > input {
            background: rgba(15, 23, 42, 0.8) !important;
            border: 1px solid rgba(139, 92, 246, 0.3) !important;
            border-radius: 12px !important;
            color: #ffffff !important;
            backdrop-filter: blur(10px) !important;
            padding: 12px 16px !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: rgba(139, 92, 246, 0.6) !important;
            box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1) !important;
        }
        
        .stButton > button {
            background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%) !important;
            border: none !important;
            border-radius: 12px !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            padding: 12px 24px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 16px rgba(139, 92, 246, 0.3) !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 24px rgba(139, 92, 246, 0.4) !important;
            background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%) !important;
        }
        
        .stExpander {
            background: rgba(15, 23, 42, 0.6) !important;
            border: 1px solid rgba(139, 92, 246, 0.2) !important;
            border-radius: 16px !important;
            backdrop-filter: blur(20px) !important;
            margin: 1rem 0 !important;
        }
        
        .stExpander > div:first-child {
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%) !important;
            border-radius: 16px 16px 0 0 !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            border-bottom: 1px solid rgba(139, 92, 246, 0.2) !important;
        }
        
        .info-section {
            background: rgba(15, 23, 42, 0.6);
            border-radius: 12px;
            padding: 20px;
            margin: 16px 0;
            border: 1px solid rgba(139, 92, 246, 0.15);
            backdrop-filter: blur(15px);
        }
        
        .section-header {
            color: #e2e8f0;
            font-size: 1.1rem;
            font-weight: 600;
            margin: 0 0 16px 0;
            letter-spacing: 0.02em;
            border-bottom: 2px solid rgba(139, 92, 246, 0.3);
            padding-bottom: 8px;
        }
        
        .detail-text {
            color: #cbd5e1;
            font-weight: 400;
            line-height: 1.6;
        }
        
        .detail-text strong {
            color: #ffffff;
            font-weight: 600;
        }
        
        .stMarkdown {
            color: #cbd5e1;
        }
        
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
            color: #ffffff;
        }
        
        div[data-testid="stToolbar"] {
            display: none;
        }
        
        .main .block-container {
            padding-top: 1rem;
            max-width: 1200px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header with gradient background
    st.markdown("""
    <div class="main-header">
        <h1>🍽️ CleanPlate</h1>
        <p>Discover restaurants with their latest health inspection grades and safety records</p>
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
    """Display restaurant card with premium dark theme and glassmorphism effects"""
    
    # Premium dark theme styling for restaurant cards
    st.markdown("""
    <style>
    .streamlit-expander {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(139, 92, 246, 0.2) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(20px) !important;
        margin: 1.5rem 0 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 8px 32px rgba(15, 23, 42, 0.5) !important;
    }
    .streamlit-expander:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 16px 48px rgba(15, 23, 42, 0.7) !important;
        border-color: rgba(139, 92, 246, 0.4) !important;
    }
    .streamlit-expander > div:first-child {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(59, 130, 246, 0.1) 100%) !important;
        border-radius: 16px 16px 0 0 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        padding: 1.25rem 1.5rem !important;
        border-bottom: 1px solid rgba(139, 92, 246, 0.2) !important;
    }
    .streamlit-expander > div:last-child {
        background: rgba(15, 23, 42, 0.4) !important;
        border-radius: 0 0 16px 16px !important;
        padding: 1.5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Use expander with enhanced visual hierarchy
    with st.expander(f"🍽️ {restaurant['name']}", expanded=True):
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
