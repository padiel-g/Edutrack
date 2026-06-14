"""add account security state

Revision ID: 8e0f2a4b6c53
Revises: 7d9e1f3a5b42
Create Date: 2026-06-14
"""
from alembic import op
import sqlalchemy as sa


revision = "8e0f2a4b6c53"
down_revision = "7d9e1f3a5b42"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("locked_until", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))
        batch.create_index("ix_users_locked_until", ["locked_until"])

    with op.batch_alter_table("students") as batch:
        batch.add_column(sa.Column("parent_must_change_password", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch.add_column(sa.Column("parent_failed_login_attempts", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("parent_locked_until", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("parent_token_version", sa.Integer(), nullable=False, server_default="0"))
        batch.create_index("ix_students_parent_locked_until", ["parent_locked_until"])


def downgrade():
    with op.batch_alter_table("students") as batch:
        batch.drop_index("ix_students_parent_locked_until")
        batch.drop_column("parent_token_version")
        batch.drop_column("parent_locked_until")
        batch.drop_column("parent_failed_login_attempts")
        batch.drop_column("parent_must_change_password")

    with op.batch_alter_table("users") as batch:
        batch.drop_index("ix_users_locked_until")
        batch.drop_column("token_version")
        batch.drop_column("locked_until")
        batch.drop_column("failed_login_attempts")
