import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os
from data_fetcher import HealthInspectionAPI
from utils import format_grade_badge, calculate_average_rating, get_cuisine_types

# Configure page
st.set_page_config(
    page_title="Restaurant Health Inspection Tracker",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'user_reviews' not in st.session_state:
    st.session_state.user_reviews = {}

if 'api_client' not in st.session_state:
    st.session_state.api_client = HealthInspectionAPI()

def main():
    st.title("🏥 Restaurant Health Inspection Tracker")
    st.markdown("Make informed dining decisions based on official health inspection data")
    
    # Sidebar for filters
    with st.sidebar:
        st.header("🔍 Filter & Search")
        
        # Search functionality
        search_term = st.text_input("Search restaurants", placeholder="Enter restaurant name...")
        
        # Location filter
        try:
            locations = st.session_state.api_client.get_available_locations()
            selected_location = st.selectbox("Location", ["All"] + locations)
        except Exception as e:
            st.error(f"Failed to load locations: {str(e)}")
            selected_location = "All"
        
        # Grade filter
        selected_grades = st.multiselect(
            "Health Grades",
            ["A", "B", "C", "Grade Pending", "Not Yet Graded"],
            default=["A", "B", "C"]
        )
        
        # Cuisine type filter
        try:
            cuisine_types = get_cuisine_types()
            selected_cuisines = st.multiselect("Cuisine Type", ["All"] + cuisine_types)
        except Exception as e:
            st.error(f"Failed to load cuisine types: {str(e)}")
            selected_cuisines = ["All"]
        
        # Inspection date filter
        st.subheader("Inspection Date Range")
        date_range = st.date_input(
            "Select date range",
            value=(datetime.now() - timedelta(days=365), datetime.now()),
            max_value=datetime.now()
        )
        
        # Apply filters button
        if st.button("Apply Filters", type="primary"):
            st.rerun()
    
    # Main content area
    try:
        # Fetch restaurant data
        with st.spinner("Loading restaurant data..."):
            restaurants_df = st.session_state.api_client.get_restaurants(
                location=selected_location if selected_location != "All" else None,
                grades=selected_grades,
                cuisines=selected_cuisines if "All" not in selected_cuisines else None,
                search_term=search_term,
                date_range=date_range
            )
        
        if restaurants_df.empty:
            st.warning("No restaurants found matching your criteria. Please adjust your filters.")
            return
        
        # Display summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Restaurants", len(restaurants_df))
        with col2:
            grade_a_count = len(restaurants_df[restaurants_df['grade'] == 'A'])
            st.metric("Grade A Restaurants", grade_a_count)
        with col3:
            avg_score = restaurants_df['score'].mean() if 'score' in restaurants_df.columns else 0
            st.metric("Average Inspection Score", f"{avg_score:.1f}")
        with col4:
            recent_inspections = len(restaurants_df[
                pd.to_datetime(restaurants_df['inspection_date']) >= (datetime.now() - timedelta(days=30))
            ])
            st.metric("Recent Inspections (30 days)", recent_inspections)
        
        # Sort options
        sort_col1, sort_col2 = st.columns([3, 1])
        with sort_col1:
            sort_by = st.selectbox(
                "Sort by:",
                ["Restaurant Name", "Health Grade", "Inspection Date", "User Rating"],
                index=2
            )
        with sort_col2:
            sort_order = st.selectbox("Order:", ["Descending", "Ascending"])
        
        # Sort dataframe
        if sort_by == "Restaurant Name":
            restaurants_df = restaurants_df.sort_values('name', ascending=(sort_order == "Ascending"))
        elif sort_by == "Health Grade":
            grade_order = {'A': 1, 'B': 2, 'C': 3, 'Grade Pending': 4, 'Not Yet Graded': 5}
            restaurants_df['grade_order'] = restaurants_df['grade'].map(grade_order)
            restaurants_df = restaurants_df.sort_values('grade_order', ascending=(sort_order == "Ascending"))
        elif sort_by == "Inspection Date":
            restaurants_df = restaurants_df.sort_values('inspection_date', ascending=(sort_order == "Ascending"))
        elif sort_by == "User Rating":
            restaurants_df['user_rating'] = restaurants_df['id'].apply(calculate_average_rating)
            restaurants_df = restaurants_df.sort_values('user_rating', ascending=(sort_order == "Ascending"))
        
        # Display restaurants in card format
        st.header(f"📋 Restaurants ({len(restaurants_df)} found)")
        
        # Create cards in columns (2 per row)
        for i in range(0, len(restaurants_df), 2):
            col1, col2 = st.columns(2)
            
            # First restaurant card
            with col1:
                display_restaurant_card(restaurants_df.iloc[i])
            
            # Second restaurant card (if exists)
            if i + 1 < len(restaurants_df):
                with col2:
                    display_restaurant_card(restaurants_df.iloc[i + 1])
    
    except Exception as e:
        st.error(f"Error loading restaurant data: {str(e)}")
        st.info("Please check your internet connection and try again.")

def display_restaurant_card(restaurant):
    """Display a single restaurant card with health inspection info and user reviews"""
    
    with st.container():
        # Restaurant header
        st.markdown(f"### {restaurant['name']}")
        
        # Grade badge and basic info
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            grade_html = format_grade_badge(restaurant['grade'])
            st.markdown(grade_html, unsafe_allow_html=True)
        
        with col2:
            if 'score' in restaurant and pd.notna(restaurant['score']):
                st.metric("Score", f"{restaurant['score']}/100")
        
        with col3:
            user_rating = calculate_average_rating(restaurant['id'])
            if user_rating > 0:
                st.metric("User Rating", f"⭐ {user_rating:.1f}/5")
        
        # Restaurant details
        st.write(f"**Address:** {restaurant.get('address', 'N/A')}")
        st.write(f"**Cuisine:** {restaurant.get('cuisine_type', 'N/A')}")
        st.write(f"**Last Inspection:** {restaurant.get('inspection_date', 'N/A')}")
        
        # Inspection details
        if 'violations' in restaurant and restaurant['violations']:
            with st.expander("🔍 Inspection Details"):
                st.write("**Violations Found:**")
                for violation in restaurant['violations']:
                    st.write(f"• {violation}")
        
        # User reviews section
        restaurant_id = restaurant['id']
        
        with st.expander("💬 User Reviews & Ratings"):
            # Display existing reviews
            if restaurant_id in st.session_state.user_reviews:
                reviews = st.session_state.user_reviews[restaurant_id]
                st.write("**Recent Reviews:**")
                for review in reviews[-3:]:  # Show last 3 reviews
                    st.write(f"⭐ **{review['rating']}/5** - {review['comment']}")
                    st.caption(f"Posted on {review['date']}")
                    st.divider()
            
            # Add new review form
            st.write("**Add Your Review:**")
            rating = st.slider(f"Rating for {restaurant['name']}", 1, 5, 3, key=f"rating_{restaurant_id}")
            comment = st.text_area(f"Your experience", key=f"comment_{restaurant_id}", 
                                 placeholder="Share your thoughts about this restaurant's cleanliness and food safety...")
            
            if st.button(f"Submit Review", key=f"submit_{restaurant_id}"):
                if comment.strip():
                    # Add review to session state
                    if restaurant_id not in st.session_state.user_reviews:
                        st.session_state.user_reviews[restaurant_id] = []
                    
                    new_review = {
                        'rating': rating,
                        'comment': comment.strip(),
                        'date': datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    
                    st.session_state.user_reviews[restaurant_id].append(new_review)
                    st.success("Review submitted successfully!")
                    st.rerun()
                else:
                    st.warning("Please enter a comment for your review.")
        
        st.divider()

if __name__ == "__main__":
    main()
