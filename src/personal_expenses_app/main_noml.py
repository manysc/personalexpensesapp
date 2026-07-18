import pandas as pd

from personal_expenses_app.core.rule_based_expense_categorizer import (
    RuleBasedExpenseCategorizer,
)
from personal_expenses_app.core.summarizer import Summarizer
from personal_expenses_app.infrastructure.banamex_file_loader import BanamexFileLoader
from personal_expenses_app.infrastructure.chase_file_loader import ChaseFileLoader
from personal_expenses_app.infrastructure.citi_file_loader import CitiFileLoader
from personal_expenses_app.infrastructure.wellsfargo_file_loader import (
    WellsfargoFileLoader,
)
from personal_expenses_app.infrastructure.expense_db_persistence import (
    ExpenseDbPersistence,
)
from personal_expenses_app.interface.user_interaction import UserInteraction


def pipeline():
    # Load and label all data
    statements_year = "2026"

    citi_file_list = [
        f"resources/citi/{statements_year}/citi-{month}-{statements_year}.pdf"
        for month in [
            "jan",
            "feb",
            "mar",
            "apr",
            # "may",
            # "jun",
            # "jul",
            # "aug",
            # "sep",
            # "oct",
            # "nov",
            # "dec"
        ]
    ]
    citi_file_loader = CitiFileLoader()

    wellsfargo_file_list = [
        f"resources/wellsfargo/{statements_year}/wellsfargo-{month}-{statements_year}.pdf"
        for month in [
            "jan",
            "feb",
            "mar",
            "apr",
            # "may",
            # "jun",
            # "jul",
            # "aug",
            # "sep",
            # "oct",
            # "nov",
            # "dec"
        ]
    ]
    wellsfargo_file_loader = WellsfargoFileLoader()

    chase_file_list = [
        f"resources/chase/{statements_year}/chase-{month}-{statements_year}.pdf"
        for month in [
            "jan",
            "feb",
            "mar",
            "apr",
            # "may",
            # "jun",
            # "jul",
            # "aug",
            # "sep",
            # "oct",
            # "nov",
            # "dec"
        ]
    ]
    chase_file_loader = ChaseFileLoader()

    banamex_file_list = [
        f"resources/banamex/{statements_year}/banamex-{month}-{statements_year}.pdf"
        for month in [
            "jan",
            "feb",
            "mar",
            "apr",
            # "may",
            # "jun",
            # "jul",
            # "aug",
            # "sep",
            # "oct",
            # "nov",
            # "dec"
        ]
    ]
    banamex_file_loader = BanamexFileLoader()

    categorized_expenses = RuleBasedExpenseCategorizer()
    user_interaction = UserInteraction()
    summarizer = Summarizer()
    db_persistence = ExpenseDbPersistence()

    all_labeled_expenses = []

    # Load expenses from file_list
    for index, filename in enumerate(citi_file_list):
        df = citi_file_loader.load_expenses_and_credits(filename)

        if index < len(wellsfargo_file_list):
            df_others = wellsfargo_file_loader.load_expenses_and_credits(
                wellsfargo_file_list[index]
            )
            df = pd.concat([df, df_others], ignore_index=True)

        if index < len(chase_file_list):
            df_others = chase_file_loader.load_expenses_and_credits(
                chase_file_list[index]
            )
            df = pd.concat([df, df_others], ignore_index=True)

        if index < len(banamex_file_list):
            df_others = banamex_file_loader.load_expenses_and_credits(
                banamex_file_list[index]
            )
            df = pd.concat([df, df_others], ignore_index=True)

        if df is None or df.empty:
            print(f"No data loaded for file: {filename}")
            continue

        # Categorize expenses based on rules
        labeled_expenses = categorized_expenses.categorize_expenses(df)

        # Persist to database
        db_persistence.save_expenses(labeled_expenses)

        all_labeled_expenses.append(labeled_expenses)

    # Summarize all expenses grouped by their actual transaction month and year,
    # so transactions from previous statement periods appear in the correct month.
    if all_labeled_expenses:
        combined = pd.concat(all_labeled_expenses, ignore_index=True)
        combined = combined.drop_duplicates()
        for (year_val, month_val), group in combined.groupby(
            [combined["Date"].dt.year, combined["Date"].dt.month]
        ):
            summary = summarizer.summarize_by_category(group)
            summary["Month"] = pd.Timestamp(year=year_val, month=month_val, day=1).strftime("%b")
            summary["Year"] = str(year_val)
            user_interaction.print_summary(summary)
            user_interaction.print_total(summary)


if __name__ == "__main__":
    pipeline()
