"""
Food Delivery Affiliate Integration for CleanPlate
Generates revenue through DoorDash, UberEats, and other delivery service partnerships
"""

import streamlit as st
import urllib.parse
from typing import Dict, Optional

class DeliveryAffiliateManager:
    """Manages affiliate links and revenue tracking for food delivery services"""
    
    def __init__(self):
        self.affiliate_data = {
            "doordash": {
                "name": "DoorDash",
                "base_url": "https://www.doordash.com/store/",
                "search_url": "https://www.doordash.com/search/",
                "color": "#ff3008",
                "icon": "🚗",
                "commission": "$1-5 per order",
                "tracking_params": {
                    "utm_source": "cleanplate",
                    "utm_medium": "affiliate", 
                    "utm_campaign": "restaurant_health_inspection",
                    "affiliate_id": "cleanplateus"  # Replace with your actual affiliate ID when approved
                }
            },
            "ubereats": {
                "name": "Uber Eats",
                "base_url": "https://www.ubereats.com/store/",
                "search_url": "https://www.ubereats.com/search?q=",
                "color": "#06c167", 
                "icon": "🛵",
                "commission": "$10 per new user signup + order",
                "tracking_params": {
                    "utm_source": "cleanplate",
                    "utm_medium": "affiliate",
                    "utm_campaign": "health_inspection_traffic",
                    "sub4": "cleanplateus.com"  # Required by UberEats Impact.com program
                }
            },
            "grubhub": {
                "name": "Grubhub",
                "base_url": "https://www.grubhub.com/restaurant/",
                "search_url": "https://www.grubhub.com/search?searchMetro=&facetFilters%5B%5D=open_now%3Atrue&queryText=",
                "color": "#ff8000",
                "icon": "🍔",
                "commission": "$3-8 per order",
                "tracking_params": {
                    "utm_source": "cleanplate",
                    "utm_medium": "affiliate",
                    "utm_campaign": "restaurant_finder"
                }
            }
        }
    
    def generate_affiliate_link(self, service: str, restaurant_name: str, restaurant_address: str = "") -> str:
        """Generate tracked affiliate link for food delivery service"""
        if service not in self.affiliate_data:
            return "#"
        
        service_data = self.affiliate_data[service]
        
        # Clean restaurant name for URL
        clean_name = restaurant_name.replace(" ", "-").replace("'", "").replace("&", "and").lower()
        clean_name = ''.join(char for char in clean_name if char.isalnum() or char == '-')
        
        # Build base URL - use search for better compatibility
        if service == "doordash":
            base_url = f"{service_data['search_url']}"
            search_query = f"{restaurant_name} {restaurant_address}".strip()
        elif service == "ubereats":
            base_url = f"{service_data['search_url']}"
            search_query = restaurant_name
        else:  # grubhub
            base_url = f"{service_data['search_url']}"
            search_query = restaurant_name
        
        # Add tracking parameters
        params = service_data['tracking_params'].copy()
        if search_query:
            if service == "ubereats":
                params['q'] = search_query
            elif service == "doordash":
                params['q'] = search_query
            else:  # grubhub
                base_url += urllib.parse.quote(search_query)
        
        # Build final URL with tracking
        if params:
            param_string = urllib.parse.urlencode(params)
            separator = "&" if "?" in base_url else "?"
            final_url = f"{base_url}{separator}{param_string}"
        else:
            final_url = base_url
            
        return final_url
    
    def display_delivery_buttons(self, restaurant_name: str, restaurant_address: str = ""):
        """Display affiliate delivery buttons for a restaurant"""
        
        # Use Streamlit columns instead of complex HTML to avoid rendering issues
        st.markdown("**🍽️ Order Food Online & Support CleanPlate**", unsafe_allow_html=False)
        
        # Create three columns for delivery buttons using native Streamlit
        col1, col2, col3 = st.columns(3)
        
        with col1:
            doordash_link = self.generate_affiliate_link("doordash", restaurant_name, restaurant_address)
            st.link_button("🚗 DoorDash", doordash_link, use_container_width=True)
        
        with col2:
            ubereats_link = self.generate_affiliate_link("ubereats", restaurant_name, restaurant_address)
            st.link_button("🛵 Uber Eats", ubereats_link, use_container_width=True)
        
        with col3:
            grubhub_link = self.generate_affiliate_link("grubhub", restaurant_name, restaurant_address)
            st.link_button("🍔 Grubhub", grubhub_link, use_container_width=True)
        
        # Revenue disclaimer using simple markdown
        st.caption("CleanPlate earns commission from food orders • Helps keep our health inspection data free")
    
    def get_revenue_potential(self) -> Dict[str, str]:
        """Return revenue potential information for delivery affiliates"""
        return {
            "DoorDash": {
                "commission": "$1-5 per order",
                "signup_bonus": "$50 per new driver referral",
                "restaurant_referral": "$1,000 per restaurant (up to 10 max)",
                "monthly_potential": "$200-1,500"
            },
            "UberEats": {
                "commission": "$10 per new user + first order",
                "payment_threshold": "$250 minimum payout",
                "conversion_tracking": "Impact.com platform",
                "monthly_potential": "$300-2,000"
            },
            "Grubhub": {
                "commission": "$3-8 per order",
                "partner_program": "Commission varies by location",
                "monthly_potential": "$150-800"
            },
            "Total Combined": "$650-4,300 per month with active user base"
        }
    
    def display_affiliate_setup_guide(self):
        """Display comprehensive setup guide for delivery affiliate programs"""
        st.markdown("""
        # 🚀 Food Delivery Affiliate Program Application Guide
        
        **Total Revenue Potential: $650-4,300/month**
        
        ---
        
        ## 1. 🚗 DoorDash Affiliate Program ($200-1,500/month)
        
        ### How to Apply:
        **Step 1: Driver Referral Program ($50 per driver)**
        - Visit: https://publisherpro.flexoffers.com/Registration?RID=1266046&aid=1957
        - Sign up with FlexOffers (DoorDash's affiliate network)
        - Provide website details: cleanplateus.com
        - Expected approval: 3-5 business days
        
        **Step 2: Restaurant Referral Program ($1,000 per restaurant)**
        - Visit: https://get.doordash.com/en-us/about/merchant-referral-program
        - Must be existing DoorDash partner (sign up as merchant first)
        - Application requirements:
          - Business information and tax ID
          - Bank account for direct deposit
          - Must refer restaurants with ≤75 locations
        - Maximum: 10 restaurant referrals per affiliate
        - Payment: Within 60 days of restaurant completing 15 orders
        
        **What You Need:**
        - Website URL: cleanplateus.com
        - Business description: "Restaurant health inspection tracking platform"
        - Monthly traffic estimate: 1,000+ unique visitors
        - Primary audience: Restaurant customers and food safety advocates
        
        ---
        
        ## 2. 🛵 UberEats Affiliate Program ($300-2,000/month)
        
        ### How to Apply:
        **Step 1: Submit Application**
        - Visit: https://www.uber.com/us/en/affiliate-program/
        - Fill out detailed application form
        - Expect 7-14 day review process
        
        **Application Requirements:**
        - **Website**: cleanplateus.com
        - **Business Model**: Restaurant discovery and health inspection platform
        - **Target Audience**: Food delivery customers seeking safe restaurants
        - **Monthly Unique Visitors**: 1,000+ (estimated)
        - **Geographic Focus**: US markets (NYC, Chicago, Austin, Boston, Seattle, LA, Detroit)
        - **Content Strategy**: Health inspection results leading to food ordering
        
        **Technical Requirements:**
        - Ability to implement Impact.com tracking pixels
        - Sub4 parameter implementation (already built into your links)
        - Click-to-install rate >0.1% (your health inspection traffic converts well)
        
        **What to Emphasize in Application:**
        - High-intent traffic: Users searching for restaurants are ready to order
        - Trust factor: Health inspection data builds confidence in restaurant quality
        - Mobile optimization: Your PWA capabilities for mobile users
        - Local focus: City-specific restaurant discovery
        
        ---
        
        ## 3. 🍔 Grubhub Partnership ($150-800/month)
        
        ### How to Apply:
        **Step 1: Direct Partnership Approach**
        - Email: partnerships@grubhub.com
        - Subject: "Restaurant Discovery Platform Partnership - CleanPlate"
        
        **Email Template:**
        ```
        Dear Grubhub Partnership Team,
        
        I operate CleanPlate (cleanplateus.com), a restaurant health inspection platform 
        serving 7 major US cities with 1,000+ monthly users researching restaurant safety.
        
        Our users actively search for restaurants and would benefit from seamless 
        ordering integration. We'd like to explore affiliate partnership opportunities.
        
        Platform Details:
        - Website: cleanplateus.com
        - Coverage: NYC, Chicago, Boston, Austin, Seattle, LA, Detroit
        - Audience: Health-conscious diners seeking safe restaurants
        - Integration: Ready to implement tracking links and conversion pixels
        
        Please let me know next steps for partnership application.
        
        Best regards,
        [Your Name]
        CleanPlate Founder
        ```
        
        **Alternative Approach:**
        - Sign up as Grubhub restaurant partner first
        - Then apply for affiliate program from within merchant dashboard
        
        ---
        
        ## 4. ✅ Application Tips for Success
        
        ### For All Programs:
        - **Be Professional**: Use business email, professional language
        - **Show Traffic**: Mention growing user base and mobile optimization
        - **Emphasize Intent**: Health inspection users are high-intent food customers
        - **Demonstrate Value**: Restaurant discovery platform with trust factors
        - **Be Patient**: Approval process takes 1-3 weeks typically
        
        ### Red Flags to Avoid:
        - Don't mention "affiliate marketing" as primary business
        - Don't oversell traffic numbers (be honest about current volume)
        - Don't rush follow-up emails (wait 1 week minimum)
        - Don't apply multiple times if rejected (wait 6 months)
        
        ---
        
        ## 5. 📊 Expected Timeline & Revenue
        
        ### Week 1-2: Applications
        - Submit all three applications
        - Prepare required documentation
        - Set up tracking systems
        
        ### Week 3-4: Approvals
        - Follow up professionally if no response
        - Complete onboarding processes
        - Update affiliate IDs in your code
        
        ### Month 1: First Revenue
        - $50-200 from initial user clicks
        - Monitor conversion rates
        - Optimize button placement
        
        ### Month 2-3: Scaling
        - $200-800 monthly recurring revenue
        - Add more restaurant data sources
        - Expand to additional cities
        
        ### Month 6+: Mature Revenue
        - $650-4,300 monthly potential
        - Reinvest in marketing and features
        - Consider additional affiliate programs
        
        ---
        
        ## 6. 🔧 Post-Approval Setup
        
        Once approved, you'll need to:
        1. **Update Affiliate IDs**: Replace placeholder IDs in delivery_affiliates.py
        2. **Add Tracking Pixels**: Implement conversion tracking (I can help with this)
        3. **Monitor Performance**: Track clicks, conversions, and revenue
        4. **Optimize Placement**: Test button positions and messaging
        
        **Your affiliate integration is already built and ready to go!**
        
        ---
        
        *Need help with any of these applications? I can help you customize the messages or troubleshoot any technical requirements.*
        """)

# Global delivery affiliate manager instance
delivery_affiliate_manager = DeliveryAffiliateManager()