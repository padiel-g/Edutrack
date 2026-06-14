"""expand fee payment workflow

Revision ID: 5b7c9d1e3f20
Revises: 8c7f1a2b3d4e
Create Date: 2026-06-13
"""
from alembic import op
import sqlalchemy as sa


revision = "5b7c9d1e3f20"
down_revision = "8c7f1a2b3d4e"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("student_fee_accounts") as batch:
        batch.add_column(sa.Column("term_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("total_fee", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch.add_column(sa.Column("total_paid", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch.create_index("ix_student_fee_accounts_term_id", ["term_id"])
        batch.create_foreign_key("fk_student_fee_accounts_term_id", "terms", ["term_id"], ["id"])

    with op.batch_alter_table("payments") as batch:
        batch.alter_column("invoice_id", existing_type=sa.Integer(), nullable=True)
        batch.add_column(sa.Column("fee_account_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("term_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("reference_number", sa.String(100), nullable=True))
        batch.add_column(sa.Column("note", sa.Text(), nullable=True))
        batch.add_column(sa.Column("previous_balance", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch.add_column(sa.Column("new_balance", sa.Numeric(12, 2), nullable=False, server_default="0"))
        batch.add_column(sa.Column("recorded_by_id", sa.Integer(), nullable=True))
        batch.create_index("ix_payments_fee_account_id", ["fee_account_id"])
        batch.create_index("ix_payments_term_id", ["term_id"])
        batch.create_index("ix_payments_reference_number", ["reference_number"])
        batch.create_index("ix_payments_recorded_by_id", ["recorded_by_id"])
        batch.create_foreign_key("fk_payments_fee_account_id", "student_fee_accounts", ["fee_account_id"], ["id"])
        batch.create_foreign_key("fk_payments_term_id", "terms", ["term_id"], ["id"])
        batch.create_foreign_key("fk_payments_recorded_by_id", "users", ["recorded_by_id"], ["id"])

    with op.batch_alter_table("receipts") as batch:
        batch.add_column(sa.Column("issued_by_id", sa.Integer(), nullable=True))
        batch.create_index("ix_receipts_issued_by_id", ["issued_by_id"])
        batch.create_foreign_key("fk_receipts_issued_by_id", "users", ["issued_by_id"], ["id"])

    op.execute("""
        UPDATE student_fee_accounts a
        SET total_fee = COALESCE(i.total_fee, a.current_balance, 0),
            total_paid = COALESCE(i.total_paid, 0),
            status = CASE
                WHEN COALESCE(a.current_balance, 0) = 0 AND COALESCE(i.total_paid, 0) > 0 THEN 'Paid'
                WHEN COALESCE(i.total_paid, 0) > 0 THEN 'Partially Paid'
                ELSE 'Unpaid'
            END
        FROM (
            SELECT fee_account_id, SUM(amount) AS total_fee, SUM(paid_amount) AS total_paid
            FROM invoices WHERE fee_account_id IS NOT NULL GROUP BY fee_account_id
        ) i
        WHERE a.id = i.fee_account_id
    """)


def downgrade():
    with op.batch_alter_table("receipts") as batch:
        batch.drop_constraint("fk_receipts_issued_by_id", type_="foreignkey")
        batch.drop_index("ix_receipts_issued_by_id")
        batch.drop_column("issued_by_id")
    with op.batch_alter_table("payments") as batch:
        for name in ["fk_payments_recorded_by_id", "fk_payments_term_id", "fk_payments_fee_account_id"]:
            batch.drop_constraint(name, type_="foreignkey")
        for name in ["ix_payments_recorded_by_id", "ix_payments_reference_number", "ix_payments_term_id", "ix_payments_fee_account_id"]:
            batch.drop_index(name)
        for name in ["recorded_by_id", "new_balance", "previous_balance", "note", "reference_number", "term_id", "fee_account_id"]:
            batch.drop_column(name)
        batch.alter_column("invoice_id", existing_type=sa.Integer(), nullable=False)
    with op.batch_alter_table("student_fee_accounts") as batch:
        batch.drop_constraint("fk_student_fee_accounts_term_id", type_="foreignkey")
        batch.drop_index("ix_student_fee_accounts_term_id")
        batch.drop_column("total_paid")
        batch.drop_column("total_fee")
        batch.drop_column("term_id")
