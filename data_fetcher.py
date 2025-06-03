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
                "address_fields": ["building", "street", "boro", "zipcode"],
                "grading_system": {
                    "type": "letter",
                    "grades": {
                        "A": {"label": "A", "description": "Grade A", "color": "#22c55e", "priority": "low"},
                        "B": {"label": "B", "description": "Grade B", "color": "#f59e0b", "priority": "medium"},
                        "C": {"label": "C", "description": "Grade C", "color": "#ef4444", "priority": "high"},
                        "Grade Pending": {"label": "Pending", "description": "Grade Pending", "color": "#6b7280", "priority": "medium"},
                        "Not Yet Graded": {"label": "Not Graded", "description": "Not Yet Graded", "color": "#6b7280", "priority": "medium"}
                    },
                    "score_system": True,
                    "score_description": "Lower scores indicate better performance"
                }
            },
            "Chicago": {
                "base_url": "https://data.cityofchicago.org/resource/4ijn-s7e5.json",
                "name": "Chicago, IL",
                "location_field": "ward",
                "grade_field": "results",
                "name_field": "dba_name",
                "address_fields": ["address", "city", "state", "zip"],
                "grading_system": {
                    "type": "pass_fail",
                    "grades": {
                        "Pass": {"label": "Pass", "description": "Passed Inspection", "color": "#22c55e", "priority": "low"},
                        "Pass w/ Conditions": {"label": "Pass*", "description": "Pass with Conditions", "color": "#f59e0b", "priority": "medium"},
                        "Fail": {"label": "Fail", "description": "Failed Inspection", "color": "#ef4444", "priority": "high"},
                        "Out of Business": {"label": "Closed", "description": "Out of Business", "color": "#6b7280", "priority": "high"},
                        "Not Ready": {"label": "Not Ready", "description": "Not Ready for Inspection", "color": "#6b7280", "priority": "medium"}
                    },
                    "score_system": False,
                    "risk_system": True,
                    "risk_levels": {
                        "Risk 1 (High)": {"label": "High Risk", "description": "High Risk Facility", "color": "#ef4444", "priority": "high"},
                        "Risk 2 (Medium)": {"label": "Medium Risk", "description": "Medium Risk Facility", "color": "#f59e0b", "priority": "medium"},
                        "Risk 3 (Low)": {"label": "Low Risk", "description": "Low Risk Facility", "color": "#22c55e", "priority": "low"}
                    }
                }
            },
            "Boston": {
                "base_url": "https://data.boston.gov/api/3/action/datastore_search",
                "resource_id": "4582bec6-2b4f-4f9e-bc55-cbaa73117f4c",
                "name": "Boston, MA",
                "location_field": "city",
                "grade_field": "viollevel",
                "name_field": "businessname",
                "address_fields": ["address", "city", "state", "zip"],
                "grading_system": {
                    "type": "pass_fail",
                    "grades": {
                        "HE_Pass": {"label": "Pass", "description": "Passed Health Inspection", "color": "#22c55e", "priority": "low"},
                        "HE_Fail": {"label": "Fail", "description": "Failed Health Inspection", "color": "#ef4444", "priority": "high"},
                        "Conditional": {"label": "Conditional", "description": "Conditional Pass", "color": "#f59e0b", "priority": "medium"}
                    },
                    "score_system": False,
                    "violation_system": True,
                    "violation_levels": {
                        "*": {"label": "Critical", "description": "Critical Violations", "color": "#ef4444"},
                        "**": {"label": "Serious", "description": "Serious Violations", "color": "#f59e0b"},
                        "***": {"label": "Minor", "description": "Minor Violations", "color": "#22c55e"}
                    }
                }
            },
            "Austin": {
                "base_url": "https://data.austintexas.gov/resource/ecmv-9xxi.json",
                "name": "Austin, TX",
                "location_field": "zip_code",
                "grade_field": "score",
                "name_field": "restaurant_name",
                "address_fields": ["address_1", "address_2", "city", "state", "zip_code"],
                "grading_system": {
                    "type": "numeric_score",
                    "grades": {
                        "90-100": {"label": "A", "description": "Excellent (90-100)", "color": "#22c55e", "priority": "low"},
                        "80-89": {"label": "B", "description": "Good (80-89)", "color": "#f59e0b", "priority": "medium"},
                        "70-79": {"label": "C", "description": "Satisfactory (70-79)", "color": "#ef4444", "priority": "high"},
                        "Below 70": {"label": "F", "description": "Needs Improvement (<70)", "color": "#dc2626", "priority": "high"}
                    },
                    "score_system": True,
                    "score_description": "Higher scores indicate better performance"
                }
            },
            "Seattle": {
                "base_url": "https://data.seattle.gov/resource/f29f-zza5.json",
                "name": "Seattle, WA",
                "location_field": "zip_code",
                "grade_field": "grade",
                "name_field": "name",
                "address_fields": ["address", "city", "zip_code"],
                "grading_system": {
                    "type": "letter_with_scores",
                    "grades": {
                        "Excellent": {"label": "Excellent", "description": "Excellent Rating", "color": "#22c55e", "priority": "low"},
                        "Good": {"label": "Good", "description": "Good Rating", "color": "#22c55e", "priority": "low"},
                        "Okay": {"label": "Okay", "description": "Okay Rating", "color": "#f59e0b", "priority": "medium"},
                        "Needs Improvement": {"label": "Poor", "description": "Needs Improvement", "color": "#ef4444", "priority": "high"},
                        "Unsatisfactory": {"label": "Fail", "description": "Unsatisfactory Rating", "color": "#dc2626", "priority": "high"}
                    },
                    "score_system": True,
                    "score_description": "Inspection score and violation points"
                }
            },
            "San Diego": {
                "base_url": "https://data.sandiego.gov/api/3/action/datastore_search",
                "resource_id": "ee7f2771-712d-4349-8e39-be17e8921af3",
                "name": "San Diego, CA",
                "location_field": "zip",
                "grade_field": "grade",
                "name_field": "business_name",
                "address_fields": ["address", "city", "zip"],
                "grading_system": {
                    "type": "letter",
                    "grades": {
                        "A": {"label": "A", "description": "Grade A", "color": "#22c55e", "priority": "low"},
                        "B": {"label": "B", "description": "Grade B", "color": "#f59e0b", "priority": "medium"},
                        "C": {"label": "C", "description": "Grade C", "color": "#ef4444", "priority": "high"}
                    },
                    "score_system": True,
                    "score_description": "Health inspection score"
                }
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
    
    def get_grade_info(self, grade):
        """Get jurisdiction-specific grade information"""
        grading_system = self.current_api.get("grading_system", {})
        grades = grading_system.get("grades", {})
        return grades.get(grade, {
            "label": grade,
            "description": grade,
            "color": "#6b7280",
            "priority": "medium"
        })
    
    def get_risk_info(self, risk_level):
        """Get jurisdiction-specific risk level information"""
        grading_system = self.current_api.get("grading_system", {})
        risk_levels = grading_system.get("risk_levels", {})
        return risk_levels.get(risk_level, {
            "label": risk_level,
            "description": risk_level,
            "color": "#6b7280",
            "priority": "medium"
        })
    
    def get_grading_system_info(self):
        """Get current jurisdiction's grading system information"""
        return self.current_api.get("grading_system", {})
    
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
            elif self.current_jurisdiction == "Boston":
                # Boston neighborhoods
                locations = [
                    "Back Bay", "Beacon Hill", "Charlestown", "Chinatown", "Dorchester",
                    "East Boston", "Fenway", "North End", "Roxbury", "South End"
                ]
            elif self.current_jurisdiction == "Austin":
                # Austin ZIP code areas (major zones)
                locations = [
                    "Downtown (78701)", "East Austin (78702)", "South Austin (78704)",
                    "West Austin (78703)", "North Austin (78751)", "Cedar Park (78613)"
                ]
            elif self.current_jurisdiction == "Seattle":
                # Seattle neighborhoods
                locations = [
                    "Capitol Hill", "Ballard", "Fremont", "Queen Anne", "Belltown",
                    "University District", "Georgetown", "Pioneer Square", "SoDo"
                ]
            elif self.current_jurisdiction == "San Diego":
                # San Diego districts
                locations = [
                    "Downtown", "Hillcrest", "Mission Beach", "Pacific Beach", "La Jolla",
                    "Balboa Park", "Gaslamp Quarter", "Little Italy", "Mission Valley"
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
            elif self.current_jurisdiction == "Boston":
                all_data = self._get_boston_restaurants(location, grades, cuisines, search_term, date_range, limit)
            elif self.current_jurisdiction == "Austin":
                all_data = self._get_austin_restaurants(location, grades, cuisines, search_term, date_range, limit)
            elif self.current_jurisdiction == "Seattle":
                all_data = self._get_seattle_restaurants(location, grades, cuisines, search_term, date_range, limit)
            elif self.current_jurisdiction == "San Diego":
                all_data = self._get_sandiego_restaurants(location, grades, cuisines, search_term, date_range, limit)
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
            
            # Use native Chicago grading system
            chicago_result = item.get('results', 'Not Ready')
            grade = chicago_result  # Keep original Chicago grade
            
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
    
    def _get_austin_restaurants(self, location=None, grades=None, cuisines=None, search_term=None, date_range=None, limit=500):
        """Fetch Austin restaurant inspection data"""
        where_conditions = ['score IS NOT NULL']
        
        if search_term:
            where_conditions.append(f"UPPER(restaurant_name) LIKE '%{search_term.upper()}%'")
        
        if date_range and len(date_range) == 2:
            start_date = date_range[0].strftime('%Y-%m-%d')
            end_date = date_range[1].strftime('%Y-%m-%d')
            where_conditions.append(f"inspection_date >= '{start_date}' AND inspection_date <= '{end_date}'")
        
        where_clause = ' AND '.join(where_conditions)
        
        params = {
            '$limit': min(limit, 500),
            '$order': 'inspection_date DESC',
            '$where': where_clause,
            '$select': 'restaurant_name,address,zip_code,score,inspection_date,process_description,facility_id'
        }
        
        raw_data = self._make_api_request(self.current_api["base_url"], params)
        
        if not raw_data:
            return []
        
        restaurants = []
        seen_restaurants = set()
        
        for item in raw_data:
            restaurant_key = (item.get('restaurant_name', '').strip(), item.get('address_1', ''))
            
            if restaurant_key in seen_restaurants:
                continue
            seen_restaurants.add(restaurant_key)
            
            # Convert score to Austin grade
            score = self._safe_int(item.get('score'))
            if score and score >= 90:
                grade = "90-100"
            elif score and score >= 80:
                grade = "80-89"
            elif score and score >= 70:
                grade = "70-79"
            else:
                grade = "Below 70"
            
            restaurant = {
                'id': f"AUS_{item.get('facility_id', '')}{item.get('restaurant_name', '').replace(' ', '')}",
                'name': item.get('restaurant_name', 'Unknown Restaurant').strip(),
                'address': f"{item.get('address', '')}, Austin, TX {item.get('zip_code', '')}",
                'cuisine_type': item.get('process_description', 'Not specified'),
                'grade': grade,
                'score': score,
                'inspection_date': item.get('inspection_date', '').split('T')[0] if item.get('inspection_date') else 'N/A',
                'violations': ["Violation details not available in Austin dataset"],
                'boro': f"Austin, TX {item.get('zip_code', '')}",
                'phone': '',
                'inspection_type': 'Regular Inspection'
            }
            
            restaurants.append(restaurant)
        
        if cuisines and "All" not in cuisines:
            restaurants = [r for r in restaurants if r['cuisine_type'] in cuisines]
        
        return restaurants[:limit]
    
    def _get_seattle_restaurants(self, location=None, grades=None, cuisines=None, search_term=None, date_range=None, limit=500):
        """Fetch Seattle restaurant inspection data"""
        where_conditions = ['grade IS NOT NULL']
        
        if search_term:
            where_conditions.append(f"UPPER(name) LIKE '%{search_term.upper()}%'")
        
        if date_range and len(date_range) == 2:
            start_date = date_range[0].strftime('%Y-%m-%d')
            end_date = date_range[1].strftime('%Y-%m-%d')
            where_conditions.append(f"inspection_date >= '{start_date}' AND inspection_date <= '{end_date}'")
        
        where_clause = ' AND '.join(where_conditions)
        
        params = {
            '$limit': min(limit, 500),
            '$order': 'inspection_date DESC',
            '$where': where_clause,
            '$select': 'name,address,city,zip_code,grade,inspection_score,inspection_date,business_id,program_identifier'
        }
        
        raw_data = self._make_api_request(self.current_api["base_url"], params)
        
        if not raw_data:
            return []
        
        restaurants = []
        seen_restaurants = set()
        
        for item in raw_data:
            restaurant_key = (item.get('name', '').strip(), item.get('address', ''))
            
            if restaurant_key in seen_restaurants:
                continue
            seen_restaurants.add(restaurant_key)
            
            restaurant = {
                'id': f"SEA_{item.get('business_id', '')}{item.get('name', '').replace(' ', '')}",
                'name': item.get('name', 'Unknown Restaurant').strip(),
                'address': self._format_seattle_address(item),
                'cuisine_type': item.get('program_identifier', 'Not specified'),
                'grade': item.get('grade', 'Not Graded'),
                'score': self._safe_int(item.get('inspection_score')),
                'inspection_date': item.get('inspection_date', '').split('T')[0] if item.get('inspection_date') else 'N/A',
                'violations': ["Violation details not available in Seattle dataset"],
                'boro': f"Seattle, WA {item.get('zip_code', '')}",
                'phone': '',
                'inspection_type': 'Health Inspection'
            }
            
            restaurants.append(restaurant)
        
        if cuisines and "All" not in cuisines:
            restaurants = [r for r in restaurants if r['cuisine_type'] in cuisines]
        
        return restaurants[:limit]
    
    def _get_boston_restaurants(self, location=None, grades=None, cuisines=None, search_term=None, date_range=None, limit=500):
        """Fetch Boston restaurant inspection data"""
        # Boston uses CKAN API format
        params = {
            'resource_id': self.current_api["resource_id"],
            'limit': min(limit, 500)
        }
        
        # Add search filters
        filters = {}
        if search_term:
            filters['businessname'] = search_term
        
        if filters:
            params['filters'] = json.dumps(filters)
        
        raw_data = self._make_api_request(self.current_api["base_url"], params)
        
        if not raw_data or 'result' not in raw_data or 'records' not in raw_data['result']:
            return []
        
        records = raw_data['result']['records']
        restaurants = []
        seen_restaurants = set()
        
        for item in records:
            restaurant_key = (item.get('businessname', '').strip(), item.get('address', ''))
            
            if restaurant_key in seen_restaurants:
                continue
            seen_restaurants.add(restaurant_key)
            
            # Use Boston's pass/fail result system
            result = item.get('result', 'Unknown')
            grade = result if result in ['HE_Pass', 'HE_Fail', 'Conditional'] else 'HE_Fail'
            
            # Get violation information
            violation_desc = item.get('violdesc', 'No violations recorded')
            viol_level = item.get('viol_level', '')
            
            restaurant = {
                'id': f"BOS_{item.get('licenseno', '')}{item.get('businessname', '').replace(' ', '')}",
                'name': item.get('businessname', 'Unknown Restaurant').strip(),
                'address': self._format_boston_address(item),
                'cuisine_type': item.get('descript', 'Not specified'),
                'grade': grade,
                'score': None,
                'inspection_date': item.get('resultdttm', '').split('T')[0] if item.get('resultdttm') else 'N/A',
                'violations': [f"({viol_level}) {violation_desc}" if viol_level else violation_desc],
                'boro': f"Boston, MA {item.get('zip', '')}",
                'phone': '',
                'inspection_type': 'Health Inspection',
                'violation_level': viol_level
            }
            
            restaurants.append(restaurant)
        
        if cuisines and "All" not in cuisines:
            restaurants = [r for r in restaurants if r['cuisine_type'] in cuisines]
        
        return restaurants[:limit]
    
    def _get_sandiego_restaurants(self, location=None, grades=None, cuisines=None, search_term=None, date_range=None, limit=500):
        """Fetch San Diego restaurant inspection data"""
        # San Diego uses CKAN API format
        params = {
            'resource_id': self.current_api["resource_id"],
            'limit': min(limit, 500)
        }
        
        # Add search filters
        filters = {}
        if search_term:
            filters['business_name'] = search_term
        
        if filters:
            params['filters'] = json.dumps(filters)
        
        raw_data = self._make_api_request(self.current_api["base_url"], params)
        
        if not raw_data or 'result' not in raw_data or 'records' not in raw_data['result']:
            return []
        
        records = raw_data['result']['records']
        restaurants = []
        seen_restaurants = set()
        
        for item in records:
            restaurant_key = (item.get('business_name', '').strip(), item.get('address', ''))
            
            if restaurant_key in seen_restaurants:
                continue
            seen_restaurants.add(restaurant_key)
            
            restaurant = {
                'id': f"SD_{item.get('serial_number', '')}{item.get('business_name', '').replace(' ', '')}",
                'name': item.get('business_name', 'Unknown Restaurant').strip(),
                'address': self._format_sandiego_address(item),
                'cuisine_type': item.get('business_category', 'Not specified'),
                'grade': item.get('grade', 'Not Graded'),
                'score': self._safe_int(item.get('inspection_score')),
                'inspection_date': item.get('activity_date', '').split('T')[0] if item.get('activity_date') else 'N/A',
                'violations': ["Violation details not available in San Diego dataset"],
                'boro': f"San Diego, CA {item.get('zip', '')}",
                'phone': '',
                'inspection_type': 'Health Inspection'
            }
            
            restaurants.append(restaurant)
        
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
    
    def _format_austin_address(self, item):
        """Format Austin restaurant address from API data"""
        address_1 = item.get('address_1', '')
        address_2 = item.get('address_2', '')
        city = item.get('city', '')
        state = item.get('state', '')
        zip_code = item.get('zip_code', '')
        
        address_parts = [part for part in [address_1, address_2, city, state, zip_code] if part]
        return ', '.join(address_parts) if address_parts else 'Address not available'
    
    def _format_seattle_address(self, item):
        """Format Seattle restaurant address from API data"""
        address = item.get('address', '')
        city = item.get('city', '')
        zip_code = item.get('zip_code', '')
        
        address_parts = [part for part in [address, city, zip_code] if part]
        return ', '.join(address_parts) if address_parts else 'Address not available'
    
    def _format_boston_address(self, item):
        """Format Boston restaurant address from API data"""
        address = item.get('address', '')
        city = item.get('city', '')
        state = item.get('state', '')
        zip_code = item.get('zip', '')
        
        address_parts = [part for part in [address, city, state, zip_code] if part]
        return ', '.join(address_parts) if address_parts else 'Address not available'
    
    def _format_sandiego_address(self, item):
        """Format San Diego restaurant address from API data"""
        address = item.get('address', '')
        city = item.get('city', '')
        zip_code = item.get('zip', '')
        
        address_parts = [part for part in [address, city, zip_code] if part]
        return ', '.join(address_parts) if address_parts else 'Address not available'
    
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
