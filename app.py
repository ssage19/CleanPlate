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

# Initialize database on startup
initialize_database()

def main():
    
    # Custom CSS for enhanced dark theme styling
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(90deg, #00C851, #007E33);
            padding: 1.5rem 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            text-align: center;
        }
        .main-header h1 {
            color: white;
            margin: 0;
            font-size: 2.5rem;
            font-weight: 700;
        }
        .main-header p {
            color: #e0e0e0;
            margin: 0.5rem 0 0 0;
            font-size: 1.1rem;
        }
        .restaurant-card {
            background: #262730;
            border: 1px solid #3d3d3d;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        .grade-badge {
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 25px;
            font-weight: bold;
            font-size: 1.2rem;
            margin-right: 1rem;
        }
        .grade-a { background: #00C851; color: white; }
        .grade-b { background: #ffbb33; color: black; }
        .grade-c { background: #ff4444; color: white; }
        .grade-pending { background: #33b5e5; color: white; }
        .grade-not-graded { background: #aa66cc; color: white; }
        .stats-container {
            background: #1e2130;
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .violation-item {
            background: #1e1e1e;
            border-left: 4px solid #ff4444;
            padding: 0.8rem;
            margin: 0.5rem 0;
            border-radius: 5px;
        }
        .critical-violation {
            border-left-color: #ff4444;
        }
        .non-critical-violation {
            border-left-color: #ffbb33;
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
    
    # Main search interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_term = st.text_input(
            "Search for a restaurant", 
            placeholder="Enter restaurant name...",
            help="Search by restaurant name to see health inspection results"
        )
    
    with col2:
        # Location filter
        try:
            locations = st.session_state.api_client.get_available_locations()
            selected_location = st.selectbox("Borough", ["All"] + locations)
        except Exception as e:
            st.error(f"Failed to load locations: {str(e)}")
            selected_location = "All"
    
    # Set default grades to show all grades
    selected_grades = ["A", "B", "C", "Grade Pending", "Not Yet Graded"]
    selected_cuisines = None
    date_range = None
    
    # Main content area
    try:
        # Fetch restaurant data silently
        restaurants_df = st.session_state.api_client.get_restaurants(
            location=selected_location if selected_location != "All" else None,
            grades=selected_grades,
            cuisines=selected_cuisines,
            search_term=search_term,
            date_range=date_range
        )
        
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
    """Display a simplified restaurant card using Streamlit components"""
    
    # Create a container with custom styling
    with st.container():
        # Apply custom CSS for this card
        st.markdown("""
        <style>
        .restaurant-container {
            background: #262730;
            border: 1px solid #3d3d3d;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Main restaurant info section
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"### {restaurant['name']}")
            st.write(f"**Address:** {restaurant.get('address', 'N/A')}")
            st.write(f"**Cuisine:** {restaurant.get('cuisine_type', 'Not specified')}")
            st.write(f"**Borough:** {restaurant.get('boro', 'N/A')}")
        
        with col2:
            # Health grade badge
            grade = restaurant.get('grade', 'Not Yet Graded')
            if grade == 'A':
                st.success(f"Grade: {grade}")
            elif grade == 'B':
                st.warning(f"Grade: {grade}")
            elif grade == 'C':
                st.error(f"Grade: {grade}")
            else:
                st.info(f"Grade: {grade}")
            
            # Inspection score
            if 'score' in restaurant and pd.notna(restaurant['score']):
                st.metric("Score", f"{restaurant['score']}", help="Lower is better")
        
        # Violations section
        if 'violations' in restaurant and restaurant['violations']:
            violations = [v for v in restaurant['violations'] if v != "No violations recorded"]
            if violations:
                st.markdown("**⚠️ Health Violations:**")
                for i, violation in enumerate(violations[:3]):
                    if "critical" in violation.lower():
                        st.error(f"🔴 {violation}")
                    else:
                        st.warning(f"🟡 {violation}")
                if len(violations) > 3:
                    st.caption(f"...and {len(violations) - 3} more violation(s)")
            else:
                st.success("✅ No violations recorded")
        else:
            st.success("✅ No violations recorded")
        
        # Inspection date
        if restaurant.get('inspection_date') and restaurant['inspection_date'] != 'N/A':
            st.caption(f"Last inspected: {restaurant['inspection_date']}")
        
        # Add divider
        st.divider()

if __name__ == "__main__":
    main()
