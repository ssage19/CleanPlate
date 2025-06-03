import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from data_fetcher import HealthInspectionAPI

class RestaurantDataVisualizer:
    """Comprehensive data visualization for restaurant health inspection data"""
    
    def __init__(self):
        self.api_client = HealthInspectionAPI()
        
    def create_city_comparison_dashboard(self):
        """Create comprehensive city health performance comparison"""
        st.markdown("## 🏙️ City Health Performance Dashboard")
        st.markdown("Compare health inspection performance across all 6 major cities")
        
        # Collect data from all cities
        city_data = {}
        jurisdictions = ["NYC", "Chicago", "Boston", "Austin", "Seattle", "Los Angeles"]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, jurisdiction in enumerate(jurisdictions):
            status_text.text(f"Loading {jurisdiction} data...")
            progress_bar.progress((i + 1) / len(jurisdictions))
            
            try:
                self.api_client.set_jurisdiction(jurisdiction)
                restaurants_df = self.api_client.get_restaurants(limit=500)
                
                if not restaurants_df.empty:
                    city_data[jurisdiction] = restaurants_df
                    
            except Exception as e:
                st.warning(f"Could not load data for {jurisdiction}: {str(e)}")
                
        status_text.empty()
        progress_bar.empty()
        
        if not city_data:
            st.error("No data available for visualization")
            return
            
        # Create city comparison metrics
        self._create_city_metrics_comparison(city_data)
        
        # Create grade distribution charts
        self._create_grade_distribution_charts(city_data)
        
        # Create violation analysis
        self._create_violation_severity_analysis(city_data)
        
    def _create_city_metrics_comparison(self, city_data):
        """Create city metrics comparison table and charts"""
        st.markdown("### 📊 City Performance Metrics")
        
        metrics_data = []
        
        for city, df in city_data.items():
            if df.empty:
                continue
                
            # Calculate city-specific metrics
            total_restaurants = len(df)
            
            # Get grading system info for this city
            self.api_client.set_jurisdiction(city)
            grading_info = self.api_client.get_grading_system_info()
            
            # Calculate grade distribution based on city's grading system
            if grading_info.get('type') == 'letter':
                excellent_grades = ['A']
                good_grades = ['B'] 
                poor_grades = ['C', 'F']
            elif grading_info.get('type') == 'pass_fail':
                excellent_grades = ['Pass']
                good_grades = []
                poor_grades = ['Fail', 'Conditional']
            else:  # numeric or violation points
                # For numeric systems, categorize based on score ranges
                if city == 'Seattle':  # violation points (lower is better)
                    excellent_count = len(df[df['score'].astype(str).str.contains('0|1-10', na=False)])
                    good_count = len(df[df['score'].astype(str).str.contains('11-25', na=False)])
                    poor_count = len(df[df['score'].astype(str).str.contains('26-|51+', na=False)])
                else:  # Austin (higher scores are better)
                    excellent_count = len(df[pd.to_numeric(df['score'], errors='coerce') >= 90])
                    good_count = len(df[(pd.to_numeric(df['score'], errors='coerce') >= 80) & 
                                      (pd.to_numeric(df['score'], errors='coerce') < 90)])
                    poor_count = len(df[pd.to_numeric(df['score'], errors='coerce') < 80])
                    
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
                continue
            
            # For letter and pass/fail systems
            excellent_count = len(df[df['grade'].isin(excellent_grades)])
            good_count = len(df[df['grade'].isin(good_grades)]) if good_grades else 0
            poor_count = len(df[df['grade'].isin(poor_grades)])
            
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
    
    def _create_grade_distribution_charts(self, city_data):
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
    
    def _create_violation_severity_analysis(self, city_data):
        """Create violation severity heatmap and analysis"""
        st.markdown("### 🔥 Violation Severity Analysis")
        
        # Collect violation data across cities
        all_violations = []
        
        for city, df in city_data.items():
            if df.empty or 'violations' not in df.columns:
                continue
                
            for _, row in df.iterrows():
                violations = row.get('violations', [])
                if violations and isinstance(violations, list):
                    for violation in violations:
                        if violation and violation != "No violations recorded":
                            # Categorize violation severity based on keywords
                            severity = self._categorize_violation_severity(violation)
                            all_violations.append({
                                'City': city,
                                'Violation': violation[:50] + "..." if len(violation) > 50 else violation,
                                'Severity': severity,
                                'Restaurant': row.get('name', 'Unknown')
                            })
        
        if all_violations:
            violations_df = pd.DataFrame(all_violations)
            
            # Create severity distribution by city
            severity_city = violations_df.groupby(['City', 'Severity']).size().unstack(fill_value=0)
            
            fig = px.imshow(
                severity_city.values,
                x=severity_city.columns,
                y=severity_city.index,
                color_continuous_scale='Reds',
                title="Violation Severity Heatmap by City",
                labels=dict(x="Severity Level", y="City", color="Number of Violations")
            )
            fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Show top violation types
            st.markdown("### 📋 Most Common Violation Types")
            top_violations = violations_df['Violation'].value_counts().head(10)
            
            fig_violations = px.bar(
                x=top_violations.values,
                y=top_violations.index,
                orientation='h',
                title="Top 10 Most Common Violations",
                labels={'x': 'Frequency', 'y': 'Violation Type'}
            )
            fig_violations.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                height=500
            )
            st.plotly_chart(fig_violations, use_container_width=True)
    
    def _categorize_violation_severity(self, violation_text):
        """Categorize violation severity based on keywords"""
        violation_lower = violation_text.lower()
        
        # Critical violations
        critical_keywords = ['critical', 'immediate', 'unsafe', 'contamination', 'sewage', 
                           'vermin', 'pest', 'toxic', 'poisoning', 'illness']
        
        # Major violations  
        major_keywords = ['major', 'temperature', 'cross contamination', 'expired', 
                         'unapproved', 'inadequate', 'improper']
        
        # Minor violations
        minor_keywords = ['minor', 'cleaning', 'sanitizing', 'maintenance', 'documentation',
                         'signage', 'lighting']
        
        if any(keyword in violation_lower for keyword in critical_keywords):
            return 'Critical'
        elif any(keyword in violation_lower for keyword in major_keywords):
            return 'Major'
        elif any(keyword in violation_lower for keyword in minor_keywords):
            return 'Minor'
        else:
            return 'Moderate'
    
    def create_inspection_frequency_analysis(self):
        """Analyze inspection frequency patterns"""
        st.markdown("## 📅 Inspection Frequency Analysis")
        
        # City selection for detailed analysis
        jurisdictions = ["NYC", "Chicago", "Boston", "Austin", "Seattle", "Los Angeles"]
        selected_city = st.selectbox("Select city for detailed inspection analysis:", jurisdictions)
        
        if st.button("Analyze Inspection Patterns"):
            with st.spinner("Analyzing inspection frequency patterns..."):
                try:
                    self.api_client.set_jurisdiction(selected_city)
                    restaurants_df = self.api_client.get_restaurants(limit=1000)
                    
                    if not restaurants_df.empty and 'inspection_date' in restaurants_df.columns:
                        # Parse inspection dates
                        restaurants_df['inspection_date_parsed'] = pd.to_datetime(
                            restaurants_df['inspection_date'], errors='coerce'
                        )
                        
                        # Remove rows with invalid dates
                        valid_dates_df = restaurants_df.dropna(subset=['inspection_date_parsed'])
                        
                        if not valid_dates_df.empty:
                            # Create inspection timeline
                            self._create_inspection_timeline(valid_dates_df, selected_city)
                            
                            # Create monthly inspection patterns
                            self._create_monthly_patterns(valid_dates_df, selected_city)
                        else:
                            st.warning(f"No valid inspection dates found for {selected_city}")
                    else:
                        st.warning(f"No inspection data available for {selected_city}")
                        
                except Exception as e:
                    st.error(f"Error analyzing inspection patterns: {str(e)}")
    
    def _create_inspection_timeline(self, df, city):
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
    
    def _create_monthly_patterns(self, df, city):
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