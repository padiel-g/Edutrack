"""add class registers for attendance locking

Revision ID: f0d4a91e7c83
Revises: e82f1b6d4a20
Create Date: 2026-06-08

"""
import sqlalchemy as sa
from alembic import op


revision = "f0d4a91e7c83"
down_revision = "a04b3d8f6c52"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "class_registers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("classes.id"), nullable=False, index=True),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teachers.id"), nullable=False, index=True),
        sa.Column("date", sa.Date(), nullable=False, index=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.UniqueConstraint("class_id", "date", name="uq_register_class_date"),
    )


def downgrade():
    op.drop_table("class_registers")
