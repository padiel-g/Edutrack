"""remove teacher date of birth

Revision ID: d71e2a4c9f30
Revises: c4d9a81f2e70
Create Date: 2026-06-06

"""
from alembic import op
import sqlalchemy as sa


revision = "d71e2a4c9f30"
down_revision = "c4d9a81f2e70"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("teachers", "date_of_birth")


def downgrade():
    op.add_column("teachers", sa.Column("date_of_birth", sa.Date(), nullable=True))
