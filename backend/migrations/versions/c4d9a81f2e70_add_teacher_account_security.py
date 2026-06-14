"""add teacher account security

Revision ID: c4d9a81f2e70
Revises: b0f4c2d178a9
Create Date: 2026-06-06

"""
from alembic import op
import sqlalchemy as sa


revision = "c4d9a81f2e70"
down_revision = "b0f4c2d178a9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("status", sa.String(length=20), server_default="Active", nullable=False))
    op.add_column("users", sa.Column("must_change_password", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("password_changed_at", sa.DateTime(), nullable=True))
    op.create_index(op.f("ix_users_status"), "users", ["status"], unique=False)
    op.create_index(op.f("ix_users_must_change_password"), "users", ["must_change_password"], unique=False)

    op.add_column("teachers", sa.Column("first_name", sa.String(length=80), nullable=True))
    op.add_column("teachers", sa.Column("middle_name", sa.String(length=80), nullable=True))
    op.add_column("teachers", sa.Column("last_name", sa.String(length=80), nullable=True))
    op.add_column("teachers", sa.Column("gender", sa.String(length=20), nullable=True))
    op.add_column("teachers", sa.Column("date_of_birth", sa.Date(), nullable=True))
    op.add_column("teachers", sa.Column("national_id", sa.String(length=80), nullable=True))
    op.add_column("teachers", sa.Column("phone", sa.String(length=40), nullable=True))
    op.add_column("teachers", sa.Column("email", sa.String(length=160), nullable=True))
    op.add_column("teachers", sa.Column("address", sa.String(length=255), nullable=True))
    op.add_column("teachers", sa.Column("qualification", sa.String(length=160), nullable=True))
    op.add_column("teachers", sa.Column("specialization", sa.String(length=160), nullable=True))
    op.add_column("teachers", sa.Column("hire_date", sa.Date(), nullable=True))
    op.add_column("teachers", sa.Column("employment_status", sa.String(length=30), server_default="Active", nullable=False))

    op.execute(
        """
        UPDATE teachers
        SET first_name = users.first_name,
            last_name = users.last_name,
            phone = users.phone,
            email = users.email
        FROM users
        WHERE teachers.user_id = users.id
        """
    )
    op.alter_column("teachers", "first_name", nullable=False)
    op.alter_column("teachers", "last_name", nullable=False)
    op.alter_column("teachers", "email", nullable=False)
    op.create_index(op.f("ix_teachers_national_id"), "teachers", ["national_id"], unique=True)
    op.create_index(op.f("ix_teachers_email"), "teachers", ["email"], unique=True)
    op.create_index(op.f("ix_teachers_employment_status"), "teachers", ["employment_status"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_teachers_employment_status"), table_name="teachers")
    op.drop_index(op.f("ix_teachers_email"), table_name="teachers")
    op.drop_index(op.f("ix_teachers_national_id"), table_name="teachers")
    for column in [
        "employment_status", "hire_date", "specialization", "qualification", "address",
        "email", "phone", "national_id", "date_of_birth", "gender", "last_name",
        "middle_name", "first_name",
    ]:
        op.drop_column("teachers", column)
    op.drop_index(op.f("ix_users_must_change_password"), table_name="users")
    op.drop_index(op.f("ix_users_status"), table_name="users")
    op.drop_column("users", "password_changed_at")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "must_change_password")
    op.drop_column("users", "status")
