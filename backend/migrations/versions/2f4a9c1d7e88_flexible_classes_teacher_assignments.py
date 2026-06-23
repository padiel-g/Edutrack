"""flexible classes and teacher assignments

Revision ID: 2f4a9c1d7e88
Revises: f93a2c7e5b41
Create Date: 2026-06-18

"""
from alembic import op
import sqlalchemy as sa


revision = "2f4a9c1d7e88"
down_revision = "f93a2c7e5b41"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE classes ALTER COLUMN grade_level TYPE VARCHAR(80) USING grade_level::text")
    op.add_column("classes", sa.Column("stream", sa.String(length=80), nullable=True))
    op.add_column("classes", sa.Column("academic_year_id", sa.Integer(), nullable=True))
    op.create_index("ix_classes_stream", "classes", ["stream"])
    op.create_index("ix_classes_academic_year_id", "classes", ["academic_year_id"])
    op.create_foreign_key("fk_classes_academic_year_id_academic_years", "classes", "academic_years", ["academic_year_id"], ["id"])
    op.execute(
        """
        UPDATE classes
        SET academic_year_id = COALESCE(
            (SELECT id FROM academic_years WHERE is_current = true ORDER BY id DESC LIMIT 1),
            (SELECT id FROM academic_years ORDER BY start_date DESC, id DESC LIMIT 1)
        )
        WHERE academic_year_id IS NULL
        """
    )
    op.execute("ALTER TABLE classes DROP CONSTRAINT IF EXISTS classes_name_key")
    op.create_unique_constraint("uq_class_name_academic_year", "classes", ["name", "academic_year_id"])

    op.execute("ALTER TABLE teacher_subjects DROP CONSTRAINT IF EXISTS uq_teacher_subject_class")
    op.add_column("teacher_subjects", sa.Column("academic_year_id", sa.Integer(), nullable=True))
    op.add_column("teacher_subjects", sa.Column("term_id", sa.Integer(), nullable=True))
    op.add_column("teacher_subjects", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("teacher_subjects", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.execute("UPDATE teacher_subjects SET created_at = now(), updated_at = now() WHERE created_at IS NULL")
    op.alter_column("teacher_subjects", "created_at", nullable=False)
    op.alter_column("teacher_subjects", "updated_at", nullable=False)
    op.execute(
        """
        UPDATE teacher_subjects ts
        SET academic_year_id = c.academic_year_id
        FROM classes c
        WHERE ts.class_id = c.id AND ts.academic_year_id IS NULL
        """
    )
    op.create_index("ix_teacher_subjects_academic_year_id", "teacher_subjects", ["academic_year_id"])
    op.create_index("ix_teacher_subjects_term_id", "teacher_subjects", ["term_id"])
    op.create_foreign_key("fk_teacher_subjects_academic_year_id_academic_years", "teacher_subjects", "academic_years", ["academic_year_id"], ["id"])
    op.create_foreign_key("fk_teacher_subjects_term_id_terms", "teacher_subjects", "terms", ["term_id"], ["id"])
    op.create_unique_constraint("uq_teacher_subject_class_year", "teacher_subjects", ["teacher_id", "subject_id", "class_id", "academic_year_id"])


def downgrade():
    op.drop_constraint("uq_teacher_subject_class_year", "teacher_subjects", type_="unique")
    op.drop_constraint("fk_teacher_subjects_term_id_terms", "teacher_subjects", type_="foreignkey")
    op.drop_constraint("fk_teacher_subjects_academic_year_id_academic_years", "teacher_subjects", type_="foreignkey")
    op.drop_index("ix_teacher_subjects_term_id", table_name="teacher_subjects")
    op.drop_index("ix_teacher_subjects_academic_year_id", table_name="teacher_subjects")
    op.drop_column("teacher_subjects", "updated_at")
    op.drop_column("teacher_subjects", "created_at")
    op.drop_column("teacher_subjects", "term_id")
    op.drop_column("teacher_subjects", "academic_year_id")
    op.create_unique_constraint("uq_teacher_subject_class", "teacher_subjects", ["teacher_id", "subject_id", "class_id"])

    op.drop_constraint("uq_class_name_academic_year", "classes", type_="unique")
    op.drop_constraint("fk_classes_academic_year_id_academic_years", "classes", type_="foreignkey")
    op.drop_index("ix_classes_academic_year_id", table_name="classes")
    op.drop_index("ix_classes_stream", table_name="classes")
    op.drop_column("classes", "academic_year_id")
    op.drop_column("classes", "stream")
    op.execute("ALTER TABLE classes ALTER COLUMN grade_level TYPE INTEGER USING NULLIF(regexp_replace(grade_level, '[^0-9]', '', 'g'), '')::integer")
    op.create_unique_constraint("classes_name_key", "classes", ["name"])
