import os
from pathlib import Path

import pandas as pd

from personal_expenses_app.core.corrections import Corrections
from personal_expenses_app.core.ml_based_expense_categorizer import (
    MLBasedExpenseCategorizer,
)
from personal_expenses_app.core.summarizer import Summarizer
from personal_expenses_app.infrastructure.csv_file_loader import CitiFileLoader
from personal_expenses_app.infrastructure.file_persistence import FilePersistence
from personal_expenses_app.infrastructure.wellsfargo_file_loader import (
    WellsfargoFileLoader,
)
from personal_expenses_app.interface.user_interaction import UserInteraction


def pipeline():
    # 1. Load and label all data for model training
    # Get the project root directory (2 levels up from this file)
    project_root = Path(__file__).parent.parent.parent
    resources_dir = project_root / "resources" / "citi"

    file_list = [
        str(resources_dir / f"citi-{month}-2025.CSV")
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
    citi_expenses = citi_file_loader.load_and_label_multiple_files(file_list)

    wellsfargo_resources_dir = project_root / "resources" / "wellsfargo"
    wells_fargo_file_list = [
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
    wellsfargo_expenses = wellsfargo_file_loader.load_and_label_multiple_files(
        wells_fargo_file_list
    )
    # append Wellsfargo expenses to Citi expenses
    citi_expenses = pd.concat([citi_expenses, wellsfargo_expenses])

    ml_based_expense_categorizer = MLBasedExpenseCategorizer()
    training_data = ml_based_expense_categorizer.prepare_training_data(citi_expenses)

    # 2. Split train/test for per-category accuracy
    X_train, X_test, y_train, y_test = ml_based_expense_categorizer.split_train_test(
        training_data
    )

    # 3. Train and evaluate model
    model = ml_based_expense_categorizer.train_categorization_model(
        pd.DataFrame({"Description": X_train, "Category": y_train})
    )
    cat_acc = ml_based_expense_categorizer.evaluate_model(model, X_test, y_test)

    # 4. Predict on files from file_list
    for index, filename in enumerate(file_list):
        df = citi_file_loader.load_expenses_and_credits(filename)

        if index < len(wells_fargo_file_list):
            df_others = wellsfargo_file_loader.load_expenses_and_credits(
                wells_fargo_file_list[index]
            )
            df = pd.concat([df, df_others], ignore_index=True)

        ml_predicted = ml_based_expense_categorizer.ml_categorize_expenses(
            df.copy(), model
        )

        # 5. Load and apply corrections
        file_persistence = FilePersistence()
        corrections_file = str(project_root / "resources" / "corrections.csv")
        corrections_df = file_persistence.load_corrections(corrections_file)
        corrections = Corrections()
        ml_corrected = corrections.apply_corrections(
            ml_predicted, corrections_df, citi_expenses
        )

        # 6. Collect new corrections from User, for low-accuracy categories not in corrections
        user_interaction = UserInteraction()
        user_prompt_fn = user_interaction.ask_user_correction
        new_corrections = corrections.collect_low_acc_corrections(
            ml_corrected,
            corrections_df,
            cat_acc,
            citi_expenses,
            user_prompt_fn=user_prompt_fn,
            threshold=0.8,
        )
        if not new_corrections.empty:
            file_persistence.save_corrections(new_corrections, corrections_file)
            # Reload and reapply corrections
            corrections_df = file_persistence.load_corrections(corrections_file)
            ml_corrected = corrections.apply_corrections(
                ml_corrected, corrections_df, citi_expenses
            )

        # 7. Summarize
        summarizer = Summarizer()
        month = filename.split("-")[1].capitalize()
        year = filename.split("-")[2].split(".")[0]
        summary = summarizer.summarize_by_category(ml_corrected)
        summary["Month"] = month
        summary["Year"] = year
        user_interaction.print_summary(summary)


if __name__ == "__main__":
    pipeline()
