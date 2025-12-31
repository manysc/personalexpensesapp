import logging
import os
import re

import pandas as pd
import pdfplumber

from personal_expenses_app.core.rule_based_expense_categorizer import (
    RuleBasedExpenseCategorizer,
)

logger = logging.getLogger(__name__)


class BanamexFileLoader:
    # Conversion rate: pesos to dollars
    PESO_TO_DOLLAR_RATE = 18.5

    def __init__(self):
        super().__init__()

    @staticmethod
    def _convert_to_dollars(peso_amount):
        """Convert Mexican pesos to US dollars."""
        if peso_amount is None:
            return None
        return round(peso_amount / BanamexFileLoader.PESO_TO_DOLLAR_RATE, 2)

    @staticmethod
    def _parse_month_abbrev(month_abbrev):
        """Convert Spanish month abbreviation to month number."""
        months = {
            "ENE": "01",
            "FEB": "02",
            "MAR": "03",
            "ABR": "04",
            "MAY": "05",
            "JUN": "06",
            "JUL": "07",
            "AGO": "08",
            "SEP": "09",
            "OCT": "10",
            "NOV": "11",
            "DIC": "12",
        }
        return months.get(month_abbrev.upper(), "01")

    def _extract_transactions_from_pdf(self, filename):
        """
        Extract transaction data from a Banamex PDF statement.
        Returns a DataFrame with Date, Description, Debit, and Credit columns.
        All amounts are converted from Mexican pesos to US dollars.

        Banamex format has a table with columns:
        FECHA | CONCEPTO | RETIROS | DEPÓSITOS | SALDO
        
        Each transaction starts with DD MMM and can span multiple lines.
        Lines with SUC, CAJA, HORA are metadata and should be excluded.
        The last line of each transaction contains the amounts.
        """
        if not os.path.isfile(filename):
            raise FileNotFoundError(f"File not found: {filename}")

        all_transactions = []

        # Extract year from filename
        year_match = re.search(r"-(\w+)-(\d{4})", filename)
        year = year_match.group(2) if year_match else "2025"

        with pdfplumber.open(filename) as pdf:
            in_transaction_section = False
            current_transaction = None
            self.previous_balance = None  # Track as instance variable

            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split("\n")

                for line in lines:
                    line_stripped = line.strip()

                    # Detect transaction section start
                    if "FECHA CONCEPTO" in line and ("RETIROS" in line or "DEP" in line):
                        in_transaction_section = True
                        continue

                    # Stop at summary sections
                    if (
                        "Resumen Operaciones" in line
                        or line_stripped.startswith("TARJETA ")
                    ):
                        # Finalize any pending transaction
                        if current_transaction:
                            self._add_transaction(
                                current_transaction,
                                all_transactions,
                                year,
                            )
                            current_transaction = None
                        in_transaction_section = False
                        continue

                    if not in_transaction_section:
                        continue

                    # Detect page boundaries - don't finalize transaction, just reset section flag
                    # Transactions can span multiple pages, so keep current_transaction alive
                    if line_stripped.startswith("Pägina ") or line_stripped.startswith("Página "):
                        in_transaction_section = False
                        continue

                    # Skip header repetitions, page markers, and empty lines
                    if (
                        not line_stripped
                        or "FECHA CONCEPTO" in line
                        or line_stripped.startswith("000")
                        or "Detalle de Operaciones" in line
                        or "En pesos Moneda Nacional" in line
                    ):
                        continue

                    # Check if this is the start of a new transaction (has date)
                    date_match = re.match(r"^(\d{1,2})\s+([A-Z]{3})\s+(.+)$", line_stripped)
                    
                    if date_match:
                        # Finalize previous transaction if exists
                        if current_transaction:
                            self._add_transaction(
                                current_transaction,
                                all_transactions,
                                year,
                            )

                        # Start new transaction
                        day = date_match.group(1).zfill(2)
                        month_abbrev = date_match.group(2)
                        rest = date_match.group(3)

                        month_num = self._parse_month_abbrev(month_abbrev)
                        
                        current_transaction = {
                            "day": day,
                            "month": month_num,
                            "description_lines": [],
                            "amounts": [],
                        }
                        
                        # Parse the rest of the first line
                        amounts = re.findall(r"[\d,]+\.\d\s?\d", rest)
                        desc = rest
                        for amt in amounts:
                            desc = desc.replace(amt, "", 1)
                        desc = " ".join(desc.split()).strip()
                        
                        if desc and desc.upper() != "SALDO ANTERIOR":
                            current_transaction["description_lines"].append(desc)
                        
                        if amounts:
                            current_transaction["amounts"] = [
                                float(a.replace(" ", "").replace(",", "")) for a in amounts
                            ]
                    
                    elif current_transaction:
                        # This is a continuation line for the current transaction
                        
                        # Extract amounts from this line first (even from metadata lines)
                        amounts = re.findall(r"[\d,]+\.\d\s?\d", line_stripped)
                        
                        # Skip metadata lines (but we've already extracted amounts)
                        if any(
                            line_stripped.startswith(prefix)
                            for prefix in ["SUC ", "CAJA ", "HORA ", "AUT "]
                        ) or re.match(r"^\d{8,}$", line_stripped):
                            # Update amounts if this line has them
                            if amounts:
                                current_transaction["amounts"] = [
                                    float(a.replace(" ", "").replace(",", "")) for a in amounts
                                ]
                            # Skip adding to description
                            continue
                        
                        # Extract description
                        desc = line_stripped
                        for amt in amounts:
                            desc = desc.replace(amt, "", 1)
                        desc = " ".join(desc.split()).strip()
                        
                        # Add description if meaningful
                        if desc and not desc.startswith("$"):
                            current_transaction["description_lines"].append(desc)
                        
                        # Update amounts if this line has them (last line of transaction)
                        if amounts:
                            current_transaction["amounts"] = [
                                float(a.replace(",", "")) for a in amounts
                            ]

            # Finalize any remaining transaction
            if current_transaction:
                self._add_transaction(
                    current_transaction, all_transactions, year
                )

        if not all_transactions:
            logger.warning(f"No transactions found in PDF: {filename}")
            return pd.DataFrame(columns=["Date", "Description", "Debit", "Credit"])

        df = pd.DataFrame(all_transactions)
        df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
        df["Debit"] = pd.to_numeric(df["Debit"], errors="coerce")
        df["Credit"] = pd.to_numeric(df["Credit"], errors="coerce")

        # Sort by date
        df = df.sort_values("Date").reset_index(drop=True)

        return df

    def _add_transaction(self, transaction, all_transactions, year):
        """
        Add a finalized transaction to the list.
        Determines if it's a debit or credit based on amounts and keywords.
        """
        if not transaction["amounts"]:
            return

        description = " ".join(transaction["description_lines"]).strip()
        
        # Skip if this is just a balance line
        if not description or "SALDO ANTERIOR" in description.upper():
            # But update the balance for reference
            if transaction["amounts"]:
                if len(transaction["amounts"]) == 1:
                    self.previous_balance = transaction["amounts"][0]
            return

        amounts = transaction["amounts"]
        
        # Determine transaction amount and type
        # Format can be: [AMOUNT, BALANCE] or [BALANCE] or [DEBIT, CREDIT, BALANCE]
        if len(amounts) == 1:
            # Just balance, no transaction amount visible
            # This shouldn't happen for real transactions
            return
        elif len(amounts) == 2:
            # Most common: [AMOUNT, BALANCE]
            transaction_amount = amounts[0]
            balance = amounts[1]
        else:
            # Multiple amounts, use first as transaction
            transaction_amount = amounts[0]
            balance = amounts[-1]

        # Determine if credit or debit based on keywords
        is_credit = False
        credit_keywords = [
            "PAGO RECIBIDO",
            "DEPOSITO",
            "DEPÓSITO",
            "ABONO",
            "TRANSFERENCIA RECIBIDA",
            "EXENCION",
            "EXENCIÓN",
            "INTERES",
            "INTERÉS",
        ]
        
        if any(keyword in description.upper() for keyword in credit_keywords):
            is_credit = True
        else:
            # Check balance movement if we have previous balance
            if self.previous_balance is not None:
                if balance > self.previous_balance:
                    is_credit = True

        # Update previous balance for next transaction
        self.previous_balance = balance

        # Convert to dollars
        amount_dollars = self._convert_to_dollars(transaction_amount)

        # Create transaction record
        date_str = f"{transaction['day']}/{transaction['month']}/{year}"
        all_transactions.append(
            {
                "Date": date_str,
                "Description": description,
                "Debit": None if is_credit else amount_dollars,
                "Credit": amount_dollars if is_credit else None,
            }
        )

    def _finalize_transaction(self, transaction, all_transactions, previous_balance, year):
        """
        Deprecated - kept for compatibility. Use _add_transaction instead.
        """
        self.previous_balance = previous_balance
        self._add_transaction(transaction, all_transactions, year)

    @staticmethod
    def load_expenses(filename):
        """Load only expenses (debits) from a PDF file."""
        loader = BanamexFileLoader()
        df = loader._extract_transactions_from_pdf(filename)
        return df[df["Debit"].notnull()]

    @staticmethod
    def load_credits(filename):
        """Load only credits from a PDF file."""
        loader = BanamexFileLoader()
        df = loader._extract_transactions_from_pdf(filename)
        return df[df["Credit"].notnull()]

    @staticmethod
    def load_expenses_and_credits(filename):
        """
        Load both expenses (debits) and credits from a PDF file and combine them.
        Returns a DataFrame with both debits and credits.
        All amounts are converted from Mexican pesos to US dollars at rate of 18.5 pesos per dollar.
        """
        loader = BanamexFileLoader()
        df = loader._extract_transactions_from_pdf(filename)
        # Only return rows that have either a debit or credit (not both null)
        return df[df["Debit"].notnull() | df["Credit"].notnull()]

    @staticmethod
    def load_and_label_multiple_files(file_list):
        """
        Load and categorize expenses from multiple PDF files.
        Similar to ChaseFileLoader.load_and_label_multiple_files.

        Args:
            file_list: List of PDF file paths to process

        Returns:
            Combined DataFrame with all transactions categorized and converted to USD
        """
        all_expenses = []
        categorized_expenses = RuleBasedExpenseCategorizer()
        banamex_file_loader = BanamexFileLoader()

        for filename in file_list:
            if os.path.exists(filename):
                df = banamex_file_loader.load_expenses_and_credits(filename)
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
