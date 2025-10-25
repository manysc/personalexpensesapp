import os

import pandas as pd

from personal_expenses_app.core.rule_based_expense_categorizer import (
    RuleBasedExpenseCategorizer,
)


class CsvFileLoader:
    def __init__(self):
        super().__init__()

    @staticmethod
    def load_expenses(filename):
        if not os.path.isfile(filename):
            raise FileNotFoundError(f"File not found: {filename}")
        df = pd.read_csv(filename)
        df["Debit"] = pd.to_numeric(df["Debit"], errors="coerce")
        return df[df["Debit"].notnull()]

    @staticmethod
    def load_credits(filename):
        if not os.path.isfile(filename):
            raise FileNotFoundError(f"File not found: {filename}")
        df = pd.read_csv(filename)
        df["Credit"] = pd.to_numeric(df["Credit"], errors="coerce")
        return df[df["Credit"].notnull()]

    @staticmethod
    def load_expenses_and_credits(filename):
        """
        Load both expenses (debits) and credits from a CSV file and combine them.
        Returns a DataFrame with both debits and credits.
        """
        if not os.path.isfile(filename):
            raise FileNotFoundError(f"File not found: {filename}")

        df = pd.read_csv(filename)
        df["Debit"] = pd.to_numeric(df["Debit"], errors="coerce")
        df["Credit"] = pd.to_numeric(df["Credit"], errors="coerce")

        # Only return rows that have either a debit or credit (not both null)
        return df[df["Debit"].notnull() | df["Credit"].notnull()]

    @staticmethod
    def load_and_label_multiple_files(file_list):
        all_expenses = []
        categorized_expenses = RuleBasedExpenseCategorizer()
        csv_file_loader = CsvFileLoader()
        for filename in file_list:
            if os.path.exists(filename):
                df = csv_file_loader.load_expenses_and_credits(filename)
                labeled = categorized_expenses.categorize_expenses(df)
                all_expenses.append(labeled)
            else:
                print(f"Warning: File not found: {filename}")

        if not all_expenses:
            raise ValueError(
                f"No valid expense files found. Checked {len(file_list)} files. Please verify file paths."
            )

        combined = pd.concat(all_expenses, ignore_index=True)
        return combined
