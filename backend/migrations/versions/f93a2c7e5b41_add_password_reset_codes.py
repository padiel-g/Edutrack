"""add password reset codes

Revision ID: f93a2c7e5b41
Revises: e82f1b6d4a20
Create Date: 2026-06-06

"""
from alembic import op
import sqlalchemy as sa


revision = "f93a2c7e5b41"
down_revision = "e82f1b6d4a20"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "password_reset_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("reset_token_hash", sa.String(length=255), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("reset_token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_password_reset_codes_user_id", "password_reset_codes", ["user_id"])
    op.create_index("ix_password_reset_codes_reset_token_hash", "password_reset_codes", ["reset_token_hash"])
    op.create_index("ix_password_reset_codes_expires_at", "password_reset_codes", ["expires_at"])
    op.create_index("ix_password_reset_codes_created_at", "password_reset_codes", ["created_at"])


def downgrade():
    op.drop_table("password_reset_codes")
