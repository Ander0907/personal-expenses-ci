"""Unit tests for ``app.models.category`` using SQLAlchemy metadata only."""

from sqlalchemy import Boolean, CheckConstraint, Integer, Numeric, String
from sqlalchemy.schema import UniqueConstraint

from app.db.base import Base
from app.models import Category as ExportedCategory
from app.models.category import Category

table = Category.__table__


def test_category_is_exported_from_models_package() -> None:
    """Category is importable from app.models."""
    assert ExportedCategory is Category


def test_category_table_name() -> None:
    """Category maps to the categories table."""
    assert table.name == "categories"


def test_category_is_registered_on_base_metadata() -> None:
    """Category is registered on Base metadata."""
    assert table in Base.metadata.sorted_tables


def test_category_has_exactly_the_expected_columns() -> None:
    """Category has exactly four columns."""
    assert set(table.columns.keys()) == {
        "id",
        "name",
        "monthly_budget",
        "is_active",
    }


def test_id_is_integer_primary_key() -> None:
    """Id is an integer primary key."""
    assert isinstance(table.c.id.type, Integer)
    assert table.c.id.primary_key is True


def test_name_is_non_null_string_100() -> None:
    """Name is a non-null String(100)."""
    column = table.c.name

    assert isinstance(column.type, String)
    assert column.type.length == 100
    assert column.nullable is False


def test_name_has_named_unique_constraint() -> None:
    """Name has a unique constraint named uq_categories_name."""
    uniques = [c for c in table.constraints if isinstance(c, UniqueConstraint)]

    assert [(u.name, [col.name for col in u.columns]) for u in uniques] == [
        ("uq_categories_name", ["name"])
    ]


def test_monthly_budget_is_non_null_numeric_12_2() -> None:
    """Monthly budget is a non-null Numeric(12, 2)."""
    column = table.c.monthly_budget

    assert isinstance(column.type, Numeric)
    assert column.type.precision == 12
    assert column.type.scale == 2
    assert column.nullable is False


def test_is_active_is_non_null_boolean_with_true_server_default() -> None:
    """Is active is a non-null Boolean defaulting to true on the server."""
    column = table.c.is_active

    assert isinstance(column.type, Boolean)
    assert column.nullable is False
    assert column.server_default is not None
    assert "true" in str(column.server_default.arg).lower()


def test_monthly_budget_has_named_non_negative_check() -> None:
    """Monthly budget has a named non-negative check constraint."""
    checks = [c for c in table.constraints if isinstance(c, CheckConstraint)]

    assert [(c.name, str(c.sqltext)) for c in checks] == [
        ("ck_categories_monthly_budget_non_negative", "monthly_budget >= 0")
    ]
