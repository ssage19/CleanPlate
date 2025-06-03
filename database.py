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
    """Save or update restaurant data in database using raw SQL for upsert"""
    try:
        # Use raw SQL connection for UPSERT operation
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Create restaurant table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS restaurants (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                address TEXT,
                cuisine_type VARCHAR,
                grade VARCHAR,
                score INTEGER,
                inspection_date VARCHAR,
                boro VARCHAR,
                phone VARCHAR,
                inspection_type VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Upsert restaurant data
        cursor.execute("""
            INSERT INTO restaurants (id, name, address, cuisine_type, grade, score, inspection_date, boro, phone, inspection_type)
            VALUES (%(id)s, %(name)s, %(address)s, %(cuisine_type)s, %(grade)s, %(score)s, %(inspection_date)s, %(boro)s, %(phone)s, %(inspection_type)s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                address = EXCLUDED.address,
                cuisine_type = EXCLUDED.cuisine_type,
                grade = EXCLUDED.grade,
                score = EXCLUDED.score,
                inspection_date = EXCLUDED.inspection_date,
                boro = EXCLUDED.boro,
                phone = EXCLUDED.phone,
                inspection_type = EXCLUDED.inspection_type,
                updated_at = CURRENT_TIMESTAMP
        """, restaurant_data)
        
        # Handle violations if provided
        if violations_data:
            # Create violations table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS violations (
                    id SERIAL PRIMARY KEY,
                    restaurant_id VARCHAR REFERENCES restaurants(id),
                    violation_code VARCHAR,
                    violation_description TEXT,
                    critical_flag VARCHAR,
                    inspection_date VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Clear old violations and add new ones
            cursor.execute("DELETE FROM violations WHERE restaurant_id = %s", (restaurant_data['id'],))
            
            for violation_text in violations_data:
                if violation_text and violation_text != "No violations recorded":
                    cursor.execute("""
                        INSERT INTO violations (restaurant_id, violation_description, inspection_date)
                        VALUES (%s, %s, %s)
                    """, (restaurant_data['id'], violation_text, restaurant_data.get('inspection_date')))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Failed to save restaurant data: {str(e)}")
        return False

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
    try:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Create user_reviews table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_reviews (
                id SERIAL PRIMARY KEY,
                restaurant_id VARCHAR REFERENCES restaurants(id),
                rating INTEGER NOT NULL,
                comment TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert review
        cursor.execute("""
            INSERT INTO user_reviews (restaurant_id, rating, comment)
            VALUES (%s, %s, %s)
        """, (restaurant_id, rating, comment))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        st.error(f"Failed to save review: {str(e)}")
        return False

def get_restaurant_reviews(restaurant_id):
    """Get all reviews for a restaurant"""
    try:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT rating, comment, created_at 
            FROM user_reviews 
            WHERE restaurant_id = %s 
            ORDER BY created_at DESC
        """, (restaurant_id,))
        
        reviews = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convert to simple objects
        review_objects = []
        for rating, comment, created_at in reviews:
            review_obj = type('Review', (), {
                'rating': rating,
                'comment': comment,
                'created_at': created_at
            })()
            review_objects.append(review_obj)
        
        return review_objects
    except Exception as e:
        st.error(f"Failed to get reviews: {str(e)}")
        return []

def calculate_db_average_rating(restaurant_id):
    """Calculate average rating from database"""
    try:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT AVG(rating) FROM user_reviews WHERE restaurant_id = %s
        """, (restaurant_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result and result[0] is not None:
            return float(result[0])
        return 0
        
    except Exception as e:
        st.error(f"Failed to calculate average rating: {str(e)}")
        return 0

def get_restaurant_violations(restaurant_id):
    """Get violations for a restaurant from database"""
    try:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT violation_description FROM violations WHERE restaurant_id = %s
        """, (restaurant_id,))
        
        violations = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return [v[0] for v in violations if v[0]]
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