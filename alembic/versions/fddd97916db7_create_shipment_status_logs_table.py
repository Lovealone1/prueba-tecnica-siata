"""create_shipment_status_logs_table

Revision ID: fddd97916db7
Revises: 7d15d38ad794
Create Date: 2026-05-01 10:59:43.768382

"""
from typing import Sequence, Union

import os

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fddd97916db7'
down_revision: Union[str, Sequence[str], None] = '7d15d38ad794'
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
    sql_path = os.path.join(os.path.dirname(__file__), f'{revision}_create_shipment_status_logs_table_up.sql')
    execute_sql_file(sql_path)


def downgrade() -> None:
    """Downgrade schema."""
    sql_path = os.path.join(os.path.dirname(__file__), f'{revision}_create_shipment_status_logs_table_down.sql')
    execute_sql_file(sql_path)
