"""add production query indexes

Revision ID: b0f4c2d178a9
Revises: a83c1d4e5f67
Create Date: 2026-06-06

"""
from alembic import op


revision = "b0f4c2d178a9"
down_revision = "a83c1d4e5f67"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_users_created_at", "users", ["created_at"], unique=False)
    op.create_index("ix_students_created_at", "students", ["created_at"], unique=False)
    op.create_index("ix_parents_created_at", "parents", ["created_at"], unique=False)
    op.create_index("ix_teachers_created_at", "teachers", ["created_at"], unique=False)
    op.create_index("ix_invoices_created_at", "invoices", ["created_at"], unique=False)
    op.create_index("ix_report_cards_created_at", "report_cards", ["created_at"], unique=False)


def downgrade():
    op.drop_index("ix_report_cards_created_at", table_name="report_cards")
    op.drop_index("ix_invoices_created_at", table_name="invoices")
    op.drop_index("ix_teachers_created_at", table_name="teachers")
    op.drop_index("ix_parents_created_at", table_name="parents")
    op.drop_index("ix_students_created_at", table_name="students")
    op.drop_index("ix_users_created_at", table_name="users")
