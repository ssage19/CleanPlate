import streamlit as st
import random

class AdManager:
    """
    Comprehensive ad revenue system for CleanPlate restaurant health inspection app
    """
    
    def __init__(self):
        self.ad_networks = {
            'google_adsense': {
                'name': 'Google AdSense',
                'setup_url': 'https://www.google.com/adsense/',
                'revenue_share': '68%', # Google pays 68% to publishers
                'best_for': 'General display ads, high fill rates'
            },
            'media_net': {
                'name': 'Media.net',
                'setup_url': 'https://www.media.net/',
                'revenue_share': '70%',
                'best_for': 'Contextual ads, Yahoo/Bing network'
            },
            'restaurant_specific': {
                'name': 'Restaurant Industry Ads',
                'partners': ['Grubhub', 'DoorDash', 'OpenTable', 'Yelp'],
                'revenue_type': 'CPC/CPA',
                'best_for': 'Higher rates for restaurant-related content'
            }
        }
    
    def display_banner_ad(self, position="top"):
        """Display banner advertisement"""
        ad_html = f"""
        <div style="
            background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%);
            border: 2px solid rgba(212, 175, 55, 0.3);
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
            text-align: center;
            position: relative;
        ">
            <div style="
                color: #e2e8f0;
                font-size: 0.8rem;
                position: absolute;
                top: 5px;
                left: 10px;
            ">Advertisement</div>
            
            <div id="ad-{position}" style="
                min-height: 90px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: rgba(45, 55, 72, 0.5);
                border-radius: 8px;
                margin-top: 15px;
            ">
                <!-- Google AdSense code will go here -->
                <div style="color: #a0aec0; font-size: 0.9rem;">
                    Ad Space - Revenue Generating Zone
                </div>
            </div>
        </div>
        """
        st.markdown(ad_html, unsafe_allow_html=True)
    
    def display_restaurant_affiliate_ad(self, restaurant_name=None):
        """Display restaurant-specific affiliate ads"""
        affiliate_services = [
            {
                'name': 'Order on DoorDash',
                'color': '#ff3008',
                'description': 'Get delivery from this restaurant',
                'commission': '$2-5 per order'
            },
            {
                'name': 'Reserve on OpenTable',
                'color': '#da3743',
                'description': 'Book a table now',
                'commission': '$1-3 per reservation'
            },
            {
                'name': 'Rate on Yelp',
                'color': '#d32323',
                'description': 'Share your experience',
                'commission': 'Brand partnership revenue'
            }
        ]
        
        selected_service = random.choice(affiliate_services)
        
        ad_html = f"""
        <div style="
            background: linear-gradient(135deg, {selected_service['color']}15 0%, {selected_service['color']}10 100%);
            border: 1px solid {selected_service['color']}40;
            border-radius: 10px;
            padding: 15px;
            margin: 15px 0;
            cursor: pointer;
            transition: transform 0.2s;
        " onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
            <div style="
                display: flex;
                align-items: center;
                justify-content: space-between;
            ">
                <div>
                    <div style="
                        color: #ffffff;
                        font-weight: 600;
                        font-size: 1rem;
                        margin-bottom: 5px;
                    ">{selected_service['name']}</div>
                    <div style="
                        color: #e2e8f0;
                        font-size: 0.85rem;
                    ">{selected_service['description']}</div>
                </div>
                <div style="
                    background: {selected_service['color']};
                    color: white;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 0.9rem;
                ">Click Here</div>
            </div>
        </div>
        """
        st.markdown(ad_html, unsafe_allow_html=True)
    
    def display_sponsored_restaurant(self):
        """Display sponsored restaurant promotion"""
        sponsored_html = """
        <div style="
            background: linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(212, 175, 55, 0.05) 100%);
            border: 2px solid rgba(212, 175, 55, 0.4);
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
        ">
            <div style="
                color: #d4af37;
                font-size: 0.8rem;
                font-weight: 600;
                margin-bottom: 10px;
            ">🌟 SPONSORED RESTAURANT</div>
            
            <div style="
                color: #ffffff;
                font-size: 1.1rem;
                font-weight: 600;
                margin-bottom: 8px;
            ">Premium Restaurant Spotlight</div>
            
            <div style="
                color: #e2e8f0;
                font-size: 0.9rem;
                line-height: 1.4;
            ">Grade A establishments can promote their health inspection excellence here.<br>
            <strong>Contact us for sponsored placement opportunities.</strong></div>
        </div>
        """
        st.markdown(sponsored_html, unsafe_allow_html=True)
    
    def get_revenue_setup_guide(self):
        """Return setup guide for ad revenue"""
        return {
            'immediate_setup': [
                '1. Sign up for Google AdSense (most important)',
                '2. Add AdSense code to app deployment',
                '3. Set up restaurant affiliate partnerships',
                '4. Create sponsored restaurant tier pricing'
            ],
            'expected_revenue': {
                'display_ads': '$1-5 per 1,000 views',
                'affiliate_commissions': '$1-5 per conversion',
                'sponsored_listings': '$50-200 per restaurant per month',
                'premium_placements': '$20-100 per restaurant per week'
            },
            'optimization_tips': [
                'Target food/restaurant keywords for higher ad rates',
                'Place ads strategically without disrupting user experience',
                'Partner with local restaurant delivery services',
                'Offer health inspection certificate verification services'
            ]
        }

# Global ad manager instance
ad_manager = AdManager()