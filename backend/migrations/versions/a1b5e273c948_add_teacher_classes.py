"""add teacher_classes association for class assignments independent of subjects

Revision ID: a1b5e273c948
Revises: f0d4a91e7c83
Create Date: 2026-06-08

"""
import sqlalchemy as sa
from alembic import op


revision = "a1b5e273c948"
down_revision = "f0d4a91e7c83"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "teacher_classes",
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teachers.id"), primary_key=True),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("classes.id"), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_teacher_classes_teacher_id", "teacher_classes", ["teacher_id"])
    op.create_index("ix_teacher_classes_class_id", "teacher_classes", ["class_id"])

    # Backfill from existing teacher_subjects rows so admins don't lose
    # information already captured under the subjects-per-class scheme.
    op.execute(
        """
        INSERT INTO teacher_classes (teacher_id, class_id)
        SELECT DISTINCT teacher_id, class_id
        FROM teacher_subjects
        WHERE class_id IS NOT NULL
        ON CONFLICT DO NOTHING
        """
    )


def downgrade():
    op.drop_index("ix_teacher_classes_class_id", table_name="teacher_classes")
    op.drop_index("ix_teacher_classes_teacher_id", table_name="teacher_classes")
    op.drop_table("teacher_classes")
