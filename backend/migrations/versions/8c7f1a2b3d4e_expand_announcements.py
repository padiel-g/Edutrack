"""expand announcements

Revision ID: 8c7f1a2b3d4e
Revises: a1b5e273c948
"""

from alembic import op
import sqlalchemy as sa


revision = "8c7f1a2b3d4e"
down_revision = "a1b5e273c948"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("announcements") as batch_op:
        batch_op.add_column(sa.Column("target_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("video_path", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("video_filename", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("video_mime_type", sa.String(length=120), nullable=True))
        batch_op.create_index("ix_announcements_target_id", ["target_id"], unique=False)


def downgrade():
    with op.batch_alter_table("announcements") as batch_op:
        batch_op.drop_index("ix_announcements_target_id")
        batch_op.drop_column("video_mime_type")
        batch_op.drop_column("video_filename")
        batch_op.drop_column("video_path")
        batch_op.drop_column("target_id")
