"""create_logistics_nodes

Revision ID: ead00eb76804
Revises: 3014e162f71a
Create Date: 2026-04-30 23:58:21.283210

"""
from typing import Sequence, Union

import os

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ead00eb76804'
down_revision: Union[str, Sequence[str], None] = '3014e162f71a'
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
    sql_path = os.path.join(os.path.dirname(__file__), f'{revision}_create_logistics_nodes_up.sql')
    execute_sql_file(sql_path)


def downgrade() -> None:
    """Downgrade schema."""
    sql_path = os.path.join(os.path.dirname(__file__), f'{revision}_create_logistics_nodes_down.sql')
    execute_sql_file(sql_path)
