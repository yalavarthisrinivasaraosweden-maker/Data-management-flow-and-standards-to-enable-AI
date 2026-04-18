"""
Migration script for version control system
Creates version control tables in the database
"""

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os

# Import version control models to ensure tables are defined
from version_control import Base, DataVersion, VersionTag
from am_data_pipeline_postgres import DATABASE_URL

def run_version_control_migration():
    """Create version control tables"""
    try:
        engine = create_engine(DATABASE_URL)
        
        print("=" * 60)
        print("Version Control System Migration")
        print("=" * 60)
        
        # Create tables
        print("\nCreating version control tables...")
        Base.metadata.create_all(bind=engine)
        print("✓ Tables created successfully")
        
        # Verify tables exist
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('data_versions', 'version_tags')
            """))
            tables = [row[0] for row in result]
            
            if 'data_versions' in tables:
                print("✓ data_versions table exists")
            if 'version_tags' in tables:
                print("✓ version_tags table exists")
            
            # Check indexes
            result = conn.execute(text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE schemaname = 'public'
                AND tablename IN ('data_versions', 'version_tags')
            """))
            indexes = [row[0] for row in result]
            print(f"✓ Created {len(indexes)} indexes")
        
        print("\n" + "=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        
    except SQLAlchemyError as e:
        print(f"\n✗ Migration error: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise

if __name__ == "__main__":
    run_version_control_migration()
