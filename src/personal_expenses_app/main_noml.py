from pathlib import Path

import pandas as pd

from personal_expenses_app.core.rule_based_expense_categorizer import (
    RuleBasedExpenseCategorizer,
)
from personal_expenses_app.core.summarizer import Summarizer
from personal_expenses_app.infrastructure.chase_file_loader import ChaseFileLoader
from personal_expenses_app.infrastructure.citi_file_loader import CitiFileLoader
from personal_expenses_app.infrastructure.wellsfargo_file_loader import (
    WellsfargoFileLoader,
)
from personal_expenses_app.interface.user_interaction import UserInteraction


def pipeline():
    # Load and label all data
    # Get the project root directory (2 levels up from this file)
    project_root = Path(__file__).parent.parent.parent

    citi_resources_dir = project_root / "resources" / "citi"
    citi_file_list = [
        str(citi_resources_dir / f"citi-{month}-2025.CSV")
        for month in [
            "jan",
            "feb",
            "mar",
            "apr",
            "may",
            "jun",
            "jul",
            "aug",
            "sep",
            "oct",
        ]
    ]
    citi_file_loader = CitiFileLoader()

    wellsfargo_resources_dir = project_root / "resources" / "wellsfargo"
    wellsfargo_file_list = [
        str(wellsfargo_resources_dir / f"wellsfargo-{month}-2025.pdf")
        for month in [
            "jan",
            "feb",
            "mar",
            "apr",
            "may",
            "jun",
            "jul",
            "aug",
            "sep",
            "oct",
        ]
    ]
    wellsfargo_file_loader = WellsfargoFileLoader()

    chase_resources_dir = project_root / "resources" / "chase"
    chase_file_list = [
        str(chase_resources_dir / f"chase-{month}-2025.pdf")
        for month in [
            "jan",
            "feb",
            "mar",
            "apr",
            "may",
            "jun",
            "jul",
            "aug",
            "sep",
            "oct",
        ]
    ]
    chase_file_loader = ChaseFileLoader()

    categorized_expenses = RuleBasedExpenseCategorizer()
    user_interaction = UserInteraction()
    summarizer = Summarizer()

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

        # Categorize expenses based on rules
        labeled_expenses = categorized_expenses.categorize_expenses(df)

        # Summarize
        month = filename.split("-")[1].capitalize()
        year = filename.split("-")[2].split(".")[0]
        summary = summarizer.summarize_by_category(labeled_expenses)
        summary["Month"] = month
        summary["Year"] = year
        user_interaction.print_summary(summary)
        user_interaction.print_total(summary)


if __name__ == "__main__":
    pipeline()
