import pandas as pd
import requests
import os
from datetime import datetime, timedelta
import json

class HealthInspectionAPI:
    """
    Multi-state client for fetching restaurant health inspection data from government sources
    """
    
    def __init__(self, jurisdiction="NYC"):
        # API endpoints for different jurisdictions
        self.apis = {
            "NYC": {
                "base_url": "https://data.cityofnewyork.us/resource/43nn-pn8j.json",
                "name": "New York City",
                "location_field": "boro",
                "grade_field": "grade",
                "name_field": "dba",
                "address_fields": ["building", "street", "boro", "zipcode"]
            },
            "Chicago": {
                "base_url": "https://data.cityofchicago.org/resource/4ijn-s7e5.json",
                "name": "Chicago, IL",
                "location_field": "ward",
                "grade_field": "results",
                "name_field": "dba_name",
                "address_fields": ["address", "city", "state", "zip"]
            }
        }
        
        self.current_jurisdiction = jurisdiction
        self.current_api = self.apis.get(jurisdiction, self.apis["NYC"])
        
        # Cache for API responses
        self._location_cache = {}
        self._data_cache = {}
        self._cache_timestamp = None
        self._cache_duration = 1800  # 30 minute cache for faster responses
        self._search_cache = {}  # Cache for search results
    
    def _make_api_request(self, endpoint, params=None):
        """Make API request with enhanced error handling and retries"""
        import time
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                headers = {
                    'User-Agent': 'Restaurant-Health-Inspector/1.0',
                    'Accept': 'application/json'
                }
                
                response = requests.get(
                    endpoint, 
                    params=params, 
                    headers=headers, 
                    timeout=60,  # Increased timeout
                    verify=True
                )
                response.raise_for_status()
                return response.json()
            
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise Exception("Request timed out after multiple attempts")
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise Exception("Connection failed - please check your internet connection")
            except requests.exceptions.RequestException as e:
                raise Exception(f"API request failed: {str(e)}")
            except json.JSONDecodeError as e:
                raise Exception(f"Invalid API response format: {str(e)}")
    
    def set_jurisdiction(self, jurisdiction):
        """Switch to a different jurisdiction"""
        if jurisdiction in self.apis:
            self.current_jurisdiction = jurisdiction
            self.current_api = self.apis[jurisdiction]
            # Clear cache when switching jurisdictions
            self._location_cache = {}
            self._search_cache = {}
            return True
        return False
    
    def get_available_jurisdictions(self):
        """Get list of supported jurisdictions"""
        return list(self.apis.keys())
    
    def _is_cache_valid(self):
        """Check if cache is still valid"""
        if self._cache_timestamp is None:
            return False
        return (datetime.now() - self._cache_timestamp).seconds < self._cache_duration
    
    def get_available_locations(self):
        """Get list of available locations/boroughs"""
        cache_key = self.current_jurisdiction
        if cache_key in self._location_cache and self._is_cache_valid():
            return self._location_cache[cache_key]
        
        try:
            if self.current_jurisdiction == "NYC":
                # Get distinct boroughs from NYC data
                params = {
                    '$select': 'DISTINCT boro',
                    '$limit': 10
                }
                
                data = self._make_api_request(self.current_api["base_url"], params)
                if data and isinstance(data, list):
                    locations = [item['boro'] for item in data if item.get('boro') and item['boro'].strip() and item['boro'] != '0']
                else:
                    locations = []
                
                # Add common NYC boroughs if not in data
                standard_boroughs = ['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island']
                for borough in standard_boroughs:
                    if borough not in locations:
                        locations.append(borough)
                        
            elif self.current_jurisdiction == "Chicago":
                # Chicago main API doesn't include ward data, use city districts instead
                locations = [
                    "North Side", "South Side", "West Side", "Downtown", 
                    "Loop", "Near North", "Near South", "Far North", "Far South"
                ]
            else:
                locations = []
            
            self._location_cache[cache_key] = sorted(locations)
            return self._location_cache[cache_key]
            
        except Exception as e:
            # Return default locations based on jurisdiction
            if self.current_jurisdiction == "NYC":
                return ['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island']
            elif self.current_jurisdiction == "Chicago":
                return [f"Ward {i}" for i in range(1, 11)]  # First 10 wards as fallback
            return []
    
    def get_restaurants(self, location=None, grades=None, cuisines=None, search_term=None, date_range=None, limit=1000):
        """
        Fetch restaurant inspection data with filters and pagination for larger datasets
        """
        try:
            # Create cache key for this search
            cache_key = f"{self.current_jurisdiction}_{location}_{grades}_{search_term}_{limit}"
            
            # Check if we have cached results
            import time
            if cache_key in self._search_cache:
                cached_result, cached_time = self._search_cache[cache_key]
                if time.time() - cached_time < 300:  # 5 minute cache for searches
                    return cached_result
            
            # Call jurisdiction-specific method
            if self.current_jurisdiction == "NYC":
                all_data = self._get_nyc_restaurants(location, grades, cuisines, search_term, date_range, limit)
            elif self.current_jurisdiction == "Chicago":
                all_data = self._get_chicago_restaurants(location, grades, cuisines, search_term, date_range, limit)
            else:
                return pd.DataFrame()
            
            # Cache the result for faster subsequent searches
            if all_data and len(all_data) > 0:
                result_df = pd.DataFrame(all_data)
            else:
                result_df = pd.DataFrame()
            
            self._search_cache[cache_key] = (result_df, time.time())
            return result_df
            
        except Exception as e:
            raise Exception(f"Failed to fetch restaurant data: {str(e)}")
    
    def _get_nyc_restaurants(self, location=None, grades=None, cuisines=None, search_term=None, date_range=None, limit=500):
        """Fetch NYC restaurant inspection data"""
        # Build where clause conditions
        where_conditions = ['grade IS NOT NULL']
        
        if location and location != "All":
            where_conditions.append(f"boro='{location}'")
        
        if grades:
            grade_conditions = [f"grade='{grade}'" for grade in grades]
            where_conditions.append(f"({' OR '.join(grade_conditions)})")
        
        if search_term:
            where_conditions.append(f"UPPER(dba) LIKE '%{search_term.upper()}%'")
        
        if date_range and len(date_range) == 2:
            start_date = date_range[0].strftime('%Y-%m-%d')
            end_date = date_range[1].strftime('%Y-%m-%d')
            where_conditions.append(f"inspection_date >= '{start_date}' AND inspection_date <= '{end_date}'")
        
        where_clause = ' AND '.join(where_conditions)
        
        # API request parameters
        params = {
            '$limit': min(limit, 500),
            '$order': 'inspection_date DESC',
            '$where': where_clause,
            '$select': 'camis,dba,boro,building,street,zipcode,phone,cuisine_description,inspection_date,action,violation_code,violation_description,critical_flag,score,grade,grade_date,record_date,inspection_type'
        }
        
        raw_data = self._make_api_request(self.current_api["base_url"], params)
        
        if not raw_data:
            return []
        
        # Process NYC data
        restaurants = []
        seen_restaurants = set()
        
        for item in raw_data:
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
        
        # Apply cuisine filter if specified
        if cuisines and "All" not in cuisines:
            restaurants = [r for r in restaurants if r['cuisine_type'] in cuisines]
        
        return restaurants[:limit]
    
    def _get_chicago_restaurants(self, location=None, grades=None, cuisines=None, search_term=None, date_range=None, limit=500):
        """Fetch Chicago restaurant inspection data"""
        # Build where clause conditions
        where_conditions = ['results IS NOT NULL']
        
        # Chicago API doesn't have ward data in main endpoint, so skip location filtering
        # if location and location != "All" and location.startswith("Ward "):
        #     ward_num = location.split()[1]
        #     where_conditions.append(f"ward='{ward_num}'")
        
        if grades:
            # Map NYC grades to Chicago results
            chicago_results = []
            for grade in grades:
                if grade == "A":
                    chicago_results.extend(["Pass", "Pass w/ Conditions"])
                elif grade == "B":
                    chicago_results.append("Pass w/ Conditions")
                elif grade == "C":
                    chicago_results.extend(["Fail", "Out of Business"])
                elif grade in ["Grade Pending", "Not Yet Graded"]:
                    chicago_results.append("Not Ready")
            
            if chicago_results:
                result_conditions = [f"results='{result}'" for result in chicago_results]
                where_conditions.append(f"({' OR '.join(result_conditions)})")
        
        if search_term:
            where_conditions.append(f"UPPER(dba_name) LIKE '%{search_term.upper()}%'")
        
        if date_range and len(date_range) == 2:
            start_date = date_range[0].strftime('%Y-%m-%d')
            end_date = date_range[1].strftime('%Y-%m-%d')
            where_conditions.append(f"inspection_date >= '{start_date}' AND inspection_date <= '{end_date}'")
        
        where_clause = ' AND '.join(where_conditions)
        
        # API request parameters (Chicago doesn't have violations or ward in main dataset)
        params = {
            '$limit': min(limit, 500),
            '$order': 'inspection_date DESC',
            '$where': where_clause,
            '$select': 'license_,dba_name,aka_name,facility_type,risk,address,city,state,zip,inspection_date,inspection_type,results,latitude,longitude'
        }
        
        raw_data = self._make_api_request(self.current_api["base_url"], params)
        
        if not raw_data:
            return []
        
        # Process Chicago data
        restaurants = []
        seen_restaurants = set()
        
        for item in raw_data:
            # Create unique identifier for restaurant
            restaurant_key = (item.get('dba_name', '').strip(), item.get('address', ''))
            
            if restaurant_key in seen_restaurants:
                continue
            seen_restaurants.add(restaurant_key)
            
            # Map Chicago results to NYC-style grades
            chicago_result = item.get('results', '')
            if chicago_result == "Pass":
                grade = "A"
            elif chicago_result == "Pass w/ Conditions":
                grade = "B"
            elif chicago_result in ["Fail", "Out of Business"]:
                grade = "C"
            else:
                grade = "Not Yet Graded"
            
            # Extract and clean restaurant data
            restaurant = {
                'id': f"CHI_{item.get('license_', '')}{item.get('dba_name', '').replace(' ', '')}",
                'name': item.get('dba_name', 'Unknown Restaurant').strip(),
                'address': self._format_chicago_address(item),
                'cuisine_type': item.get('facility_type', 'Not specified'),
                'grade': grade,
                'score': None,  # Chicago doesn't use numeric scores
                'inspection_date': item.get('inspection_date', '').split('T')[0] if item.get('inspection_date') else 'N/A',
                'violations': ["Violation details not available in Chicago dataset"],
                'boro': 'Chicago',  # Since ward data isn't available in main endpoint
                'phone': '',  # Not available in Chicago data
                'inspection_type': item.get('inspection_type', ''),
                'risk': item.get('risk', '')
            }
            
            restaurants.append(restaurant)
        
        # Apply cuisine filter if specified
        if cuisines and "All" not in cuisines:
            restaurants = [r for r in restaurants if r['cuisine_type'] in cuisines]
        
        return restaurants[:limit]
    
    def _format_chicago_address(self, item):
        """Format Chicago restaurant address from API data"""
        address = item.get('address', '')
        city = item.get('city', '')
        state = item.get('state', '')
        zip_code = item.get('zip', '')
        
        address_parts = [part for part in [address, city, state, zip_code] if part]
        return ', '.join(address_parts) if address_parts else 'Address not available'
    
    def _extract_chicago_violations(self, item):
        """Extract violation information from Chicago API response"""
        violations = []
        violation_text = item.get('violations', '')
        
        if violation_text and violation_text.strip():
            # Chicago violations are in a single text field, split by common delimiters
            violation_parts = violation_text.replace('|', '\n').split('\n')
            for part in violation_parts:
                if part.strip():
                    violations.append(part.strip())
        
        return violations if violations else ["No violations recorded"]
    
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
