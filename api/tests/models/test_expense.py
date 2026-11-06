"""Unit tests for ``app.models.expense`` using SQLAlchemy metadata only."""

from sqlalchemy import CheckConstraint, Date, DateTime, Integer, Numeric, String

from app.db.base import Base
from app.models import Expense as ExportedExpense
from app.models.expense import Expense

table = Expense.__table__


def test_expense_is_exported_from_models_package() -> None:
    """Expense is importable from app.models."""
    assert ExportedExpense is Expense


def test_expense_table_name() -> None:
    """Expense maps to the expenses table."""
    assert table.name == "expenses"


def test_expense_is_registered_on_base_metadata() -> None:
    """Expense is registered on Base metadata."""
    assert table in Base.metadata.sorted_tables


def test_expense_has_exactly_the_expected_columns() -> None:
    """Expense has exactly six columns."""
    assert set(table.columns.keys()) == {
        "id",
        "category_id",
        "amount",
        "description",
        "spent_at",
        "created_at",
    }


def test_id_is_integer_primary_key() -> None:
    """Id is an integer primary key."""
    assert isinstance(table.c.id.type, Integer)
    assert table.c.id.primary_key is True


def test_category_id_is_non_null_integer() -> None:
    """Category id is a non-null integer."""
    assert isinstance(table.c.category_id.type, Integer)
    assert table.c.category_id.nullable is False


def test_category_id_has_single_restrict_foreign_key_to_categories() -> None:
    """Category id has one named RESTRICT foreign key to categories.id."""
    fks = list(table.foreign_keys)

    assert len(fks) == 1
    fk = fks[0]
    assert fk.target_fullname == "categories.id"
    assert fk.parent.name == "category_id"
    assert fk.ondelete == "RESTRICT"
    assert fk.constraint is not None
    assert fk.constraint.name == "fk_expenses_category_id_categories"


def test_amount_is_non_null_numeric_12_2() -> None:
    """Amount is a non-null Numeric(12, 2)."""
    column = table.c.amount

    assert isinstance(column.type, Numeric)
    assert column.type.precision == 12
    assert column.type.scale == 2
    assert column.nullable is False


def test_description_is_nullable_string_255() -> None:
    """Description is a nullable String(255)."""
    column = table.c.description

    assert isinstance(column.type, String)
    assert column.type.length == 255
    assert column.nullable is True


def test_spent_at_is_non_null_date() -> None:
    """Spent at is a non-null Date."""
    assert isinstance(table.c.spent_at.type, Date)
    assert table.c.spent_at.nullable is False


def test_created_at_is_timezone_aware_with_server_default() -> None:
    """Created at is a non-null tz-aware DateTime with a server default."""
    column = table.c.created_at

    assert isinstance(column.type, DateTime)
    assert column.type.timezone is True
    assert column.nullable is False
    assert column.server_default is not None


def test_amount_has_named_positive_check() -> None:
    """Amount has a named positive check constraint."""
    checks = [c for c in table.constraints if isinstance(c, CheckConstraint)]

    assert [(c.name, str(c.sqltext)) for c in checks] == [
        ("ck_expenses_amount_positive", "amount > 0")
    ]


def test_expense_has_exactly_the_expected_indexes() -> None:
    """Expense has exactly the two expected indexes with ordered columns."""
    indexes = {
        index.name: [column.name for column in index.columns] for index in table.indexes
    }

    assert indexes == {
        "ix_expenses_category_id_spent_at": ["category_id", "spent_at"],
        "ix_expenses_spent_at": ["spent_at"],
    }
