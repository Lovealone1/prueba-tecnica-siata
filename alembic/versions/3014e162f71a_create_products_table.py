"""create_products_table

Revision ID: 3014e162f71a
Revises: a84710b933e3
Create Date: 2026-04-30 23:16:37.210043

"""
from typing import Sequence, Union
import os

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3014e162f71a'
down_revision: Union[str, Sequence[str], None] = 'a84710b933e3'
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
    sql_path = os.path.join(os.path.dirname(__file__), f'{revision}_create_products_table_up.sql')
    execute_sql_file(sql_path)


def downgrade() -> None:
    """Downgrade schema."""
    sql_path = os.path.join(os.path.dirname(__file__), f'{revision}_create_products_table_down.sql')
    execute_sql_file(sql_path)
