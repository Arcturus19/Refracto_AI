"""
Database initialization script for Patient Service
Run this to create the database tables
"""

from database import Base, engine
from models import Patient

def init_db():
    """Create all database tables"""
    print("Creating patient database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Patient database tables created successfully!")

if __name__ == "__main__":
    init_db()
