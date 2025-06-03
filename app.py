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
    
    # Sage green themed styling with enhanced visual hierarchy
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(135deg, #9CAF88, #B8C5A8);
            padding: 2rem 2.5rem;
            border-radius: 15px;
            margin-bottom: 3rem;
            text-align: center;
            box-shadow: 0 8px 32px rgba(156, 175, 136, 0.3);
        }
        .main-header h1 {
            color: #2F3E2F;
            margin: 0;
            font-size: 3rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }
        .main-header p {
            color: #3A4F3A;
            margin: 1rem 0 0 0;
            font-size: 1.3rem;
            font-weight: 400;
        }
        
        /* Typography Hierarchy */
        .section-header {
            font-size: 1.5rem;
            font-weight: 600;
            color: #9CAF88;
            margin: 2rem 0 1rem 0;
            border-bottom: 2px solid #9CAF88;
            padding-bottom: 0.5rem;
        }
        
        .content-block {
            background: #3A4F3A;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            border-left: 4px solid #9CAF88;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        }
        
        .info-group {
            background: rgba(156, 175, 136, 0.1);
            border-radius: 10px;
            padding: 1.25rem;
            margin: 1rem 0;
            border: 1px solid rgba(156, 175, 136, 0.3);
        }
        
        .priority-high {
            background: #8B4F47;
            color: #F5F7F5;
        }
        
        .priority-medium {
            background: #C5A572;
            color: #2F3E2F;
        }
        
        .priority-low {
            background: #9CAF88;
            color: #F5F7F5;
        }
        
        .divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, #9CAF88, transparent);
            margin: 2rem 0;
        }
        
        /* Enhanced spacing */
        .spaced-content > * {
            margin-bottom: 1.5rem;
        }
        
        .card-grid {
            display: grid;
            gap: 2rem;
            margin: 2rem 0;
        }
        
        /* Visual emphasis */
        .highlight-box {
            background: linear-gradient(135deg, #9CAF88, #B8C5A8);
            color: #2F3E2F;
            padding: 1rem 1.5rem;
            border-radius: 25px;
            font-weight: 600;
            text-align: center;
            box-shadow: 0 4px 12px rgba(156, 175, 136, 0.4);
        }
        
        .metric-container {
            background: #3A4F3A;
            border-radius: 10px;
            padding: 1.5rem;
            text-align: center;
            border: 2px solid #9CAF88;
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
    
    # Jurisdiction selector
    col_juris, col_search, col_location = st.columns([1, 2, 1])
    
    with col_juris:
        jurisdictions = st.session_state.api_client.get_available_jurisdictions()
        jurisdiction_names = {"NYC": "New York City", "Chicago": "Chicago, IL"}
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
    
    # Set default grades to show all grades
    selected_grades = ["A", "B", "C", "Grade Pending", "Not Yet Graded"]
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
    """Display restaurant card with enhanced visual hierarchy and sage green theme"""
    
    # Enhanced sage green styling for restaurant cards
    st.markdown("""
    <style>
    .streamlit-expander {
        border: 3px solid #9CAF88 !important;
        border-radius: 15px !important;
        background: linear-gradient(135deg, #3A4F3A 0%, #2F3E2F 100%) !important;
        box-shadow: 0 12px 32px rgba(156, 175, 136, 0.25) !important;
        margin: 2rem 0 !important;
        transition: all 0.3s ease !important;
    }
    .streamlit-expander:hover {
        transform: translateY(-4px) !important;
        box-shadow: 0 16px 40px rgba(156, 175, 136, 0.35) !important;
    }
    .streamlit-expander > div:first-child {
        background: linear-gradient(90deg, #9CAF88, #B8C5A8, #9CAF88) !important;
        border-radius: 12px 12px 0 0 !important;
        color: #2F3E2F !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        padding: 1rem 1.5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Use expander with enhanced visual hierarchy
    with st.expander(f"🍽️ {restaurant['name']}", expanded=True):
        # Restaurant information with clear visual grouping
        st.markdown('<div class="info-group">', unsafe_allow_html=True)
        st.markdown('<h4 class="section-header">📍 Location Details</h4>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**Address:** {restaurant.get('address', 'N/A')}")
            st.markdown(f"**Cuisine:** {restaurant.get('cuisine_type', 'Not specified')}")
            st.markdown(f"**Borough:** {restaurant.get('boro', 'N/A')}")
        
        with col2:
            # Health grade with priority-based styling
            grade = restaurant.get('grade', 'Not Yet Graded')
            grade_class = "priority-low" if grade == 'A' else "priority-medium" if grade == 'B' else "priority-high" if grade == 'C' else "priority-medium"
            
            st.markdown(f"""
            <div class="highlight-box {grade_class}">
                <div style="font-size: 1.5rem; font-weight: 700;">Grade: {grade}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Inspection score with enhanced metric display
            if 'score' in restaurant and pd.notna(restaurant['score']):
                st.markdown(f"""
                <div class="metric-container">
                    <div style="font-size: 2rem; font-weight: 700; color: #9CAF88;">{restaurant['score']}</div>
                    <div style="font-size: 0.9rem; color: #F5F7F5; opacity: 0.8;">Inspection Score</div>
                    <div style="font-size: 0.8rem; color: #F5F7F5; opacity: 0.6;">(Lower is better)</div>
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
