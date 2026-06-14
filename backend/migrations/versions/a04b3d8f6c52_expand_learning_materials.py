"""expand learning materials

Revision ID: a04b3d8f6c52
Revises: f93a2c7e5b41
Create Date: 2026-06-07

"""
from alembic import op
import sqlalchemy as sa


revision = "a04b3d8f6c52"
down_revision = "f93a2c7e5b41"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("learning_materials", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("learning_materials", sa.Column("stored_filename", sa.String(length=255), nullable=True))
    op.add_column("learning_materials", sa.Column("original_filename", sa.String(length=255), nullable=True))
    op.add_column("learning_materials", sa.Column("mime_type", sa.String(length=120), nullable=True))
    op.add_column("learning_materials", sa.Column("file_size", sa.Integer(), nullable=True))
    op.alter_column("learning_materials", "class_id", nullable=True)
    op.create_unique_constraint("uq_learning_materials_stored_filename", "learning_materials", ["stored_filename"])


def downgrade():
    op.drop_constraint("uq_learning_materials_stored_filename", "learning_materials", type_="unique")
    op.alter_column("learning_materials", "class_id", nullable=False)
    op.drop_column("learning_materials", "file_size")
    op.drop_column("learning_materials", "mime_type")
    op.drop_column("learning_materials", "original_filename")
    op.drop_column("learning_materials", "stored_filename")
    op.drop_column("learning_materials", "description")
