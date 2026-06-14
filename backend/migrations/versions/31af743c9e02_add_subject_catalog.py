"""add subject catalog

Revision ID: 31af743c9e02
Revises: 9d2e8f6b31a4
Create Date: 2026-06-06

"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = "31af743c9e02"
down_revision = "9d2e8f6b31a4"
branch_labels = None
depends_on = None


SUBJECTS = [
    ("MATH", "Mathematics"),
    ("PURE-MATH", "Pure Mathematics"),
    ("COMB-SCI", "Combined Science"),
    ("BIO", "Biology"),
    ("CHEM", "Chemistry"),
    ("PHYS", "Physics"),
    ("GEO", "Geography"),
    ("SHONA", "Shona"),
    ("ENG", "English"),
    ("AGRIC", "Agriculture"),
    ("HERITAGE", "Heritage Studies"),
    ("ADD-MATH", "Additional Mathematics"),
    ("FRS", "FRS"),
    ("HIST", "History"),
    ("COMM", "Commerce"),
    ("ECON", "Economics"),
    ("CROP-SCI", "Crop Science"),
    ("BUS-STUD", "Business Studies"),
    ("TECH-GR", "Technical Graphics"),
    ("COMP-STUD", "Computer Studies"),
    ("LIT-ENG", "Literature in English"),
    ("LIT-SHONA", "Literature in Shona"),
    ("SOC", "Sociology"),
    ("ANIM-SCI", "Animal Science"),
    ("BUILD", "Building"),
    ("WOOD", "Wood Work"),
    ("ACC", "Accounts"),
    ("TEXT-DES", "Textile Design"),
]


def upgrade():
    connection = op.get_bind()
    now = datetime.utcnow()
    statement = sa.text(
        """
        INSERT INTO subjects (code, name, stream, created_at, updated_at)
        VALUES (:code, :name, NULL, :created_at, :updated_at)
        ON CONFLICT (code) DO NOTHING
        """
    )
    for code, name in SUBJECTS:
        connection.execute(
            statement,
            {"code": code, "name": name, "created_at": now, "updated_at": now},
        )


def downgrade():
    pass
