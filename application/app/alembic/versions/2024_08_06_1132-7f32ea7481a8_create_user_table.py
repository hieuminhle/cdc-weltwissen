"""Create user table.

Revision ID: 7f32ea7481a8
Revises:
Create Date: 2024-08-06 11:32:11.387467

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# test comment
# revision identifiers, used by Alembic.
revision: str = '7f32ea7481a8'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cosi_usage",
        sa.Column("oid_hashed", sa.String(64)),
        sa.Column("session_id", sa.String(64), primary_key=True),
        sa.Column("chat_type", sa.String(32)),
        sa.Column("time_stamp", sa.DateTime, server_default=sa.func.now(), primary_key=True),
        sa.Column("num_token_prompt", sa.Integer, nullable=True),
        sa.Column("num_token_response", sa.Integer, nullable=True),
        sa.Column("response_time", sa.Integer),
        sa.PrimaryKeyConstraint("session_id", "time_stamp", name="pk_cosi_usage")
    )


def downgrade() -> None:
    pass
