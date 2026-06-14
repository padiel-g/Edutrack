"""add manual payment term

Revision ID: 6c8d0e2f4a31
Revises: 5b7c9d1e3f20
Create Date: 2026-06-13
"""
from alembic import op
import sqlalchemy as sa


revision = "6c8d0e2f4a31"
down_revision = "5b7c9d1e3f20"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("payments") as batch:
        batch.add_column(sa.Column("term_name", sa.String(length=80), nullable=True))
        batch.create_index("ix_payments_term_name", ["term_name"])


def downgrade():
    with op.batch_alter_table("payments") as batch:
        batch.drop_index("ix_payments_term_name")
        batch.drop_column("term_name")
