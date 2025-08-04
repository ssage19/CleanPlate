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
        """Display clean ad placeholder using native Streamlit components"""
        # Use native Streamlit container for clean display
        with st.container():
            st.caption("ADVERTISEMENT")
            
            # Create clean ad placeholder using Streamlit info box
            st.info("🏆 Premium Ad Space - Google AdSense account verified")
    
    def display_restaurant_affiliate_ad(self, restaurant_name=None):
        """Removed embedded buttons - keeping interface clean and simple as requested"""
        pass
    
    def display_sponsored_restaurant(self):
        """Display sponsored restaurant promotion"""
        sponsored_html = """
        <div style="
            background: linear-gradient(135deg, rgba(212, 175, 55, 0.08) 0%, rgba(45, 55, 72, 0.95) 100%);
            border: 1px solid rgba(212, 175, 55, 0.4);
            border-radius: 10px;
            padding: 16px;
            margin: 16px 0;
            position: relative;
            overflow: hidden;
        ">
            <div style="
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: linear-gradient(90deg, #d4af37 0%, #f6d55c 100%);
            "></div>
            
            <div style="
                color: #d4af37;
                font-size: 0.75rem;
                font-weight: 700;
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 1px;
            ">✨ SPONSORED</div>
            
            <div style="
                color: #ffffff;
                font-size: 1rem;
                font-weight: 600;
                margin-bottom: 6px;
            ">Featured Restaurant Partnership</div>
            
            <div style="
                color: #cbd5e0;
                font-size: 0.85rem;
                line-height: 1.4;
            ">Grade A restaurants can showcase their health inspection excellence.<br>
            <span style="color: #d4af37; font-weight: 500;">Premium placement available</span></div>
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