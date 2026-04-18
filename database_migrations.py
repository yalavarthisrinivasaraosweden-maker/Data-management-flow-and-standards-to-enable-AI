"""
Database migration scripts for PostgreSQL
Run this script to set up or migrate the database schema
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/am_data_db"
)

def create_database():
    """Create the database if it doesn't exist"""
    # Connect to postgres database to create the target database
    admin_url = DATABASE_URL.rsplit('/', 1)[0] + '/postgres'
    admin_engine = create_engine(admin_url)
    
    db_name = DATABASE_URL.rsplit('/', 1)[1]
    
    with admin_engine.connect() as conn:
        # Check if database exists
        result = conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        )
        exists = result.fetchone()
        
        if not exists:
            # Terminate existing connections
            conn.execute(text(f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{db_name}' AND pid <> pg_backend_pid()
            """))
            
            # Create database
            conn.execute(text(f"CREATE DATABASE {db_name}"))
            conn.commit()
            print(f"✓ Database '{db_name}' created successfully")
        else:
            print(f"✓ Database '{db_name}' already exists")
    
    admin_engine.dispose()

def run_migrations():
    """Run database migrations"""
    from am_data_pipeline_postgres import Base, engine
    
    try:
        print("Running database migrations...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✓ All tables created successfully")
        
        # Verify tables exist
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            print(f"✓ Tables created: {', '.join(tables)}")
        
        # Verify indexes
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE schemaname = 'public'
            """))
            indexes = [row[0] for row in result]
            print(f"✓ Indexes created: {len(indexes)} indexes")
        
    except SQLAlchemyError as e:
        print(f"✗ Migration error: {e}")
        raise

def verify_connection():
    """Verify database connection"""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0] # type: ignore
            print(f"✓ Connected to PostgreSQL: {version.split(',')[0]}")
        engine.dispose()
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("AM Data Pipeline - Database Migration Script")
    print("=" * 60)
    
    # Verify connection
    if not verify_connection():
        print("\nPlease ensure PostgreSQL is running and DATABASE_URL is correct.")
        print(f"Current DATABASE_URL: {DATABASE_URL}")
        exit(1)
    
    # Create database if needed
    print("\n1. Checking database...")
    create_database()
    
    # Run migrations
    print("\n2. Running migrations...")
    run_migrations()
    
    print("\n" + "=" * 60)
    print("✓ Migration completed successfully!")
    print("=" * 60)
