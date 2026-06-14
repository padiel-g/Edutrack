"""add report card workflow

Revision ID: 7d9e1f3a5b42
Revises: 6c8d0e2f4a31
Create Date: 2026-06-14
"""
from alembic import op
import sqlalchemy as sa


revision = "7d9e1f3a5b42"
down_revision = "6c8d0e2f4a31"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "student_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("term_id", sa.Integer(), nullable=False),
        sa.Column("academic_year_id", sa.Integer(), nullable=False),
        sa.Column("ca_mark", sa.Numeric(6, 2), nullable=False),
        sa.Column("exam_mark", sa.Numeric(6, 2), nullable=False),
        sa.Column("final_mark", sa.Numeric(6, 2), nullable=False),
        sa.Column("effort_grade", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"]),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"]),
        sa.ForeignKeyConstraint(["term_id"], ["terms.id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "subject_id", "term_id", "academic_year_id", name="uq_student_result_period_subject"),
    )
    for column in ["student_id", "subject_id", "teacher_id", "class_id", "term_id", "academic_year_id"]:
        op.create_index(f"ix_student_results_{column}", "student_results", [column])

    with op.batch_alter_table("report_cards") as batch:
        batch.add_column(sa.Column("class_teacher_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("teacher_comment", sa.Text(), nullable=True))
        batch.add_column(sa.Column("overall_achievement", sa.String(40), nullable=True))
        batch.add_column(sa.Column("attitude_to_learning", sa.String(40), nullable=True))
        batch.add_column(sa.Column("behaviour", sa.String(40), nullable=True))
        batch.add_column(sa.Column("attendance_summary", sa.String(40), nullable=True))
        batch.add_column(sa.Column("targets", sa.Text(), nullable=True))
        batch.add_column(sa.Column("admin_comment", sa.Text(), nullable=True))
        batch.add_column(sa.Column("approved_by_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("approved_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("published_at", sa.DateTime(), nullable=True))
        batch.create_index("ix_report_cards_class_teacher_id", ["class_teacher_id"])
        batch.create_index("ix_report_cards_approved_by_id", ["approved_by_id"])
        batch.create_foreign_key("fk_report_cards_class_teacher_id", "teachers", ["class_teacher_id"], ["id"])
        batch.create_foreign_key("fk_report_cards_approved_by_id", "users", ["approved_by_id"], ["id"])
        batch.create_unique_constraint("uq_report_card_student_period", ["student_id", "term_id", "academic_year_id"])

    op.execute("UPDATE report_cards SET status = INITCAP(COALESCE(status, 'Draft'))")
    op.alter_column(
        "report_cards",
        "status",
        existing_type=sa.String(30),
        nullable=False,
        server_default=sa.text("'Draft'"),
    )

    op.create_table(
        "report_signatures",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("report_id", sa.Integer(), nullable=False),
        sa.Column("admin_id", sa.Integer(), nullable=False),
        sa.Column("signature_image", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["admin_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["report_id"], ["report_cards.id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("report_id"),
    )
    op.create_index("ix_report_signatures_report_id", "report_signatures", ["report_id"], unique=True)
    op.create_index("ix_report_signatures_admin_id", "report_signatures", ["admin_id"])


def downgrade():
    op.drop_index("ix_report_signatures_admin_id", table_name="report_signatures")
    op.drop_index("ix_report_signatures_report_id", table_name="report_signatures")
    op.drop_table("report_signatures")
    with op.batch_alter_table("report_cards") as batch:
        batch.drop_constraint("uq_report_card_student_period", type_="unique")
        batch.drop_constraint("fk_report_cards_approved_by_id", type_="foreignkey")
        batch.drop_constraint("fk_report_cards_class_teacher_id", type_="foreignkey")
        batch.drop_index("ix_report_cards_approved_by_id")
        batch.drop_index("ix_report_cards_class_teacher_id")
        for column in ["published_at", "approved_at", "approved_by_id", "admin_comment", "targets", "attendance_summary", "behaviour", "attitude_to_learning", "overall_achievement", "teacher_comment", "class_teacher_id"]:
            batch.drop_column(column)
    op.drop_table("student_results")
