import streamlit as st
import pandas as pd
from data_fetcher import HealthInspectionAPI
from database import init_database, get_restaurant_reviews, save_user_review
from ads import AdManager
import traceback
# Remove invalid imports - implement directly in app

def main():
    # Page configuration
    st.set_page_config(
        page_title="CleanPlate - Restaurant Health Inspections",
        page_icon="🍽️",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for restaurant theme
    st.markdown("""
    <style>
        .main {
            background: linear-gradient(135deg, #1a202c 0%, #2d3748 50%, #1a202c 100%);
            color: #f7fafc;
        }
        
        .stTitle {
            color: #f7fafc !important;
            font-family: 'Playfair Display', serif;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .restaurant-card {
            background: rgba(45, 55, 72, 0.8);
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize database
    init_database()
    
    # Initialize session state variables
    if 'current_jurisdiction' not in st.session_state:
        st.session_state.current_jurisdiction = 'NYC'
    if 'api_client' not in st.session_state:
        st.session_state.api_client = HealthInspectionAPI()
    if 'show_revenue_guide' not in st.session_state:
        st.session_state.show_revenue_guide = False

    # Initialize advertisement manager
    ad_manager = AdManager()
    
    # Header with custom logo - Clean Streamlit approach
    col_logo, col_title = st.columns([0.2, 0.8])
    
    with col_logo:
        st.image("./static/cleanplate-logo.png", width=80)
    
    with col_title:
        st.markdown("""
        <div style="padding-top: 15px;">
            <h1 style="
                font-family: 'Playfair Display', serif; 
                font-weight: 700; 
                font-size: 3.2rem; 
                color: #f7fafc; 
                margin: 0; 
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                line-height: 1.1;
                letter-spacing: -1px;
            ">CleanPlate</h1>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin: 15px 0;">
        <p style="
            font-size: 1.1rem; 
            color: #e2e8f0; 
            font-style: italic;
            font-family: 'Inter', sans-serif;
        ">Peeking behind the kitchen door, so you can dine without doubt. We dish out health inspection scores, making informed choices deliciously easy.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display header ad for revenue generation
    ad_manager.display_banner_ad("header")
    
    # Revenue Setup Menu (Admin Access)
    if st.sidebar.button("💰 Revenue Setup Guide"):
        st.session_state.show_revenue_guide = True
    
    if st.session_state.get('show_revenue_guide', False):
        from revenue_dashboard import display_revenue_setup_guide
        display_revenue_setup_guide()
        if st.button("← Back to App"):
            st.session_state.show_revenue_guide = False
            st.rerun()
        return
    
    # Main interface
    col_juris, col_search, col_location = st.columns([1, 2, 1])
    
    with col_juris:
        jurisdictions = st.session_state.api_client.get_available_jurisdictions()
        jurisdiction_names = {
            "NYC": "New York City, NY", 
            "Chicago": "Chicago, IL",
            "Boston": "Boston, MA",
            "Austin": "Austin, TX", 
            "Seattle": "Seattle, WA",
            "Detroit": "Detroit, MI",
            "Los Angeles": "Los Angeles, CA"
        }
        jurisdiction_options = [jurisdiction_names.get(j, j) for j in jurisdictions]
        
        selected_jurisdiction_display = st.selectbox(
            "City", 
            jurisdiction_options,
            index=jurisdiction_options.index(jurisdiction_names[st.session_state.current_jurisdiction])
        )
        
        reverse_map = {v: k for k, v in jurisdiction_names.items()}
        selected_jurisdiction = reverse_map.get(selected_jurisdiction_display, "NYC")
        
        if selected_jurisdiction != st.session_state.current_jurisdiction:
            st.session_state.current_jurisdiction = selected_jurisdiction
            st.rerun()
    
    with col_search:
        search_term = st.text_input("🔍 Search Restaurants", placeholder="Enter restaurant name...")
    
    with col_location:
        location_filter = st.text_input("📍 Neighborhood", placeholder="Area/zip...")

    st.divider()
    
    # Fetch and display restaurant data
    try:
        with st.spinner(f"Fetching restaurant data from {selected_jurisdiction_display}..."):
            # Get restaurants from current jurisdiction
            restaurants_df = st.session_state.api_client.get_restaurants(
                search_term=search_term,
                location=location_filter
            )
            
            if not restaurants_df.empty:
                # Filter to show only the most recent inspection per restaurant
                restaurants_df = restaurants_df.sort_values(['name', 'inspection_date']).groupby('name').tail(1)
                
                # Apply search filters
                if search_term:
                    mask = restaurants_df['name'].str.contains(search_term, case=False, na=False)
                    restaurants_df = restaurants_df[mask]
                
                if location_filter:
                    mask = restaurants_df['address'].str.contains(location_filter, case=False, na=False)
                    restaurants_df = restaurants_df[mask]
                
                # Display results
                st.markdown(f"### Found {len(restaurants_df)} restaurants")
                
                for idx, restaurant in restaurants_df.iterrows():
                    with st.container():
                        # Restaurant header
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.markdown(f"**{restaurant['name']}**")
                            st.caption(f"📍 {restaurant['address']}")
                        
                        with col2:
                            grade = restaurant.get('grade', 'N/A')
                            if grade == 'A':
                                st.success(f"Grade: {grade}")
                            elif grade == 'B':
                                st.warning(f"Grade: {grade}")
                            elif grade == 'C':
                                st.error(f"Grade: {grade}")
                            else:
                                st.info(f"Grade: {grade}")
                        
                        with col3:
                            score = restaurant.get('score', 'N/A')
                            st.metric("Score", score)
                        
                        # Additional details
                        col_details, col_date = st.columns([2, 1])
                        
                        with col_details:
                            cuisine = restaurant.get('cuisine_type', 'Not specified')
                            st.caption(f"🍽️ {cuisine}")
                        
                        with col_date:
                            inspection_date = restaurant.get('inspection_date', 'Unknown')
                            st.caption(f"📅 {inspection_date}")
                        
                        # User reviews section
                        reviews = get_restaurant_reviews(restaurant['name'])
                        if reviews:
                            avg_rating = sum([r['rating'] for r in reviews]) / len(reviews)
                            st.caption(f"⭐ User Rating: {avg_rating:.1f}/5 ({len(reviews)} reviews)")
                        
                        # Add review button
                        if st.button(f"📝 Add Review", key=f"review_{idx}"):
                            st.session_state[f'show_review_form_{idx}'] = True
                        
                        # Review form
                        if st.session_state.get(f'show_review_form_{idx}', False):
                            with st.form(f"review_form_{idx}"):
                                rating = st.slider("Rating", 1, 5, 3)
                                comment = st.text_area("Comment (optional)")
                                submitted = st.form_submit_button("Submit Review")
                                
                                if submitted:
                                    save_user_review(restaurant['name'], rating, comment)
                                    st.success("Review saved!")
                                    st.session_state[f'show_review_form_{idx}'] = False
                                    st.rerun()
                        
                        # Display advertisement between restaurants
                        if idx % 3 == 2:  # Every 3rd restaurant
                            ad_manager.display_banner_ad("content")
                        
                        st.divider()
            
            else:
                st.warning("No restaurants found matching your criteria.")
                
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        st.error(traceback.format_exc())

if __name__ == "__main__":
    main()