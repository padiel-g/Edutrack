"""add student class type

Revision ID: 9d2e8f6b31a4
Revises: 436a3aa98b65
Create Date: 2026-06-06

"""
from alembic import op
import sqlalchemy as sa


revision = "9d2e8f6b31a4"
down_revision = "436a3aa98b65"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("students", sa.Column("class_type", sa.String(length=80), nullable=True))
    op.create_index(op.f("ix_students_class_type"), "students", ["class_type"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_students_class_type"), table_name="students")
    op.drop_column("students", "class_type")
