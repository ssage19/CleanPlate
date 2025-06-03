import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

# Initialize database
init_database()

def main():
    # Apply CSS styling
    st.markdown("""
    <style>
        .main-header {
            text-align: center;
            padding: 2rem 0;
            background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            margin: -1rem -1rem 2rem -1rem;
            border-radius: 0 0 20px 20px;
        }
        .main-header h1 {
            color: #f7fafc;
            font-size: 3rem;
            margin-bottom: 0.5rem;
            font-weight: 700;
        }
        .main-header p {
            color: #a0aec0;
            font-size: 1.2rem;
            margin: 0;
            max-width: 800px;
            margin: 0 auto;
            line-height: 1.5;
        }
        .info-section {
            background-color: #2d3748;
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
            border-left: 4px solid #d4af37;
        }
        .section-header {
            color: #f7fafc;
            font-size: 1.3rem;
            margin-bottom: 1rem;
            font-weight: 600;
        }
        .detail-text {
            color: #e2e8f0;
            margin: 0.5rem 0;
            line-height: 1.6;
        }
        .divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, #4a5568, transparent);
            margin: 1.5rem 0;
        }
        [data-testid="stAppViewContainer"] {
            padding-top: 0rem !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header with icon
    st.markdown("""
    <div class="main-header">
        <h1>
            <span style="font-size: 72px; vertical-align: middle; margin-right: 16px;">🍽️</span>
            CleanPlate
        </h1>
        <p>Peeking behind the kitchen door, so you can dine without doubt. We dish out health inspection scores, making informed choices deliciously easy.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Restaurant Search", "📊 City Analytics", "📅 Inspection Trends"])
    
    with tab1:
        show_restaurant_search()
    
    with tab2:
        show_city_analytics()
    
    with tab3:
        show_inspection_trends()

def show_restaurant_search():
    """Show the main restaurant search interface"""
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

def show_city_analytics():
    """Show city health performance analytics"""
    st.markdown("## 🏙️ City Health Performance Dashboard")
    st.markdown("Compare health inspection performance across all 6 major cities")
    
    if st.button("Load City Comparison Data", key="load_city_data"):
        with st.spinner("Loading data from all cities..."):
            city_data = {}
            jurisdictions = ["NYC", "Chicago", "Boston", "Austin", "Seattle", "Los Angeles"]
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, jurisdiction in enumerate(jurisdictions):
                status_text.text(f"Loading {jurisdiction} data...")
                progress_bar.progress((i + 1) / len(jurisdictions))
                
                try:
                    st.session_state.api_client.set_jurisdiction(jurisdiction)
                    restaurants_df = st.session_state.api_client.get_restaurants(limit=300)
                    
                    if not restaurants_df.empty:
                        city_data[jurisdiction] = restaurants_df
                        
                except Exception as e:
                    st.warning(f"Could not load data for {jurisdiction}: {str(e)}")
                    
            status_text.empty()
            progress_bar.empty()
            
            if city_data:
                create_city_comparison_charts(city_data)
                create_grade_distribution_charts(city_data)
            else:
                st.error("No data available for visualization")

def show_inspection_trends():
    """Show inspection frequency and trends analysis"""
    st.markdown("## 📅 Inspection Frequency Analysis")
    
    jurisdictions = ["NYC", "Chicago", "Boston", "Austin", "Seattle", "Los Angeles"]
    selected_city = st.selectbox("Select city for detailed inspection analysis:", jurisdictions)
    
    if st.button("Analyze Inspection Patterns"):
        with st.spinner("Analyzing inspection frequency patterns..."):
            try:
                st.session_state.api_client.set_jurisdiction(selected_city)
                restaurants_df = st.session_state.api_client.get_restaurants(limit=500)
                
                if not restaurants_df.empty and 'inspection_date' in restaurants_df.columns:
                    # Parse inspection dates
                    restaurants_df['inspection_date_parsed'] = pd.to_datetime(
                        restaurants_df['inspection_date'], errors='coerce'
                    )
                    
                    # Remove rows with invalid dates
                    valid_dates_df = restaurants_df.dropna(subset=['inspection_date_parsed'])
                    
                    if not valid_dates_df.empty:
                        create_inspection_timeline(valid_dates_df, selected_city)
                        create_monthly_patterns(valid_dates_df, selected_city)
                    else:
                        st.warning(f"No valid inspection dates found for {selected_city}")
                else:
                    st.warning(f"No inspection data available for {selected_city}")
                    
            except Exception as e:
                st.error(f"Error analyzing inspection patterns: {str(e)}")

def create_city_comparison_charts(city_data):
    """Create city comparison metrics and charts"""
    st.markdown("### 📊 City Performance Metrics")
    
    metrics_data = []
    
    for city, df in city_data.items():
        if df.empty:
            continue
            
        total_restaurants = len(df)
        
        # Get grading system info for this city
        st.session_state.api_client.set_jurisdiction(city)
        grading_info = st.session_state.api_client.get_grading_system_info()
        
        # Calculate grade distribution based on city's grading system
        if grading_info.get('type') == 'letter':
            excellent_count = len(df[df['grade'] == 'A'])
            good_count = len(df[df['grade'] == 'B'])
            poor_count = len(df[df['grade'].isin(['C', 'F'])])
        elif grading_info.get('type') == 'pass_fail':
            excellent_count = len(df[df['grade'] == 'Pass'])
            good_count = 0
            poor_count = len(df[df['grade'].isin(['Fail', 'Conditional'])])
        else:
            # For numeric systems, use simple categorization
            excellent_count = len(df) // 3  # Approximate
            good_count = len(df) // 3
            poor_count = len(df) - excellent_count - good_count
        
        excellent_pct = (excellent_count / total_restaurants * 100) if total_restaurants > 0 else 0
        good_pct = (good_count / total_restaurants * 100) if total_restaurants > 0 else 0
        poor_pct = (poor_count / total_restaurants * 100) if total_restaurants > 0 else 0
        
        metrics_data.append({
            'City': city,
            'Total Restaurants': total_restaurants,
            'Excellent Performance (%)': round(excellent_pct, 1),
            'Good Performance (%)': round(good_pct, 1),
            'Poor Performance (%)': round(poor_pct, 1),
            'Grading System': grading_info.get('type', 'Unknown')
        })
    
    if metrics_data:
        metrics_df = pd.DataFrame(metrics_data)
        
        # Display metrics table
        st.dataframe(metrics_df, use_container_width=True)
        
        # Create bar chart comparison
        fig = px.bar(
            metrics_df, 
            x='City', 
            y=['Excellent Performance (%)', 'Good Performance (%)', 'Poor Performance (%)'],
            title="Health Performance Comparison Across Cities",
            color_discrete_map={
                'Excellent Performance (%)': '#22c55e',
                'Good Performance (%)': '#f59e0b', 
                'Poor Performance (%)': '#ef4444'
            },
            height=500
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        st.plotly_chart(fig, use_container_width=True)

def create_grade_distribution_charts(city_data):
    """Create grade distribution pie charts for each city"""
    st.markdown("### 🎯 Grade Distribution by City")
    
    cols = st.columns(2)
    col_idx = 0
    
    for city, df in city_data.items():
        if df.empty:
            continue
            
        # Get grade distribution
        grade_counts = df['grade'].value_counts()
        
        if len(grade_counts) > 0:
            with cols[col_idx % 2]:
                fig = px.pie(
                    values=grade_counts.values,
                    names=grade_counts.index,
                    title=f"{city} Grade Distribution",
                    color_discrete_map={
                        'A': '#22c55e', 'Pass': '#22c55e', 'Excellent': '#22c55e',
                        'B': '#f59e0b', 'Good': '#f59e0b',
                        'C': '#ef4444', 'Fail': '#ef4444', 'Poor': '#ef4444',
                        'Conditional': '#f97316'
                    }
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig, use_container_width=True)
                
            col_idx += 1

def create_inspection_timeline(df, city):
    """Create inspection timeline visualization"""
    st.markdown(f"### 📈 {city} Inspection Timeline")
    
    # Group by month
    df['year_month'] = df['inspection_date_parsed'].dt.to_period('M')
    monthly_counts = df.groupby('year_month').size()
    
    # Convert period index to string for plotting
    monthly_counts.index = monthly_counts.index.astype(str)
    
    fig = px.line(
        x=monthly_counts.index,
        y=monthly_counts.values,
        title=f"Monthly Inspection Trends - {city}",
        labels={'x': 'Month', 'y': 'Number of Inspections'}
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white'
    )
    st.plotly_chart(fig, use_container_width=True)

def create_monthly_patterns(df, city):
    """Create monthly inspection pattern analysis"""
    st.markdown(f"### 📊 {city} Seasonal Inspection Patterns")
    
    # Extract month names
    df['month_name'] = df['inspection_date_parsed'].dt.month_name()
    monthly_pattern = df['month_name'].value_counts().reindex([
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ], fill_value=0)
    
    fig = px.bar(
        x=monthly_pattern.index,
        y=monthly_pattern.values,
        title=f"Inspections by Month - {city}",
        labels={'x': 'Month', 'y': 'Number of Inspections'}
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white'
    )
    st.plotly_chart(fig, use_container_width=True)

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