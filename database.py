import os
import psycopg2
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import streamlit as st

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(Text)
    cuisine_type = Column(String)
    grade = Column(String)
    score = Column(Integer)
    inspection_date = Column(String)
    boro = Column(String)
    phone = Column(String)
    inspection_type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to reviews
    reviews = relationship("UserReview", back_populates="restaurant")

class UserReview(Base):
    __tablename__ = "user_reviews"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(String, ForeignKey("restaurants.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to restaurant
    restaurant = relationship("Restaurant", back_populates="reviews")

class Violation(Base):
    __tablename__ = "violations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_id = Column(String, ForeignKey("restaurants.id"), nullable=False)
    violation_code = Column(String)
    violation_description = Column(Text)
    critical_flag = Column(String)
    inspection_date = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Database functions
def init_database():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        return True
    except Exception as e:
        st.error(f"Failed to initialize database: {str(e)}")
        return False

def get_db_session():
    """Get database session"""
    return SessionLocal()

def save_restaurant_to_db(restaurant_data, violations_data=None):
    """Save or update restaurant data in database"""
    session = None
    try:
        session = get_db_session()
        
        # Check if restaurant exists
        existing = session.query(Restaurant).filter(Restaurant.id == restaurant_data['id']).first()
        
        if existing:
            # Update existing restaurant
            for key, value in restaurant_data.items():
                if hasattr(existing, key) and key not in ['updated_at', 'created_at']:
                    setattr(existing, key, value)
        else:
            # Create new restaurant
            restaurant = Restaurant(**restaurant_data)
            session.add(restaurant)
        
        # Save violations if provided
        if violations_data:
            # Remove old violations for this restaurant
            session.query(Violation).filter(Violation.restaurant_id == restaurant_data['id']).delete()
            
            # Add new violations
            for violation_text in violations_data:
                if violation_text and violation_text != "No violations recorded":
                    violation = Violation(
                        restaurant_id=restaurant_data['id'],
                        violation_description=violation_text,
                        inspection_date=restaurant_data.get('inspection_date')
                    )
                    session.add(violation)
        
        session.commit()
        return True
        
    except Exception as e:
        if session:
            session.rollback()
        st.error(f"Failed to save restaurant data: {str(e)}")
        return False
    finally:
        if session:
            session.close()

def get_restaurant_from_db(restaurant_id):
    """Get restaurant data from database"""
    try:
        session = get_db_session()
        restaurant = session.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        session.close()
        return restaurant
    except Exception as e:
        st.error(f"Failed to get restaurant data: {str(e)}")
        return None

def save_user_review(restaurant_id, rating, comment):
    """Save user review to database"""
    session = None
    try:
        session = get_db_session()
        
        review = UserReview(
            restaurant_id=restaurant_id,
            rating=rating,
            comment=comment
        )
        
        session.add(review)
        session.commit()
        return True
        
    except Exception as e:
        if session:
            session.rollback()
        st.error(f"Failed to save review: {str(e)}")
        return False
    finally:
        if session:
            session.close()

def get_restaurant_reviews(restaurant_id):
    """Get all reviews for a restaurant"""
    try:
        session = get_db_session()
        reviews = session.query(UserReview).filter(
            UserReview.restaurant_id == restaurant_id
        ).order_by(UserReview.created_at.desc()).all()
        session.close()
        return reviews
    except Exception as e:
        st.error(f"Failed to get reviews: {str(e)}")
        return []

def calculate_db_average_rating(restaurant_id):
    """Calculate average rating from database"""
    try:
        session = get_db_session()
        reviews = session.query(UserReview).filter(UserReview.restaurant_id == restaurant_id).all()
        session.close()
        
        if not reviews:
            return 0
        
        total_rating = sum(review.rating for review in reviews)
        return total_rating / len(reviews)
        
    except Exception as e:
        st.error(f"Failed to calculate average rating: {str(e)}")
        return 0

def get_restaurant_violations(restaurant_id):
    """Get violations for a restaurant from database"""
    try:
        session = get_db_session()
        violations = session.query(Violation).filter(
            Violation.restaurant_id == restaurant_id
        ).all()
        session.close()
        return [v.violation_description for v in violations if v.violation_description]
    except Exception as e:
        st.error(f"Failed to get violations: {str(e)}")
        return []

def search_restaurants_in_db(search_term=None, location=None, grades=None, limit=100):
    """Search restaurants in database"""
    try:
        session = get_db_session()
        query = session.query(Restaurant)
        
        if search_term:
            query = query.filter(Restaurant.name.ilike(f'%{search_term}%'))
        
        if location and location != "All":
            query = query.filter(Restaurant.boro == location.upper())
        
        if grades:
            query = query.filter(Restaurant.grade.in_(grades))
        
        restaurants = query.limit(limit).all()
        session.close()
        return restaurants
        
    except Exception as e:
        st.error(f"Failed to search restaurants: {str(e)}")
        return []

def get_db_statistics():
    """Get database statistics"""
    try:
        session = get_db_session()
        
        total_restaurants = session.query(Restaurant).count()
        total_reviews = session.query(UserReview).count()
        grade_a_count = session.query(Restaurant).filter(Restaurant.grade == 'A').count()
        
        session.close()
        
        return {
            'total_restaurants': total_restaurants,
            'total_reviews': total_reviews,
            'grade_a_count': grade_a_count
        }
        
    except Exception as e:
        st.error(f"Failed to get statistics: {str(e)}")
        return {
            'total_restaurants': 0,
            'total_reviews': 0,
            'grade_a_count': 0
        }