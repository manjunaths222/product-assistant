"""
Migration script to add repo_path column to projects table
Run this if you have existing data and want to add the repo_path column
"""

from app.models.database import engine
from sqlalchemy import text

def migrate_add_repo_path():
    """Add repo_path column to projects table"""
    print("Adding repo_path column to projects table...")
    
    with engine.connect() as conn:
        try:
            # Check if column already exists
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='projects' AND column_name='repo_path'
            """)
            result = conn.execute(check_query)
            if result.fetchone():
                print("Column 'repo_path' already exists. Skipping migration.")
                return
            
            # Add the column (nullable first, then we'll update and make it NOT NULL)
            alter_query = text("""
                ALTER TABLE projects 
                ADD COLUMN repo_path VARCHAR(1000)
            """)
            conn.execute(alter_query)
            conn.commit()
            
            print("Successfully added repo_path column!")
            
            # Update existing rows with computed repo_path
            from app.config import GIT_REPO_BASE_PATH
            update_query = text(f"""
                UPDATE projects 
                SET repo_path = :base_path || '/' || project_id
                WHERE repo_path IS NULL
            """)
            conn.execute(update_query, {"base_path": GIT_REPO_BASE_PATH})
            conn.commit()
            
            print(f"Updated existing projects with computed repo_path values (using {GIT_REPO_BASE_PATH}).")
            
            # Make the column NOT NULL after updating all rows
            alter_not_null_query = text("""
                ALTER TABLE projects 
                ALTER COLUMN repo_path SET NOT NULL
            """)
            conn.execute(alter_not_null_query)
            conn.commit()
            
            print("Made repo_path column NOT NULL.")
            
        except Exception as e:
            conn.rollback()
            print(f"Error during migration: {str(e)}")
            raise

if __name__ == "__main__":
    migrate_add_repo_path()

