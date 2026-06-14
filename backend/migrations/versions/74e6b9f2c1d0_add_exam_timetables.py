"""add exam timetables

Revision ID: 74e6b9f2c1d0
Revises: 31af743c9e02
Create Date: 2026-06-06

"""
from alembic import op
import sqlalchemy as sa


revision = "74e6b9f2c1d0"
down_revision = "31af743c9e02"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "exam_timetables",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("exam_date", sa.Date(), nullable=False),
        sa.Column("class_type", sa.String(length=80), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("venue", sa.String(length=120), nullable=True),
        sa.Column("paper", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exam_timetables_class_type"), "exam_timetables", ["class_type"], unique=False)
    op.create_index(op.f("ix_exam_timetables_exam_date"), "exam_timetables", ["exam_date"], unique=False)
    op.create_index(op.f("ix_exam_timetables_subject_id"), "exam_timetables", ["subject_id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_exam_timetables_subject_id"), table_name="exam_timetables")
    op.drop_index(op.f("ix_exam_timetables_exam_date"), table_name="exam_timetables")
    op.drop_index(op.f("ix_exam_timetables_class_type"), table_name="exam_timetables")
    op.drop_table("exam_timetables")
