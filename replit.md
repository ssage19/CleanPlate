# CleanPlate - Restaurant Health Inspection App

## Overview

CleanPlate is a comprehensive restaurant health inspection app built with Streamlit that aggregates health inspection data from multiple jurisdictions (NYC, Chicago, and others). The application provides users with real-time access to restaurant health grades, inspection details, violation records, and user reviews. The platform features a sophisticated revenue system through display advertising, affiliate partnerships, and sponsored restaurant listings.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit with custom CSS theming
- **Design Pattern**: Single-page application with dynamic content rendering
- **Styling**: Custom CSS with restaurant-themed gradients, typography (Inter/Playfair Display fonts), and responsive design
- **User Interface**: Wide layout with collapsible sidebar, sophisticated color scheme using dark backgrounds with gold accents

### Backend Architecture
- **Data Layer**: SQLAlchemy ORM with PostgreSQL database
- **API Integration**: Multi-jurisdiction health inspection data fetching through government APIs
- **Session Management**: Streamlit session state for user data persistence
- **Caching**: Streamlit resource caching for database initialization and API clients

### Data Storage Solutions
- **Primary Database**: PostgreSQL with connection pooling (pool_size=10, max_overflow=20)
- **Schema Design**: 
  - Restaurants table (id, name, address, cuisine_type, grade, score, inspection_date, etc.)
  - UserReviews table with foreign key relationship to restaurants
- **Connection Management**: SQLAlchemy engine with pool pre-ping validation and 1-hour connection recycling

### Authentication and Authorization
- **Current State**: No formal authentication system implemented
- **User Data**: Anonymous user reviews stored in session state and database
- **Access Control**: Public access to all restaurant data and inspection records

### Revenue System
- **Advertising Framework**: AdManager class supporting multiple ad networks
- **Revenue Streams**: 
  - Google AdSense integration (68% revenue share)
  - Media.net contextual advertising (70% revenue share)
  - Restaurant-specific affiliate programs (CPC/CPA model)
- **Monetization Strategy**: Banner ads, sponsored listings, affiliate commissions from food delivery platforms

## External Dependencies

### Government Data APIs
- **NYC Open Data**: New York City health inspection data (data.cityofnewyork.us)
- **Chicago Data Portal**: Chicago health inspection records (data.cityofchicago.org)
- **Multi-jurisdiction Support**: Extensible API client supporting different grading systems (letter grades, pass/fail)

### Third-party Services
- **Google AdSense**: Primary advertising revenue stream
- **Media.net**: Secondary ad network for contextual advertising
- **Restaurant Affiliate Partners**: 
  - DoorDash (order commissions)
  - OpenTable (reservation commissions)
  - Grubhub (delivery partnerships)
  - Yelp (restaurant data integration)

### Development Dependencies
- **Streamlit**: Web application framework
- **SQLAlchemy**: Database ORM and connection management
- **psycopg2**: PostgreSQL database adapter
- **pandas**: Data manipulation and analysis
- **requests**: HTTP client for API interactions
- **plotly**: Data visualization (referenced in legacy code)

### Database Infrastructure
- **PostgreSQL**: Primary database requiring DATABASE_URL environment variable
- **Connection Pooling**: Built-in SQLAlchemy connection management
- **Data Persistence**: Restaurant records, user reviews, inspection histories