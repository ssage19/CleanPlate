import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from data_fetcher import HealthInspectionAPI
from database import init_database, save_restaurant_to_db
from utils import format_grade_badge, calculate_average_rating

# Set page configuration
st.set_page_config(
    page_title="CleanPlate - Restaurant Health Inspections",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'api_client' not in st.session_state:
    st.session_state.api_client = HealthInspectionAPI()
    st.session_state.current_jurisdiction = "NYC"

# Initialize database on startup
init_database()

def main():
    
    # SINGLE CONSOLIDATED THEME - All styling in one location only
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;500;600;700&display=swap');
        
        /* Main App Background - Sophisticated Restaurant Atmosphere */
        .stApp {
            background: 
                radial-gradient(ellipse at top left, rgba(212, 175, 55, 0.05) 0%, transparent 50%),
                radial-gradient(ellipse at bottom right, rgba(212, 175, 55, 0.03) 0%, transparent 40%),
                linear-gradient(135deg, #0a0e13 0%, #1a1f2e 25%, #2d3748 50%, #1a1f2e 75%, #0a0e13 100%) !important;
            color: #f7fafc !important;
            font-family: 'Inter', sans-serif !important;
            min-height: 100vh !important;
        }
        
        /* Header */
        .main-header {
            background: linear-gradient(135deg, rgba(20, 25, 35, 0.95) 0%, rgba(45, 55, 72, 0.9) 100%);
            padding: 4rem 3rem;
            margin: -1rem -1rem 3rem -1rem;
            border-bottom: 2px solid rgba(212, 175, 55, 0.3);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        }
        
        .main-header h1 {
            color: #ffffff;
            font-size: 4rem;
            font-weight: 600;
            margin: 0;
            font-family: 'Playfair Display', serif;
            text-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        }
        
        .main-header p {
            color: rgba(212, 175, 55, 0.9);
            font-size: 0.95rem;
            margin: 1.5rem 0 0 0;
            font-weight: 500;
            letter-spacing: 0.15em;
            font-family: 'Inter', sans-serif;
            text-transform: uppercase;
        }
        
        /* Form Controls */
        .stSelectbox > div > div {
            background: rgba(45, 55, 72, 0.9) !important;
            border: 1px solid rgba(212, 175, 55, 0.4) !important;
            border-radius: 8px !important;
            color: #f7fafc !important;
        }
        
        .stTextInput > div > div > input {
            background: rgba(45, 55, 72, 0.9) !important;
            border: 1px solid rgba(212, 175, 55, 0.4) !important;
            border-radius: 8px !important;
            color: #f7fafc !important;
            padding: 12px 16px !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #d4af37 !important;
            box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.2) !important;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%) !important;
            border: none !important;
            border-radius: 8px !important;
            color: #1a1f2e !important;
            font-weight: 600 !important;
            padding: 12px 24px !important;
            text-transform: uppercase;
            letter-spacing: 0.02em;
            font-size: 0.875rem;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 24px rgba(212, 175, 55, 0.4) !important;
        }
        
        /* Restaurant Cards */
        .stExpander {
            background: rgba(45, 55, 72, 0.9) !important;
            border: 1px solid rgba(212, 175, 55, 0.3) !important;
            border-radius: 12px !important;
            margin: 2rem 0 !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3) !important;
        }
        
        .stExpander > div:first-child {
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%) !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            font-family: 'Playfair Display', serif !important;
            border-bottom: 1px solid rgba(212, 175, 55, 0.3) !important;
        }
        
        /* Info Sections */
        .info-section {
            background: rgba(45, 55, 72, 0.8);
            border-radius: 8px;
            padding: 20px;
            margin: 16px 0;
            border: 1px solid rgba(212, 175, 55, 0.2);
        }
        
        .section-header {
            color: #ffffff;
            font-size: 1.2rem;
            font-weight: 600;
            margin: 0 0 16px 0;
            border-bottom: 2px solid #d4af37;
            padding-bottom: 8px;
            font-family: 'Playfair Display', serif;
        }
        
        .detail-text {
            color: #e2e8f0;
            font-weight: 400;
            line-height: 1.6;
            font-family: 'Inter', sans-serif;
            margin-bottom: 8px;
        }
        
        .detail-text strong {
            color: #ffffff;
            font-weight: 600;
        }
        
        /* Dividers */
        .divider {
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, rgba(212, 175, 55, 0.5) 50%, transparent 100%);
            margin: 2rem 0;
        }
        
        /* General Elements */
        .stMarkdown {
            color: #e2e8f0;
            font-family: 'Inter', sans-serif;
        }
        
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
            color: #ffffff;
            font-family: 'Playfair Display', serif;
        }
        
        .stCaption {
            color: #a0aec0 !important;
        }
        
        /* Hide Streamlit default elements */
        div[data-testid="stToolbar"] {
            display: none;
        }
        
        /* Hide Streamlit header */
        header[data-testid="stHeader"] {
            display: none !important;
        }
        
        /* Hide top padding from main container */
        .main .block-container {
            padding-top: 0rem !important;
            max-width: 1200px;
        }
        
        /* Ensure no top margin on main container */
        .main {
            padding-top: 0rem !important;
        }
        
        /* Remove any top spacing */
        [data-testid="stAppViewContainer"] {
            padding-top: 0rem !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header with icon
    st.markdown("""
    <div class="main-header">
        <h1>
            <span style="font-size: 48px; vertical-align: middle; margin-right: 16px;">🍽️</span>
            CleanPlate
        </h1>
        <p>Peeking behind the kitchen door, so you can dine without doubt. We dish out health inspection scores, making informed choices deliciously easy.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main interface
    col_juris, col_search, col_location = st.columns([1, 2, 1])
    
    with col_juris:
        jurisdictions = st.session_state.api_client.get_available_jurisdictions()
        jurisdiction_names = {
            "NYC": "New York City", 
            "Chicago": "Chicago, IL",
            "Boston": "Boston, MA",
            "Austin": "Austin, TX", 
            "Seattle": "Seattle, WA",
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
            # Clean up any existing database connections before switching
            try:
                from database import engine
                engine.dispose()  # Close all existing connections
            except:
                pass  # Ignore cleanup errors
            
            st.session_state.current_jurisdiction = selected_jurisdiction
            st.session_state.api_client.set_jurisdiction(selected_jurisdiction)
            st.rerun()
        
        grading_info = st.session_state.api_client.get_grading_system_info()
        if grading_info.get('type') == 'letter':
            st.caption("Letter Grade System (A, B, C)")
        elif grading_info.get('type') == 'pass_fail':
            st.caption("Pass/Fail System")
    
    # Create a form to enable Enter key submission
    with st.form(key="search_form", clear_on_submit=False):
        col_search_form, col_location_form, col_button_form = st.columns([2, 1, 0.5])
        
        with col_search_form:
            search_term = st.text_input(
                "Search for a restaurant", 
                placeholder="Enter restaurant name...",
                help="Search by restaurant name to see health inspection results",
                key="search_input"
            )
        
        with col_location_form:
            locations = st.session_state.api_client.get_available_locations()
            location_filter = st.selectbox(
                "Borough",
                ["All"] + locations,
                key="location_select"
            )
            location_filter = None if location_filter == "All" else location_filter
        
        with col_button_form:
            st.write("")  # Add spacing
            search_clicked = st.form_submit_button("SEARCH", use_container_width=True)

    if search_clicked:
        # Show loading spinner while searching
        with st.spinner("🔍 Searching for results..."):
            try:
                restaurants_df = st.session_state.api_client.get_restaurants(
                    location=location_filter,
                    search_term=search_term,
                    limit=1000
                )
                
                if restaurants_df.empty:
                    st.warning("No restaurants found matching your criteria. Please adjust your filters.")
                    return
                
                # Save to database
                for _, restaurant in restaurants_df.iterrows():
                    restaurant_data = restaurant.to_dict()
                    violations = restaurant_data.pop('violations', [])
                    save_restaurant_to_db(restaurant_data, violations)
                
                st.subheader(f"Showing {len(restaurants_df)} restaurants")
                
                # Display restaurants
                restaurants_df = restaurants_df.sort_values('inspection_date', ascending=False)
                for _, restaurant in restaurants_df.iterrows():
                    display_restaurant_card(restaurant)
                    
            except Exception as e:
                st.error(f"Error loading restaurant data: {str(e)}")
                st.info("Please check your internet connection and try again.")

def display_restaurant_card(restaurant):
    """Display restaurant card with consolidated styling"""
    
    with st.expander(f"{restaurant['name']}", expanded=True):
        st.markdown('<div class="info-section">', unsafe_allow_html=True)
        st.markdown('<h4 class="section-header">Location Details</h4>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f'<div class="detail-text"><strong>Address:</strong> {restaurant.get("address", "N/A")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="detail-text"><strong>Cuisine:</strong> {restaurant.get("cuisine_type", "Not specified")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="detail-text"><strong>Location:</strong> {restaurant.get("boro", "N/A")}</div>', unsafe_allow_html=True)
            
            # Inspection date prominently displayed
            inspection_date = restaurant.get("inspection_date", "Date not available")
            if inspection_date and inspection_date != "Date not available":
                from utils import format_inspection_date
                formatted_date = format_inspection_date(inspection_date)
                st.markdown(f'<div class="detail-text" style="font-weight: 600; color: #fbbf24; margin-top: 8px;"><strong>Last Inspected:</strong> {formatted_date}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="detail-text" style="color: #9ca3af; margin-top: 8px;"><strong>Last Inspected:</strong> {inspection_date}</div>', unsafe_allow_html=True)
        
        with col2:
            grade = restaurant.get('grade', 'Not Yet Graded')
            grade_info = st.session_state.api_client.get_grade_info(grade)
            
            st.markdown(f"""
            <div style="background-color: {grade_info['color']}20; border: 2px solid {grade_info['color']}; 
                        border-radius: 8px; padding: 16px; text-align: center;">
                <div style="font-size: 1.5rem; font-weight: 700; color: {grade_info['color']};">
                    {grade_info['label']}
                </div>
                <div style="font-size: 0.9rem; color: #a0aec0; margin-top: 4px;">
                    {grade_info['description']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Violations section
        st.markdown('<h4 class="section-header">Health Inspection Results</h4>', unsafe_allow_html=True)
        
        if 'violations' in restaurant and restaurant['violations']:
            violations = [v for v in restaurant['violations'] if v != "No violations recorded"]
            if violations:
                for i, violation in enumerate(violations[:3]):
                    st.markdown(f'<div class="detail-text">• {violation}</div>', unsafe_allow_html=True)
                
                if len(violations) > 3:
                    with st.expander(f"View {len(violations) - 3} more violations"):
                        for violation in violations[3:]:
                            st.markdown(f'<div class="detail-text">• {violation}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="detail-text" style="color: #68d391;">✓ No violations recorded</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="detail-text" style="color: #68d391;">✓ No violations recorded</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()