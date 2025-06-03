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
    page_title="Restaurant Health Inspection Tracker",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
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
    st.title("🏥 Restaurant Health Inspection Tracker")
    st.markdown("Search restaurants and view their health inspection grades and violations")
    
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
        # Fetch restaurant data with progress indicator
        with st.spinner("Loading restaurant inspection data from NYC database..."):
            restaurants_df = st.session_state.api_client.get_restaurants(
                location=selected_location if selected_location != "All" else None,
                grades=selected_grades,
                cuisines=selected_cuisines,
                search_term=search_term,
                date_range=date_range
            )
            
        # Display data statistics
        if not restaurants_df.empty:
            st.success(f"✅ Retrieved {len(restaurants_df)} restaurant inspection records from NYC Health Department database")
        else:
            st.info("No restaurant inspection records found matching your search criteria")
            
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
    """Display a simplified restaurant card with health inspection info"""
    
    with st.container():
        # Create columns for layout
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"### {restaurant['name']}")
            st.write(f"**Address:** {restaurant.get('address', 'N/A')}")
            if restaurant.get('cuisine_type'):
                st.write(f"**Cuisine:** {restaurant['cuisine_type']}")
        
        with col2:
            # Health grade badge
            grade_html = format_grade_badge(restaurant['grade'])
            st.markdown(grade_html, unsafe_allow_html=True)
        
        with col3:
            # Inspection score
            if 'score' in restaurant and pd.notna(restaurant['score']):
                st.metric("Score", f"{restaurant['score']}")
                st.caption("(Lower is better)")
        
        # Violations section
        if 'violations' in restaurant and restaurant['violations']:
            violations = [v for v in restaurant['violations'] if v != "No violations recorded"]
            if violations:
                st.write("**⚠️ Violations Found:**")
                for violation in violations[:3]:  # Show up to 3 violations
                    st.write(f"• {violation}")
                if len(violations) > 3:
                    st.caption(f"...and {len(violations) - 3} more violation(s)")
            else:
                st.write("**✅ No violations recorded**")
        else:
            st.write("**✅ No violations recorded**")
        
        # Inspection date
        if restaurant.get('inspection_date') and restaurant['inspection_date'] != 'N/A':
            st.caption(f"Last inspected: {restaurant['inspection_date']}")
        
        st.divider()

if __name__ == "__main__":
    main()
