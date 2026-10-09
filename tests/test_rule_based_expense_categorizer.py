import pandas as pd

from personal_expenses_app.core.rule_based_expense_categorizer import RuleBasedExpenseCategorizer


def _categorize(categorizer, description):
    df = pd.DataFrame(
        [{"Date": "2026-09-04", "Bank": "chase", "Description": description, "Debit": None, "Credit": 1.0}]
    )
    return categorizer.categorize_expenses(df)["Category"].iloc[0]


def test_default_categories_classify_veronica_zelle_as_real_state():
    result = _categorize(RuleBasedExpenseCategorizer(), "Zelle Payment From Veronica Flores 123")
    assert result == "Real State"


def test_custom_categories_override_defaults():
    categorizer = RuleBasedExpenseCategorizer({"Real State": ["Payment From Someone"], "Other Cat": ["WALMART"]})
    assert _categorize(categorizer, "Zelle Payment From Someone Else") == "Real State"
    assert _categorize(categorizer, "WALMART #123") == "Other Cat"


def test_empty_custom_categories_fall_back_to_defaults():
    assert _categorize(RuleBasedExpenseCategorizer({}), "WALMART #123") == "Groceries"
