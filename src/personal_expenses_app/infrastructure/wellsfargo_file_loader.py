import os
import re

import pandas as pd
import pdfplumber

from personal_expenses_app.core.rule_based_expense_categorizer import (
    RuleBasedExpenseCategorizer,
)


class WellsfargoFileLoader:
    def __init__(self):
        super().__init__()

    @staticmethod
    def _parse_wellsfargo_transaction_line(line, year="2025"):
        """
        Parse a single Wells Fargo transaction line.
        Format: M/D Description [Amount1] [Amount2]
        Where Amount2 (if present) is the ending balance, and Amount1 is the transaction amount.
        Some lines only have the transaction amount without the ending balance.

        Returns: dict with Date, Description, Debit, Credit or None if not a transaction line
        """
        # Match lines that start with date M/D or MM/DD
        match = re.match(r"^(\d{1,2}/\d{1,2})\s+(.+)$", line.strip())
        if not match:
            return None

        date_str = match.group(1)
        rest = match.group(2)

        # Extract all amounts from the line
        amounts = re.findall(r"[\d,]+\.\d{2}", rest)

        # Need at least one amount (transaction amount)
        if len(amounts) < 1:
            return None

        # Remove amounts from description
        description = rest
        for amt in amounts:
            description = description.replace(amt, "").strip()

        # Clean up description
        description = " ".join(description.split())

        # Determine transaction amount
        if len(amounts) >= 2:
            # Second to last amount is the transaction amount
            # Last amount is the balance (ignore it)
            transaction_amount = float(amounts[-2].replace(",", ""))
        else:
            # Only one amount - it's the transaction amount
            transaction_amount = float(amounts[0].replace(",", ""))

        # Determine if credit or debit based on keywords
        credit_keywords = [
            "transfer from",
            "deposit",
            "credit",
            "interest",
            "refund",
            "recurring transfer from",
        ]
        is_credit = any(keyword in description.lower() for keyword in credit_keywords)

        return {
            "Date": f"{date_str}/{year}",
            "Description": description,
            "Debit": None if is_credit else transaction_amount,
            "Credit": transaction_amount if is_credit else None,
        }

    def _extract_transactions_from_pdf(self, filename):
        """
        Extract transaction data from a Wells Fargo PDF statement.
        Returns a DataFrame with Date, Description, Debit, and Credit columns.

        Wells Fargo format:
        Date Number Description Additions Subtractions balance
        1/2 Bank of America Mortgage 250102 P12739652 , Salas M 798.44 3,157.01

        Some transactions span multiple lines when description is long.
        """
        if not os.path.isfile(filename):
            raise FileNotFoundError(f"File not found: {filename}")

        transactions = []

        # Extract year from filename
        year_match = re.search(r"-(\w+)-(\d{4})", filename)
        year = year_match.group(2) if year_match else "2025"

        with pdfplumber.open(filename) as pdf:
            in_transaction_section = False
            pending_line = None  # Store line that might continue on next line

            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split("\n")

                for i, line in enumerate(lines):
                    # Check if we're in the transaction history section
                    if "Transaction history" in line:
                        in_transaction_section = True
                        continue

                    # Stop at totals line or other end markers
                    if line.strip().startswith("Totals"):
                        in_transaction_section = False
                        # Process any pending line before stopping
                        if pending_line:
                            transaction = self._parse_wellsfargo_transaction_line(
                                pending_line, year
                            )
                            if transaction:
                                transactions.append(transaction)
                            pending_line = None
                        continue

                    # Only process if we're in the transaction section
                    if not in_transaction_section:
                        continue

                    # Skip header lines
                    if (
                        "Date Number Description" in line
                        or "Deposits/" in line
                        or "Withdrawals/" in line
                    ):
                        continue

                    # Check if current line starts with a date (potential new transaction)
                    if re.match(r"^\d{1,2}/\d{1,2}\s+", line):
                        # Process any pending line first
                        if pending_line:
                            transaction = self._parse_wellsfargo_transaction_line(
                                pending_line, year
                            )
                            if transaction:
                                transactions.append(transaction)
                            pending_line = None

                        # Try to parse current line
                        transaction = self._parse_wellsfargo_transaction_line(
                            line, year
                        )
                        if transaction:
                            # Successfully parsed, add it
                            transactions.append(transaction)
                        else:
                            # Couldn't parse (maybe needs next line), store it
                            pending_line = line
                    elif pending_line:
                        # This line might be continuation of previous transaction
                        # Merge and try to parse again
                        merged_line = pending_line + " " + line.strip()
                        transaction = self._parse_wellsfargo_transaction_line(
                            merged_line, year
                        )
                        if transaction:
                            transactions.append(transaction)
                            pending_line = None
                        else:
                            # Still can't parse, keep accumulating
                            pending_line = merged_line

            # Process any remaining pending line
            if pending_line:
                transaction = self._parse_wellsfargo_transaction_line(
                    pending_line, year
                )
                if transaction:
                    transactions.append(transaction)

        if not transactions:
            raise ValueError(f"No transactions found in PDF: {filename}")

        df = pd.DataFrame(transactions)
        df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")
        df["Debit"] = pd.to_numeric(df["Debit"], errors="coerce")
        df["Credit"] = pd.to_numeric(df["Credit"], errors="coerce")

        return df

    @staticmethod
    def load_expenses(filename):
        """Load only expenses (debits) from a PDF file."""
        loader = WellsfargoFileLoader()
        df = loader._extract_transactions_from_pdf(filename)
        return df[df["Debit"].notnull()]

    @staticmethod
    def load_credits(filename):
        """Load only credits from a PDF file."""
        loader = WellsfargoFileLoader()
        df = loader._extract_transactions_from_pdf(filename)
        return df[df["Credit"].notnull()]

    @staticmethod
    def load_expenses_and_credits(filename):
        """
        Load both expenses (debits) and credits from a PDF file and combine them.
        Returns a DataFrame with both debits and credits.
        """
        loader = WellsfargoFileLoader()
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
        pdf_file_loader = WellsfargoFileLoader()

        for filename in file_list:
            if os.path.exists(filename):
                df = pdf_file_loader.load_expenses_and_credits(filename)
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
