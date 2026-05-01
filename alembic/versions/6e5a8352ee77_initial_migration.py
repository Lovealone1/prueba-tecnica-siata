"""Initial migration

Revision ID: 6e5a8352ee77
Revises: 
Create Date: 2026-04-30 19:04:56.415411

"""
from typing import Sequence, Union
import os

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e5a8352ee77'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def execute_sql_file(file_path: str) -> None:
    with open(file_path, 'r') as f:
        sql = f.read()
    
    statements = [s.strip() for s in sql.split(';') if s.strip()]
    for statement in statements:
        op.execute(sa.text(statement))


def upgrade() -> None:
    """Upgrade schema."""
    # Execute raw SQL upgrade script
    sql_path = os.path.join(os.path.dirname(__file__), f'{revision}_create_users_table_up.sql')
    execute_sql_file(sql_path)


def downgrade() -> None:
    """Downgrade schema."""
    # Execute raw SQL downgrade script
    sql_path = os.path.join(os.path.dirname(__file__), f'{revision}_create_users_table_down.sql')
    execute_sql_file(sql_path)
