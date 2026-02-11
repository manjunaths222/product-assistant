"""add_project_summary_fields

Revision ID: add_project_summary_001
Revises: add_project_features_001
Create Date: 2026-02-10 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = 'add_project_summary_001'
down_revision: Union[str, Sequence[str], None] = 'add_project_features_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add project_name, summary, purpose, and tech_stack columns to projects table."""
    # Check if columns already exist
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Get the projects table columns
    projects_columns = [col['name'] for col in inspector.get_columns('projects')]
    
    # Add project_name column if it doesn't exist
    if 'project_name' not in projects_columns:
        op.add_column('projects', sa.Column('project_name', sa.String(length=500), nullable=True))
        print("Added 'project_name' column to projects table")
    else:
        print("Column 'project_name' already exists, skipping")
    
    # Add summary column if it doesn't exist
    if 'summary' not in projects_columns:
        op.add_column('projects', sa.Column('summary', sa.Text(), nullable=True))
        print("Added 'summary' column to projects table")
    else:
        print("Column 'summary' already exists, skipping")
    
    # Add purpose column if it doesn't exist
    if 'purpose' not in projects_columns:
        op.add_column('projects', sa.Column('purpose', sa.Text(), nullable=True))
        print("Added 'purpose' column to projects table")
    else:
        print("Column 'purpose' already exists, skipping")
    
    # Add tech_stack column if it doesn't exist
    if 'tech_stack' not in projects_columns:
        op.add_column('projects', sa.Column('tech_stack', postgresql.JSON(astext_type=sa.Text()), nullable=True))
        print("Added 'tech_stack' column to projects table")
    else:
        print("Column 'tech_stack' already exists, skipping")


def downgrade() -> None:
    """Downgrade schema - remove project_name, summary, purpose, and tech_stack columns from projects table."""
    # Check if columns exist before dropping
    bind = op.get_bind()
    inspector = inspect(bind)
    projects_columns = [col['name'] for col in inspector.get_columns('projects')]
    
    # Drop columns if they exist
    if 'tech_stack' in projects_columns:
        op.drop_column('projects', 'tech_stack')
        print("Dropped 'tech_stack' column from projects table")
    
    if 'purpose' in projects_columns:
        op.drop_column('projects', 'purpose')
        print("Dropped 'purpose' column from projects table")
    
    if 'summary' in projects_columns:
        op.drop_column('projects', 'summary')
        print("Dropped 'summary' column from projects table")
    
    if 'project_name' in projects_columns:
        op.drop_column('projects', 'project_name')
        print("Dropped 'project_name' column from projects table")

