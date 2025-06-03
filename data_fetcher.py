import pandas as pd
import requests
import os
from datetime import datetime, timedelta
import json

class HealthInspectionAPI:
    """
    Client for fetching restaurant health inspection data from government sources
    """
    
    def __init__(self):
        # NYC Open Data API endpoint for restaurant inspections
        self.nyc_api_base = "https://data.cityofnewyork.us/resource/43nn-pn8j.json"
        self.api_key = os.getenv("NYC_OPEN_DATA_API_KEY", None)
        
        # Cache for API responses
        self._location_cache = None
        self._data_cache = {}
        self._cache_timestamp = None
        self._cache_duration = 3600  # 1 hour cache
    
    def _make_api_request(self, endpoint, params=None):
        """Make API request with error handling"""
        try:
            headers = {}
            if self.api_key:
                headers['X-App-Token'] = self.api_key
            
            response = requests.get(endpoint, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid API response format: {str(e)}")
    
    def _is_cache_valid(self):
        """Check if cache is still valid"""
        if self._cache_timestamp is None:
            return False
        return (datetime.now() - self._cache_timestamp).seconds < self._cache_duration
    
    def get_available_locations(self):
        """Get list of available locations/boroughs"""
        if self._location_cache and self._is_cache_valid():
            return self._location_cache
        
        try:
            # Get distinct boroughs from NYC data
            params = {
                '$select': 'DISTINCT boro',
                '$limit': 10
            }
            
            data = self._make_api_request(self.nyc_api_base, params)
            locations = [item['boro'] for item in data if item.get('boro')]
            
            # Add common NYC boroughs if not in data
            standard_boroughs = ['MANHATTAN', 'BROOKLYN', 'QUEENS', 'BRONX', 'STATEN ISLAND']
            for borough in standard_boroughs:
                if borough not in locations:
                    locations.append(borough)
            
            self._location_cache = sorted(locations)
            return self._location_cache
            
        except Exception as e:
            # Return default NYC boroughs if API fails
            return ['MANHATTAN', 'BROOKLYN', 'QUEENS', 'BRONX', 'STATEN ISLAND']
    
    def get_restaurants(self, location=None, grades=None, cuisines=None, search_term=None, date_range=None, limit=100):
        """
        Fetch restaurant inspection data with filters
        """
        try:
            # Build API query parameters
            params = {
                '$limit': limit,
                '$order': 'inspection_date DESC'
            }
            
            # Build where clause
            where_conditions = []
            
            if location and location != "All":
                where_conditions.append(f"boro='{location.upper()}'")
            
            if grades:
                grade_conditions = [f"grade='{grade}'" for grade in grades]
                where_conditions.append(f"({' OR '.join(grade_conditions)})")
            
            if search_term:
                where_conditions.append(f"UPPER(dba) LIKE '%{search_term.upper()}%'")
            
            if date_range and len(date_range) == 2:
                start_date = date_range[0].strftime('%Y-%m-%d')
                end_date = date_range[1].strftime('%Y-%m-%d')
                where_conditions.append(f"inspection_date >= '{start_date}' AND inspection_date <= '{end_date}'")
            
            if where_conditions:
                params['$where'] = ' AND '.join(where_conditions)
            
            # Make API request
            data = self._make_api_request(self.nyc_api_base, params)
            
            if not data:
                return pd.DataFrame()
            
            # Process and clean data
            restaurants = []
            seen_restaurants = set()
            
            for item in data:
                # Create unique identifier for restaurant
                restaurant_key = (item.get('dba', '').strip(), item.get('building', ''), item.get('street', ''))
                
                if restaurant_key in seen_restaurants:
                    continue
                seen_restaurants.add(restaurant_key)
                
                # Extract and clean restaurant data
                restaurant = {
                    'id': f"{item.get('camis', '')}{item.get('dba', '').replace(' ', '')}",
                    'name': item.get('dba', 'Unknown Restaurant').strip(),
                    'address': self._format_address(item),
                    'cuisine_type': item.get('cuisine_description', 'Not specified'),
                    'grade': item.get('grade', 'Not Yet Graded'),
                    'score': self._safe_int(item.get('score')),
                    'inspection_date': item.get('inspection_date', '').split('T')[0] if item.get('inspection_date') else 'N/A',
                    'violations': self._extract_violations(item),
                    'boro': item.get('boro', ''),
                    'phone': item.get('phone', ''),
                    'inspection_type': item.get('inspection_type', '')
                }
                
                restaurants.append(restaurant)
            
            df = pd.DataFrame(restaurants)
            
            # Apply cuisine filter if specified
            if cuisines and "All" not in cuisines:
                df = df[df['cuisine_type'].isin(cuisines)]
            
            return df.head(limit)
            
        except Exception as e:
            raise Exception(f"Failed to fetch restaurant data: {str(e)}")
    
    def _format_address(self, item):
        """Format restaurant address from API data"""
        building = item.get('building', '')
        street = item.get('street', '')
        boro = item.get('boro', '')
        zipcode = item.get('zipcode', '')
        
        address_parts = [part for part in [building, street, boro, zipcode] if part]
        return ', '.join(address_parts) if address_parts else 'Address not available'
    
    def _safe_int(self, value):
        """Safely convert value to integer"""
        try:
            return int(float(value)) if value and str(value).strip() else None
        except (ValueError, TypeError):
            return None
    
    def _extract_violations(self, item):
        """Extract violation information from API response"""
        violations = []
        
        # Check for violation description
        if item.get('violation_description'):
            violations.append(item['violation_description'])
        
        # Check for critical flag
        if item.get('critical_flag') == 'Y':
            violations.append("Critical violation found")
        
        # Add violation code if available
        if item.get('violation_code'):
            violations.append(f"Violation code: {item['violation_code']}")
        
        return violations if violations else ["No violations recorded"]
