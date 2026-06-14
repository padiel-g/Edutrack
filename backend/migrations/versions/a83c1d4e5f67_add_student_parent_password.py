"""add student parent password

Revision ID: a83c1d4e5f67
Revises: 74e6b9f2c1d0
Create Date: 2026-06-06

"""
from alembic import op
import sqlalchemy as sa
from werkzeug.security import generate_password_hash


revision = "a83c1d4e5f67"
down_revision = "74e6b9f2c1d0"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("students", sa.Column("parent_password_hash", sa.String(length=255), nullable=True))
    students = sa.table(
        "students",
        sa.column("id", sa.Integer()),
        sa.column("parent_password_hash", sa.String(length=255)),
    )
    op.execute(students.update().values(parent_password_hash=generate_password_hash("Edutrack")))


def downgrade():
    op.drop_column("students", "parent_password_hash")
