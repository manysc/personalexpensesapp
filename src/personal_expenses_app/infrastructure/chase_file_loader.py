import logging
import os
import re

import pandas as pd
import pdfplumber

from personal_expenses_app.core.rule_based_expense_categorizer import (
    RuleBasedExpenseCategorizer,
)

logger = logging.getLogger(__name__)


class ChaseFileLoader:
    def __init__(self):
        super().__init__()

    @staticmethod
    def _parse_chase_transaction_line(line, year="2025"):
        """
        Parse a single Chase transaction line.
        Format: MM/DD Description $Amount
        Example: 12/23 Zelle Payment From Carmen Samaniego Wfct0Yclh2Kt $600.00

        Returns: dict with Date, Description, amount or None if not a transaction line
        """
        if "Remote Online Deposit" in line:
            logger.info(f"line with Remote Online Deposit: {line}")
        # Match lines that start with date MM/DD
        match = re.match(
            r"^(\d{1,2}/\d{1,2})\s+(.+?)\s+\$?([\d,]+\.\d{2})$", line.strip()
        )
        if not match:
            return None

        date_str = match.group(1)
        description = match.group(2).strip()
        amount_str = match.group(3)

        # Remove $ and commas from amount
        amount = float(amount_str.replace(",", "").replace("$", ""))

        return {
            "Date": f"{date_str}/{year}",
            "Description": description,
            "Amount": amount,
        }

    def _extract_transactions_from_pdf(self, filename):
        """
        Extract transaction data from a Chase PDF statement.
        Returns a DataFrame with Date, Description, Debit, and Credit columns.

        Chase format has two sections:
        - DEPOSITS AND ADDITIONS (credits)
        - ELECTRONIC WITHDRAWALS (debits)
        """
        if not os.path.isfile(filename):
            raise FileNotFoundError(f"File not found: {filename}")

        credits = []
        debits = []

        # Extract year from filename
        year_match = re.search(r"-(\w+)-(\d{4})", filename)
        year = year_match.group(2) if year_match else "2025"

        with pdfplumber.open(filename) as pdf:
            current_section = None

            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split("\n")

                for line in lines:
                    line_stripped = line.strip()

                    # Detect section headers
                    if "DEPOSITS AND ADDITIONS" in line:
                        current_section = "credits"
                        continue
                    elif "ELECTRONIC WITHDRAWALS" in line:
                        current_section = "debits"
                        continue
                    elif line_stripped.startswith(
                        "Total Deposits"
                    ) or line_stripped.startswith("Total Electronic"):
                        current_section = None
                        continue

                    # Skip headers and empty lines
                    if not current_section or not line_stripped:
                        continue

                    if "DATE DESCRIPTION AMOUNT" in line:
                        continue

                    # Try to parse the line as a transaction
                    transaction = self._parse_chase_transaction_line(line, year)
                    if transaction:
                        if current_section == "credits":
                            credits.append(transaction)
                        elif current_section == "debits":
                            debits.append(transaction)

        # Combine into single list with Debit/Credit columns
        all_transactions = []

        for credit in credits:
            all_transactions.append(
                {
                    "Date": credit["Date"],
                    "Description": credit["Description"],
                    "Debit": None,
                    "Credit": credit["Amount"],
                }
            )

        for debit in debits:
            all_transactions.append(
                {
                    "Date": debit["Date"],
                    "Description": debit["Description"],
                    "Debit": debit["Amount"],
                    "Credit": None,
                }
            )

        if not all_transactions:
            raise ValueError(f"No transactions found in PDF: {filename}")

        df = pd.DataFrame(all_transactions)
        df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")
        df["Debit"] = pd.to_numeric(df["Debit"], errors="coerce")
        df["Credit"] = pd.to_numeric(df["Credit"], errors="coerce")

        # Sort by date
        df = df.sort_values("Date").reset_index(drop=True)

        return df

    @staticmethod
    def load_expenses(filename):
        """Load only expenses (debits) from a PDF file."""
        loader = ChaseFileLoader()
        df = loader._extract_transactions_from_pdf(filename)
        return df[df["Debit"].notnull()]

    @staticmethod
    def load_credits(filename):
        """Load only credits from a PDF file."""
        loader = ChaseFileLoader()
        df = loader._extract_transactions_from_pdf(filename)
        return df[df["Credit"].notnull()]

    @staticmethod
    def load_expenses_and_credits(filename):
        """
        Load both expenses (debits) and credits from a PDF file and combine them.
        Returns a DataFrame with both debits and credits.
        """
        loader = ChaseFileLoader()
        df = loader._extract_transactions_from_pdf(filename)
        # Only return rows that have either a debit or credit (not both null)
        return df[df["Debit"].notnull() | df["Credit"].notnull()]

    @staticmethod
    def load_and_label_multiple_files(file_list):
        """
        Load and categorize expenses from multiple PDF files.
        Similar to CsvFileLoader.load_and_label_multiple_files.

        Args:
            file_list: List of PDF file paths to process

        Returns:
            Combined DataFrame with all transactions categorized
        """
        all_expenses = []
        categorized_expenses = RuleBasedExpenseCategorizer()
        chase_file_loader = ChaseFileLoader()

        for filename in file_list:
            if os.path.exists(filename):
                df = chase_file_loader.load_expenses_and_credits(filename)
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
