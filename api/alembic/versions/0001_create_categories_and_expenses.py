"""Create categories and expenses tables.

Revision ID: 0001
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the categories and expenses tables with their indexes."""
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("monthly_budget", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.true(), nullable=False
        ),
        sa.CheckConstraint(
            "monthly_budget >= 0",
            name=op.f("ck_categories_monthly_budget_non_negative"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_categories"),
        sa.UniqueConstraint("name", name="uq_categories_name"),
    )
    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("spent_at", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("amount > 0", name=op.f("ck_expenses_amount_positive")),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name="fk_expenses_category_id_categories",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_expenses"),
    )
    op.create_index(
        "ix_expenses_category_id_spent_at",
        "expenses",
        ["category_id", "spent_at"],
    )
    op.create_index("ix_expenses_spent_at", "expenses", ["spent_at"])


def downgrade() -> None:
    """Drop the indexes and tables in reverse order."""
    op.drop_index("ix_expenses_spent_at", table_name="expenses")
    op.drop_index("ix_expenses_category_id_spent_at", table_name="expenses")
    op.drop_table("expenses")
    op.drop_table("categories")
