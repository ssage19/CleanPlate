import streamlit as st
from datetime import datetime

def format_grade_badge(grade):
    """Format health grade as colored badge"""
    
    grade_colors = {
        'A': {'bg': '#27AE60', 'text': 'white'},  # Success green
        'B': {'bg': '#F39C12', 'text': 'white'},  # Warning orange
        'C': {'bg': '#E74C3C', 'text': 'white'},  # Danger red
        'Grade Pending': {'bg': '#95A5A6', 'text': 'white'},  # Gray
        'Not Yet Graded': {'bg': '#BDC3C7', 'text': 'black'}   # Light gray
    }
    
    color_info = grade_colors.get(grade, {'bg': '#BDC3C7', 'text': 'black'})
    
    badge_html = f"""
    <div style="
        background-color: {color_info['bg']};
        color: {color_info['text']};
        padding: 8px 16px;
        border-radius: 20px;
        text-align: center;
        font-weight: bold;
        font-size: 18px;
        margin: 5px 0;
        display: inline-block;
        min-width: 60px;
    ">
        {grade}
    </div>
    """
    
    return badge_html

def calculate_average_rating(restaurant_id):
    """Calculate average user rating for a restaurant"""
    if restaurant_id not in st.session_state.user_reviews:
        return 0
    
    reviews = st.session_state.user_reviews[restaurant_id]
    if not reviews:
        return 0
    
    total_rating = sum(review['rating'] for review in reviews)
    return total_rating / len(reviews)

def get_cuisine_types():
    """Get list of common cuisine types for filtering"""
    
    # Common cuisine types found in NYC restaurant data
    cuisine_types = [
        'American', 'Chinese', 'Italian', 'Mexican', 'Japanese', 'Thai', 'Indian',
        'French', 'Mediterranean', 'Korean', 'Vietnamese', 'Greek', 'Spanish',
        'Turkish', 'Caribbean', 'Ethiopian', 'Moroccan', 'Lebanese', 'German',
        'Russian', 'Polish', 'Jewish/Kosher', 'Pizza', 'Hamburgers', 'Sandwiches',
        'Bakery', 'Delicatessen', 'Seafood', 'Steakhouse', 'Vegetarian',
        'Latin (Cuban, Dominican, Puerto Rican, South & Central American)',
        'African', 'Middle Eastern', 'Pakistani', 'Bangladeshi', 'Filipino',
        'Peruvian', 'Brazilian', 'Tex-Mex', 'Barbecue', 'Soul Food',
        'Cajun', 'Continental', 'Fusion', 'Tapas', 'Sushi', 'Ramen',
        'Dim Sum', 'Hot Dogs/Pretzels', 'Ice Cream, Gelato, Yogurt, Ices',
        'Donuts', 'Bagels/Pretzels', 'Juice, Smoothies, Fruit Salads',
        'Coffee/Tea', 'Not Listed/Not Applicable'
    ]
    
    return sorted(cuisine_types)

def validate_date_range(date_range):
    """Validate and format date range for API queries"""
    if not date_range or len(date_range) != 2:
        return None
    
    start_date, end_date = date_range
    
    # Ensure end date is not in the future
    if end_date > datetime.now().date():
        end_date = datetime.now().date()
    
    # Ensure start date is not after end date
    if start_date > end_date:
        start_date = end_date
    
    return (start_date, end_date)

def format_inspection_date(date_str):
    """Format inspection date for display"""
    try:
        if date_str and date_str != 'N/A':
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime('%B %d, %Y')
        return 'Date not available'
    except ValueError:
        return date_str

def get_grade_description(grade):
    """Get description for health grade"""
    descriptions = {
        'A': 'Excellent - Score of 0-13 points',
        'B': 'Good - Score of 14-27 points', 
        'C': 'Fair - Score of 28+ points',
        'Grade Pending': 'Inspection completed, grade pending',
        'Not Yet Graded': 'Not yet inspected or graded'
    }
    
    return descriptions.get(grade, 'Grade information not available')

def filter_dataframe_by_search(df, search_term, columns=['name', 'address', 'cuisine_type']):
    """Filter dataframe by search term across multiple columns"""
    if not search_term:
        return df
    
    search_term = search_term.lower()
    mask = df[columns].astype(str).apply(
        lambda x: x.str.lower().str.contains(search_term, na=False)
    ).any(axis=1)
    
    return df[mask]

def export_restaurant_data(df, filename="restaurant_inspections.csv"):
    """Export restaurant data to CSV"""
    try:
        csv_data = df.to_csv(index=False)
        return csv_data
    except Exception as e:
        st.error(f"Error exporting data: {str(e)}")
        return None
