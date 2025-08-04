import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from data_fetcher import HealthInspectionAPI
from database import init_database, save_restaurant_to_db
from utils import format_grade_badge, calculate_average_rating
from ads import ad_manager
from delivery_affiliates import delivery_affiliate_manager

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

# Initialize logo
if 'logo_base64' not in st.session_state:
    import base64
    try:
        with open('attached_assets/Clean Plate_1754314259976.png', 'rb') as f:
            logo_data = f.read()
            st.session_state.logo_base64 = base64.b64encode(logo_data).decode()
    except FileNotFoundError:
        # Fallback to emoji if logo file not found
        st.session_state.logo_base64 = ""

# Initialize database on startup
init_database()

def main():
    
    # Add PWA meta tags and Google AdSense
    st.markdown("""
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="apple-mobile-web-app-title" content="CleanPlate">
        <meta name="theme-color" content="#d4af37">
        <link rel="manifest" href="/static/manifest.json">
        <link rel="icon" type="image/png" sizes="192x192" href="/static/icon-192.png">
        <link rel="apple-touch-icon" href="/static/icon-192.png">
        
        <!-- Google AdSense Meta Tag for Account Verification -->
        <meta name="google-adsense-account" content="ca-pub-8384381342878857">
    </head>
    
    <script>
        // Register service worker for PWA functionality
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', function() {
                navigator.serviceWorker.register('/static/service-worker.js')
                .then(function(registration) {
                    console.log('ServiceWorker registration successful');
                }, function(err) {
                    console.log('ServiceWorker registration failed: ', err);
                });
            });
        }
        
        // Add install prompt for PWA
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            
            // Show custom install button
            const installButton = document.createElement('button');
            installButton.textContent = '📱 Install CleanPlate App';
            installButton.style.cssText = `
                position: fixed; 
                bottom: 20px; 
                right: 20px; 
                background: #d4af37; 
                color: #1a202c; 
                border: none; 
                padding: 12px 20px; 
                border-radius: 25px; 
                font-weight: bold; 
                cursor: pointer; 
                z-index: 1000;
                box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
            `;
            
            installButton.addEventListener('click', () => {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then((choiceResult) => {
                    if (choiceResult.outcome === 'accepted') {
                        console.log('User accepted the install prompt');
                        installButton.remove();
                    }
                    deferredPrompt = null;
                });
            });
            
            document.body.appendChild(installButton);
        });
    </script>
    """, unsafe_allow_html=True)
    
    # RESPONSIVE DESIGN - Optimized for all devices
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;500;600;700&display=swap');
        
        /* Main App Background - Responsive Restaurant Atmosphere */
        .stApp {
            background: 
                radial-gradient(ellipse at top left, rgba(212, 175, 55, 0.05) 0%, transparent 50%),
                radial-gradient(ellipse at bottom right, rgba(212, 175, 55, 0.03) 0%, transparent 40%),
                linear-gradient(135deg, #0a0e13 0%, #1a1f2e 25%, #2d3748 50%, #1a1f2e 75%, #0a0e13 100%) !important;
            color: #f7fafc !important;
            font-family: 'Inter', sans-serif !important;
            min-height: 100vh !important;
            width: 100% !important;
            overflow-x: hidden !important;
        }
        
        /* Responsive Container */
        .main .block-container {
            padding: 1rem !important;
            max-width: none !important;
            width: 100% !important;
        }
        
        /* Mobile-First Responsive Breakpoints */
        @media (max-width: 640px) {
            .stApp {
                font-size: 14px !important;
            }
            
            .main .block-container {
                padding: 0.5rem !important;
            }
            
            /* Mobile Header */
            .main-header {
                padding: 2rem 1rem !important;
                margin: -0.5rem -0.5rem 1.5rem -0.5rem !important;
            }
            
            .main-header h1 {
                font-size: 2rem !important;
                line-height: 1.2 !important;
            }
            
            .main-header span {
                font-size: 2.5rem !important;
                margin-right: 8px !important;
            }
            
            .main-header p {
                font-size: 0.9rem !important;
                line-height: 1.4 !important;
            }
        }
        
        @media (min-width: 641px) and (max-width: 768px) {
            /* Tablet Styles */
            .main-header {
                padding: 3rem 1.5rem !important;
            }
            
            .main-header h1 {
                font-size: 2.5rem !important;
            }
        }
        
        @media (min-width: 769px) {
            /* Desktop Styles */
            .main .block-container {
                max-width: 1200px !important;
                margin: 0 auto !important;
            }
        }
        
        /* Responsive Header */
        .main-header {
            background: linear-gradient(135deg, rgba(20, 25, 35, 0.95) 0%, rgba(45, 55, 72, 0.9) 100%);
            padding: 3rem 2rem;
            margin: -1rem -1rem 2rem -1rem;
            border-bottom: 2px solid rgba(212, 175, 55, 0.3);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
            text-align: center;
            width: 100%;
            box-sizing: border-box;
        }
        
        .main-header h1 {
            color: #ffffff;
            font-size: clamp(2rem, 5vw, 4rem);
            font-weight: 600;
            margin: 0;
            font-family: 'Playfair Display', serif;
            text-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
            line-height: 1.2;
            word-wrap: break-word;
        }
        
        .main-header p {
            color: rgba(212, 175, 55, 0.9);
            font-size: clamp(0.8rem, 2vw, 0.95rem);
            margin: 1rem 0 0 0;
            font-weight: 500;
            letter-spacing: 0.1em;
            font-family: 'Inter', sans-serif;
            text-transform: uppercase;
            line-height: 1.4;
        }
        
        /* Responsive Form Controls */
        .stSelectbox > div > div {
            background: rgba(45, 55, 72, 0.9) !important;
            border: 1px solid rgba(212, 175, 55, 0.4) !important;
            border-radius: 8px !important;
            color: #f7fafc !important;
            width: 100% !important;
            box-sizing: border-box !important;
        }
        
        .stTextInput > div > div > input {
            background: rgba(45, 55, 72, 0.9) !important;
            border: 1px solid rgba(212, 175, 55, 0.4) !important;
            border-radius: 8px !important;
            color: #f7fafc !important;
            padding: 12px 16px !important;
            width: 100% !important;
            box-sizing: border-box !important;
        }
        
        /* Mobile Form Adjustments */
        @media (max-width: 640px) {
            .stSelectbox > div > div {
                font-size: 14px !important;
            }
            
            .stTextInput > div > div > input {
                padding: 10px 12px !important;
                font-size: 14px !important;
            }
            
            .stButton > button {
                width: 100% !important;
                padding: 10px 16px !important;
                font-size: 14px !important;
            }
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
        
        /* Responsive Restaurant Cards */
        .stExpander {
            background: rgba(45, 55, 72, 0.9) !important;
            border: 1px solid rgba(212, 175, 55, 0.3) !important;
            border-radius: 12px !important;
            margin: 1rem 0 !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3) !important;
            width: 100% !important;
            box-sizing: border-box !important;
        }
        
        /* Mobile Restaurant Card Adjustments */
        @media (max-width: 640px) {
            .stExpander {
                margin: 0.5rem 0 !important;
                border-radius: 8px !important;
            }
            
            .stExpander > div:first-child {
                font-size: 1rem !important;
                padding: 12px !important;
            }
        }
        
        .stExpander > div:first-child {
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%) !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            font-family: 'Playfair Display', serif !important;
            border-bottom: 1px solid rgba(212, 175, 55, 0.3) !important;
        }
        
        /* Responsive Info Sections */
        .info-section {
            background: rgba(45, 55, 72, 0.8);
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            border: 1px solid rgba(212, 175, 55, 0.2);
            width: 100%;
            box-sizing: border-box;
        }
        
        @media (max-width: 640px) {
            .info-section {
                padding: 0.75rem;
                margin: 0.5rem 0;
                border-radius: 6px;
            }
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
        
        /* Responsive Layout Adjustments */
        [data-testid="stAppViewContainer"] {
            padding-top: 0rem !important;
            width: 100% !important;
        }
        
        /* Column Responsiveness */
        [data-testid="column"] {
            width: 100% !important;
            padding: 0 0.25rem !important;
        }
        
        @media (max-width: 640px) {
            [data-testid="column"] {
                min-width: 100% !important;
                padding: 0.25rem 0 !important;
            }
            
            /* Stack columns on mobile */
            .row-widget {
                flex-direction: column !important;
            }
        }
        
        /* Touch-friendly elements */
        @media (max-width: 768px) {
            .stButton > button, .stSelectbox, .stTextInput {
                min-height: 44px !important; /* iOS recommended touch target */
            }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Temporarily disabled advertisement display to fix core functionality
    # ad_manager.display_banner_ad("header")
    
    # Header with custom logo
    logo_base64 = st.session_state.get('logo_base64', '')
    if logo_base64:
        logo_html = f'<img src="data:image/png;base64,{logo_base64}" style="width: 90px; height: 90px; vertical-align: middle; margin-right: 16px; border-radius: 50%;" alt="CleanPlate Logo" />'
    else:
        logo_html = '<span style="font-size: 90px; vertical-align: middle; margin-right: 16px;">🍽️</span>'
    
    st.markdown(f"""
    <div class="main-header">
        <h1>
            {logo_html}
            CleanPlate
        </h1>
        <p>Peeking behind the kitchen door, so you can dine without doubt. We dish out health inspection scores, making informed choices deliciously easy.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display header ad for revenue generation
    ad_manager.display_banner_ad("header")
    
    # Revenue Setup Menu (Admin Access)
    if st.sidebar.button("💰 Revenue Setup Guide"):
        st.session_state.show_revenue_guide = True
    
    if st.sidebar.button("🚗 Delivery Affiliates Setup"):
        st.session_state.show_delivery_guide = True
    
    if st.session_state.get('show_revenue_guide', False):
        from revenue_dashboard import display_revenue_setup_guide
        display_revenue_setup_guide()
        if st.button("← Back to App"):
            st.session_state.show_revenue_guide = False
            st.rerun()
        return
    
    if st.session_state.get('show_delivery_guide', False):
        delivery_affiliate_manager.display_affiliate_setup_guide()
        if st.button("← Back to App"):
            st.session_state.show_delivery_guide = False
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
    
    # Advanced Search Section
    with st.expander("🔍 Advanced Search Options", expanded=False):
        st.markdown("**Refine your search with these advanced filters:**")
        
        col_search_mode, col_grade_filter = st.columns(2)
        
        with col_search_mode:
            search_mode = st.radio(
                "Search Mode",
                ["Contains (partial match)", "Exact words", "Starts with"],
                help="Choose how to match your search terms"
            )
        
        with col_grade_filter:
            grading_info = st.session_state.api_client.get_grading_system_info()
            if grading_info.get('grades'):
                grade_options = ["All Grades"] + list(grading_info['grades'].keys())
                grade_filter = st.selectbox(
                    "Grade Filter",
                    grade_options,
                    help="Filter by health inspection grade"
                )
                grade_filter = None if grade_filter == "All Grades" else [grade_filter]
            else:
                grade_filter = None
        
        # Cuisine filter
        cuisine_filter = st.multiselect(
            "Cuisine Types",
            ["Italian", "Chinese", "Mexican", "American", "Japanese", "Thai", "Indian", "Mediterranean", "French", "Korean"],
            help="Filter by cuisine type (optional)"
        )
        cuisine_filter = None if not cuisine_filter else cuisine_filter

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
                "Borough/Area",
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
                # Apply advanced search filtering
                processed_search_term = search_term
                if search_term and search_mode:
                    if search_mode == "Exact words":
                        # For exact word matching, wrap in quotes or use exact match logic
                        processed_search_term = f'"{search_term}"' if search_term else search_term
                    elif search_mode == "Starts with":
                        # Add prefix matching indicator
                        processed_search_term = f"{search_term}*" if search_term else search_term
                
                restaurants_df = st.session_state.api_client.get_restaurants(
                    location=location_filter,
                    search_term=processed_search_term,
                    grades=grade_filter,
                    cuisines=cuisine_filter,
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
                

                
                # Temporarily disabled sponsored restaurant display to fix HTML rendering issue
                # ad_manager.display_sponsored_restaurant()
                
                # Deduplicate restaurants to show only the most recent inspection per establishment
                latest_inspections = {}
                for _, restaurant in restaurants_df.iterrows():
                    name = restaurant.get('name', 'Unknown')
                    address = restaurant.get('address', '')
                    restaurant_key = f"{name}|{address}".lower()
                    
                    # Keep only the most recent inspection for each restaurant
                    if restaurant_key not in latest_inspections:
                        latest_inspections[restaurant_key] = restaurant
                    else:
                        # Compare dates and keep the more recent one
                        current_date = latest_inspections[restaurant_key].get('inspection_date', '')
                        new_date = restaurant.get('inspection_date', '')
                        if new_date > current_date:
                            latest_inspections[restaurant_key] = restaurant
                
                # Convert back to DataFrame for display
                unique_restaurants = list(latest_inspections.values())
                
                st.subheader(f"Showing {len(unique_restaurants)} unique restaurants (most recent inspection only)")
                
                # Display unique restaurants
                for restaurant in sorted(unique_restaurants, key=lambda x: x.get('inspection_date', ''), reverse=True):
                    display_restaurant_card(restaurant)
                    
            except Exception as e:
                st.error(f"Error loading restaurant data: {str(e)}")
                st.info("Please check your internet connection and try again.")

def display_restaurant_card(restaurant):
    """Display restaurant card with sophisticated multi-inspection timeline"""
    
    # Handle both old and new data formats
    inspections = restaurant.get('inspections', [])
    if not inspections:
        # Create single inspection from main restaurant data for backwards compatibility
        inspections = [{
            'grade': restaurant.get('grade', 'Not Yet Graded'),
            'score': restaurant.get('score'),
            'inspection_date': restaurant.get('inspection_date', 'N/A'),
            'violations': restaurant.get('violations', []),
            'inspection_type': restaurant.get('inspection_type', ''),
            'critical_flag': restaurant.get('critical_flag', '')
        }]
    
    # Latest inspection for main display
    latest_inspection = inspections[0] if inspections else {}
    
    # Create more prominent restaurant header
    restaurant_name = restaurant['name']
    grade = restaurant.get('grade', 'Not Yet Graded')
    grade_info = st.session_state.api_client.get_grade_info(grade)
    
    # Create prominent restaurant header using native Streamlit components
    st.markdown(f"# {restaurant_name}")
    
    # Display grade in a clean way
    grade_label = grade_info['label']
    grade_desc = grade_info['description']
    
    col_grade, col_spacer = st.columns([1, 2])
    with col_grade:
        if grade_label == 'A':
            st.success(f"Grade: {grade_label} - {grade_desc}")
        elif grade_label == 'B':
            st.warning(f"Grade: {grade_label} - {grade_desc}")
        elif grade_label == 'C':
            st.error(f"Grade: {grade_label} - {grade_desc}")
        else:
            st.info(f"Grade: {grade_label} - {grade_desc}")

    with st.expander("📋 Restaurant Details & Order Food", expanded=True):
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("📍 Restaurant Information")
            st.write(f"**Address:** {restaurant.get('address', 'N/A')}")
            st.write(f"**Cuisine:** {restaurant.get('cuisine_type', 'Not specified')}")
            st.write(f"**Location:** {restaurant.get('boro', 'N/A')}")
        
        with col2:
            # Add delivery affiliate buttons for revenue generation
            delivery_affiliate_manager.display_delivery_buttons(
                restaurant_name=restaurant['name'],
                restaurant_address=restaurant.get('address', '')
            )
        
        # Inspection History Timeline - Using native Streamlit components
        if len(inspections) > 1:
            st.subheader("📋 Inspection History Timeline")
            
            for i, inspection in enumerate(inspections[:5]):  # Show up to 5 most recent
                inspection_date = inspection.get("inspection_date", "Date not available")
                if inspection_date and inspection_date != "Date not available":
                    from utils import format_inspection_date
                    formatted_date = format_inspection_date(inspection_date)
                else:
                    formatted_date = inspection_date
                
                grade = inspection.get('grade', 'Not Graded')
                grade_info = st.session_state.api_client.get_grade_info(grade)
                score = inspection.get('score')
                inspection_type = inspection.get('inspection_type', 'Regular Inspection')
                
                # Use native Streamlit components instead of raw HTML
                timeline_icon = "🔸" if i == 0 else "🔹"
                
                # Create timeline entry using columns
                col_icon, col_content = st.columns([0.1, 0.9])
                
                with col_icon:
                    st.write(timeline_icon)
                
                with col_content:
                    # Date and grade in same row
                    date_col, grade_col = st.columns([0.7, 0.3])
                    
                    with date_col:
                        st.write(f"**{formatted_date}**")
                        st.caption(f"Type: {inspection_type}" + (f" | Score: {score}" if score else ""))
                    
                    with grade_col:
                        # Display grade badge using native Streamlit
                        st.markdown(f"""
                        <div style="background: {grade_info['color']}20; border: 1px solid {grade_info['color']}; 
                                   border-radius: 5px; padding: 5px 10px; text-align: center;">
                            <span style="color: {grade_info['color']}; font-weight: bold; font-size: 0.9rem;">
                                {grade_info['label']}
                            </span>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Add separator between entries
                if i < min(len(inspections) - 1, 4):
                    st.markdown("---")
            
            if len(inspections) > 5:
                st.caption(f"... and {len(inspections) - 5} more inspections")
        
        # Latest Inspection Details
        latest_date = latest_inspection.get("inspection_date", "Date not available")
        if latest_date and latest_date != "Date not available":
            from utils import format_inspection_date
            formatted_latest_date = format_inspection_date(latest_date)
            st.subheader(f"🔍 Latest Inspection - {formatted_latest_date}")
        else:
            st.subheader("🔍 Latest Inspection Results")
        
        if 'violations' in latest_inspection and latest_inspection['violations']:
            violations = [v for v in latest_inspection['violations'] if v != "No violations recorded"]
            if violations:
                for i, violation in enumerate(violations[:3]):
                    st.write(f"• {violation}")
                
                if len(violations) > 3:
                    with st.expander(f"View {len(violations) - 3} more violations from latest inspection"):
                        for violation in violations[3:]:
                            st.write(f"• {violation}")
            else:
                st.success("✓ No violations recorded")
        else:
            st.success("✓ No violations recorded")

if __name__ == "__main__":
    main()