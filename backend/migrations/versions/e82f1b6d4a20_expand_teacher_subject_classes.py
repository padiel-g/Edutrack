"""expand teacher subject class assignments

Revision ID: e82f1b6d4a20
Revises: d71e2a4c9f30
Create Date: 2026-06-06

"""
from alembic import op


revision = "e82f1b6d4a20"
down_revision = "d71e2a4c9f30"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE teacher_subjects DROP CONSTRAINT teacher_subjects_pkey")
    op.execute("ALTER TABLE teacher_subjects ADD COLUMN id BIGSERIAL PRIMARY KEY")
    op.create_index("ix_teacher_subjects_teacher_id", "teacher_subjects", ["teacher_id"])
    op.create_index("ix_teacher_subjects_subject_id", "teacher_subjects", ["subject_id"])
    op.create_unique_constraint(
        "uq_teacher_subject_class",
        "teacher_subjects",
        ["teacher_id", "subject_id", "class_id"],
    )


def downgrade():
    op.drop_constraint("uq_teacher_subject_class", "teacher_subjects", type_="unique")
    op.drop_index("ix_teacher_subjects_subject_id", table_name="teacher_subjects")
    op.drop_index("ix_teacher_subjects_teacher_id", table_name="teacher_subjects")
    op.drop_constraint("teacher_subjects_pkey", "teacher_subjects", type_="primary")
    op.drop_column("teacher_subjects", "id")
    op.create_primary_key("teacher_subjects_pkey", "teacher_subjects", ["teacher_id", "subject_id"])
