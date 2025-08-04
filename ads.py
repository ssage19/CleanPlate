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
        """Display Google AdSense banner advertisement"""
        ad_html = """
        <div style="
            background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
            border: 1px solid rgba(212, 175, 55, 0.2);
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            text-align: center;
            position: relative;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            width: 100%;
            box-sizing: border-box;
            max-width: 100%;
        ">
            <div style="
                color: #a0aec0;
                font-size: 0.7rem;
                position: absolute;
                top: 3px;
                left: 8px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            ">Advertisement</div>
            
            <div id="ad-""" + position + """" style="
                min-height: 280px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: rgba(26, 32, 44, 0.6);
                border-radius: 6px;
                margin-top: 12px;
                width: 100%;
                box-sizing: border-box;
                padding: 10px;
            ">
                <!-- Google AdSense Code -->
                <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3394301342758377"
                     crossorigin="anonymous"></script>
                <!-- CleanPlate Banner Ad -->
                <ins class="adsbygoogle"
                     style="display:block"
                     data-ad-client="ca-pub-3394301342758377"
                     data-ad-slot="1234567890"
                     data-ad-format="auto"
                     data-full-width-responsive="true"></ins>
                <script>
                     (adsbygoogle = window.adsbygoogle || []).push({});
                </script>
            </div>
        </div>
        """
        st.markdown(ad_html, unsafe_allow_html=True)
    
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