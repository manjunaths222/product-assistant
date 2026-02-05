"""
Database initialization script
Run this to create the database tables
"""

from app.models.database import Base, engine
from app.config import DATABASE_URL

def init_db():
    """Initialize database tables"""
    print(f"Creating database tables...")
    print(f"Database URL: {DATABASE_URL}")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()

