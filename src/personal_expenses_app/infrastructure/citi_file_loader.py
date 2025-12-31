import logging
import os
import re

import pandas as pd
import pdfplumber

from personal_expenses_app.core.rule_based_expense_categorizer import (
    RuleBasedExpenseCategorizer,
)

logger = logging.getLogger(__name__)


class CitiFileLoader:
    def __init__(self):
        super().__init__()

    @staticmethod
    def _parse_citi_transaction_line(line, year="2025"):
        """
        Parse a single Citi transaction line.
        Supports multiple formats:
        1. MM/DD MM/DD Description $Amount [optional extra text]
           Example: 12/09 12/10 DAIRY QUEEN #15096 TUCSON AZ $11.50
        2. MM/DD Description $Amount (single date with description and amount)
           Example: 11/03 AUTOPAY 999990000037199RAUTOPAY AUTO-PMT -$3,993.51
        3. MM/DD Description (for foreign currency, amount on next line)
           Example: 12/20 PURO PA DELANTE HERMOSILLO SOMX
        4. MM/DD $Amount (date and amount only, description elsewhere)
           Example: 12/12 $68.00

        The first date is the transaction date, the second is the post date (when present).
        Negative amounts indicate credits/refunds.

        Returns: dict with Date, Description, Debit, Credit or None if not a transaction line
        """
        line_stripped = line.strip()
        
        # Format 1: Two dates with description and amount
        # Example: 12/09 12/10 DAIRY QUEEN #15096 TUCSON AZ $11.50
        # Important: The amount should NOT be part of summary text like "Year to Date : $X.XX"
        # If we see "Year to Date" or similar, this is likely a foreign currency transaction
        match = re.match(
            r"^(\d{1,2}/\d{1,2})\s+(\d{1,2}/\d{1,2})\s+(.+?)\s+(-?\$?[\d,]+\.\d{2})",
            line_stripped,
        )
        if match:
            transaction_date = match.group(1)
            description = match.group(3).strip()
            amount_str = match.group(4)
            
            # Check if the amount is part of summary text (e.g., "Year to Date : $509.64")
            # These should not be treated as transaction amounts
            full_text_before_amount = match.group(3)
            if re.search(r"Year to Date\s*:\s*$", full_text_before_amount, re.IGNORECASE):
                # This is a foreign currency transaction - skip Format 1 parsing
                # The amount will be on the next line with "MEXICAN PESO"
                pass
            else:
                # Normal Format 1 transaction
                amount = float(amount_str.replace(",", "").replace("$", ""))
                
                if amount < 0:
                    return {
                        "Date": f"{transaction_date}/{year}",
                        "Description": description,
                        "Debit": None,
                        "Credit": abs(amount),
                    }
                else:
                    return {
                        "Date": f"{transaction_date}/{year}",
                        "Description": description,
                        "Debit": amount,
                        "Credit": None,
                    }
        
        # Format 2: Single date with description and amount (for payments/autopay)
        # Example: 11/03 AUTOPAY 999990000037199RAUTOPAY AUTO-PMT -$3,993.51
        # This must be checked BEFORE Format 4 (single date + amount only)
        # IMPORTANT: Skip lines with reward amounts (e.g., "+$29.54" with "1% on all other purchases")
        # Those are foreign currency transactions with amount on next line
        match = re.match(
            r"^(\d{1,2}/\d{1,2})\s+(.+?)\s+(-?\$?[\d,]+\.\d{2})",
            line_stripped,
        )
        if match:
            # Make sure the description is not just another date (to avoid matching Format 1)
            transaction_date = match.group(1)
            description = match.group(2).strip()
            amount_str = match.group(3)
            
            # Skip if description looks like a date (MM/DD format)
            # Also skip if amount starts with '+' (reward amount, not transaction amount)
            if not re.match(r"^\d{1,2}/\d{1,2}", description) and not amount_str.startswith("+"):
                amount = float(amount_str.replace(",", "").replace("$", ""))
                
                if amount < 0:
                    return {
                        "Date": f"{transaction_date}/{year}",
                        "Description": description,
                        "Debit": None,
                        "Credit": abs(amount),
                    }
                else:
                    return {
                        "Date": f"{transaction_date}/{year}",
                        "Description": description,
                        "Debit": amount,
                        "Credit": None,
                    }
        
        # Format 1b: Two dates with ONLY amount (no description between dates and amount)
        # Example: 12/09 12/10 $3.00 (description is on previous line)
        match = re.match(
            r"^(\d{1,2}/\d{1,2})\s+(\d{1,2}/\d{1,2})\s+(-?\$?[\d,]+\.\d{2})\s*$",
            line_stripped,
        )
        if match:
            transaction_date = match.group(1)
            amount_str = match.group(3)
            amount = float(amount_str.replace(",", "").replace("$", ""))
            
            # Return with placeholder description to be filled from previous line
            if amount < 0:
                return {
                    "Date": f"{transaction_date}/{year}",
                    "Description": "PENDING_DESCRIPTION",
                    "Debit": None,
                    "Credit": abs(amount),
                }
            else:
                return {
                    "Date": f"{transaction_date}/{year}",
                    "Description": "PENDING_DESCRIPTION",
                    "Debit": amount,
                    "Credit": None,
                }
        
        # Format 2: Single date with amount (date and amount only, for multi-line transactions)
        # Example: 12/12 $68.00
        match = re.match(
            r"^(\d{1,2}/\d{1,2})\s+(-?\$?[\d,]+\.\d{2})",
            line_stripped,
        )
        if match:
            transaction_date = match.group(1)
            amount_str = match.group(2)
            amount = float(amount_str.replace(",", "").replace("$", ""))
            
            # Return with placeholder description to be filled later
            if amount < 0:
                return {
                    "Date": f"{transaction_date}/{year}",
                    "Description": "PENDING_DESCRIPTION",
                    "Debit": None,
                    "Credit": abs(amount),
                }
            else:
                return {
                    "Date": f"{transaction_date}/{year}",
                    "Description": "PENDING_DESCRIPTION",
                    "Debit": amount,
                    "Credit": None,
                }
        
        # Format 3: Single date with description (amount on next line, for foreign currency)
        # Example: 12/20 PURO PA DELANTE HERMOSILLO SOMX
        # Example: 05/27 1335 HERMOSILLO HERMOSILLO SOMX
        match = re.match(
            r"^(\d{1,2}/\d{1,2})\s+(.+)",
            line_stripped,
        )
        if match:
            # Check that it's not a single date + amount pattern (Format 2)
            remaining_text = match.group(2).strip()
            if not re.match(r"^-?\$?[\d,]+\.\d{2}\s*$", remaining_text):
                # This is a partial transaction, caller needs to look for amount
                return "PARTIAL"
        
        return None

    def _extract_transactions_from_pdf(self, filename):
        """
        Extract transaction data from a Citi PDF statement.
        Returns a DataFrame with Date, Description, Debit, and Credit columns.

        Citi format has cardholder-specific sections with purchase transactions:
        - MANUEL SALAS section with "Standard Purchases"
        - REYNA VARELA section with transactions

        Transactions are in the format:
        12/09 12/10 DAIRY QUEEN #15096 TUCSON AZ $11.50
        (transaction date, post date, description, amount)
        """
        if not os.path.isfile(filename):
            raise FileNotFoundError(f"File not found: {filename}")

        transactions = []

        # Extract year and month from filename
        year_match = re.search(r"-(\w+)-(\d{4})", filename)
        year = year_match.group(2) if year_match else "2025"
        statement_month = year_match.group(1) if year_match else "jan"
        
        # Map month names to numbers
        month_map = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
        }
        statement_month_num = month_map.get(statement_month.lower(), 1)

        with pdfplumber.open(filename) as pdf:
            in_transaction_section = False
            in_payments_section = False  # Track if we're in Payments, Credits and Adjustments
            current_cardholder = None
            pending_description = None  # For multi-line transactions
            skip_next_line = False  # Track if we should skip the next line (used by Pattern 3)

            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split("\n")

                for i, line in enumerate(lines):
                    line_stripped = line.strip()

                    # Check if we should skip this line (set by Pattern 3 in previous iteration)
                    if skip_next_line:
                        skip_next_line = False
                        continue

                    # Detect cardholder sections
                    if "MANUEL SALAS" in line and "Card ending in" not in line:
                        current_cardholder = "MANUEL SALAS"
                        # Check next line for continuation OR if transactions follow immediately
                        next_line = lines[i+1] if i < len(lines)-1 else ""
                        if "cont'd" not in next_line.lower():
                            # Check if next line looks like a transaction (starts with date pattern)
                            # OR if it's a peso amount line (orphaned amount from previous page)
                            # In the peso amount case, check the line AFTER for transactions
                            next_line_stripped = next_line.strip()
                            if re.match(r"^\d{1,2}/\d{1,2}", next_line_stripped):
                                in_transaction_section = True
                            elif re.match(r"^[\d,]+\.\d+-?\s+MEXICAN\s+PESO", next_line_stripped):
                                # Next line is a peso amount - check line after that for transactions
                                next_next_line = lines[i+2] if i+2 < len(lines) else ""
                                if re.match(r"^\d{1,2}/\d{1,2}", next_next_line.strip()):
                                    in_transaction_section = True
                                else:
                                    in_transaction_section = False
                            else:
                                in_transaction_section = False
                            # DON'T reset in_payments_section here - it can span multiple cardholders
                            # Only reset pending_description if not a continuation
                            if "cont'd" not in line.lower():
                                pending_description = None
                        continue
                    elif "REYNA VARELA" in line and "Card ending in" not in line:
                        current_cardholder = "REYNA VARELA"
                        # Check next line for continuation OR if transactions follow immediately
                        next_line = lines[i+1] if i < len(lines)-1 else ""
                        if "cont'd" not in next_line.lower():
                            # Check if next line looks like a transaction (starts with date pattern)
                            # OR if it's a peso amount line (orphaned amount from previous page)
                            # In the peso amount case, check the line AFTER for transactions
                            next_line_stripped = next_line.strip()
                            if re.match(r"^\d{1,2}/\d{1,2}", next_line_stripped):
                                in_transaction_section = True
                            elif re.match(r"^[\d,]+\.\d+-?\s+MEXICAN\s+PESO", next_line_stripped):
                                # Next line is a peso amount - check line after that for transactions
                                next_next_line = lines[i+2] if i+2 < len(lines) else ""
                                if re.match(r"^\d{1,2}/\d{1,2}", next_next_line.strip()):
                                    in_transaction_section = True
                                else:
                                    in_transaction_section = False
                            else:
                                in_transaction_section = False
                            # DON'T reset in_payments_section here - it can span multiple cardholders
                            # Only reset pending_description if not a continuation
                            if "cont'd" not in line.lower():
                                pending_description = None
                        continue

                    # Check for Mexican peso transactions BEFORE section header checks
                    # because lines with "Earned This Period" can be both peso amounts and section headers
                    # We check peso_match first since it's very specific (must match exact pattern)
                    peso_match = re.match(r"^[\d,]+\.\d+-?\s+MEXICAN\s+PESO\s+(-?\$?[\d,]+\.\d{2})", line_stripped)
                    if peso_match:
                        if pending_description and not in_payments_section:
                            # We have a pending description and found its amount
                            amount_str = peso_match.group(1)
                            amount = float(amount_str.replace(",", "").replace("$", ""))
                            
                            # Extract date and description from pending line
                            desc_match = re.match(r"^(\d{1,2}/\d{1,2})\s+(.*)", pending_description)
                            if desc_match:
                                transaction_date = desc_match.group(1)
                                description = desc_match.group(2).strip()
                                
                                # Remove reward text from description (e.g., "1% on all other purchases +$29.54")
                                # This can appear at the end of foreign currency transaction lines
                                description = re.sub(r'\s+\d%\s+on\s+.*?\+\$[\d,]+\.\d{2}.*$', '', description, flags=re.IGNORECASE)
                                # Also remove section header text like "Costco Cash Back Rewards" appended to transaction lines
                                description = re.sub(r'\s+Costco\s+Cash\s+Back\s+Rewards$', '', description, flags=re.IGNORECASE)
                                description = description.strip()
                                
                                transaction = {
                                    "Date": f"{transaction_date}/{year}",
                                    "Description": description,
                                    "Debit": amount if amount >= 0 else None,
                                    "Credit": abs(amount) if amount < 0 else None,
                                }
                                
                                # Adjust year for transactions in the previous year
                                trans_month = int(transaction_date.split("/")[0])
                                if trans_month > statement_month_num:
                                    prev_year = str(int(year) - 1)
                                    transaction["Date"] = transaction["Date"].replace(f"/{year}", f"/{prev_year}")
                                
                                transactions.append(transaction)
                                logger.debug(f"Parsed foreign currency transaction for {current_cardholder}: {transaction}")
                        # Always clear pending_description and skip to next line after processing MEXICAN PESO line
                        pending_description = None
                        continue

                    # Detect start of transaction sections
                    if "Payments, Credits and Adjustments" in line:
                        in_transaction_section = True
                        in_payments_section = True  # Mark that we're in payments section
                        continue
                    elif (
                        "Standard Purchases" in line
                        or (current_cardholder and "Purchase" in line and "Payments" not in line)
                        # Only match section headers for Costco Cash Back Rewards, not balance summaries
                        # Don't require current_cardholder for "Costco Cash Back Rewards" section header
                        # because the cardholder name may appear AFTER the section header
                        or line_stripped.startswith("Costco Cash Back Rewards")
                        # Match "Earned This Period" section header, but NOT when it's appended to a transaction line
                        # Transaction lines start with MM/DD, section headers don't
                        or ("Earned This Period" in line and "Earned this period" not in line 
                            and not re.match(r"^\d{1,2}/\d{1,2}", line_stripped))
                    ):
                        in_transaction_section = True
                        in_payments_section = False  # Not in payments section
                        # For continuation pages, DO NOT reset pending_description
                        continue

                    # Stop at certain section markers
                    # Check if line starts with these (not just contains)
                    if (
                        line_stripped.startswith("CARDHOLDER SUMMARY")
                        or line_stripped.startswith("Foreign Currency Transactions")
                        or line_stripped.startswith("Interest Charged")
                        or line_stripped.startswith("Fees")
                        or line_stripped.startswith("Year-To-Date Totals")
                        or line_stripped.startswith("2024 Totals Year-to-Date")
                        or (line_stripped.startswith("Costco Cash Back Rewards") 
                            and not re.match(r"^\d{1,2}/\d{1,2}", line_stripped))
                    ):
                        in_transaction_section = False
                        in_payments_section = False
                        pending_description = None
                        continue

                    # Skip header and separator lines
                    # Also skip Costco Cash Back Rewards summary lines (e.g., "Total Earned:", "Earned this period")
                    # BUT don't skip if previous line looks like a merchant description (part of multi-line transaction)
                    # OR if a MEXICAN PESO line follows within a few lines (indicating foreign currency transaction)
                    should_skip_header = (
                        not line_stripped
                        or "Sale Post" in line
                        or "Date Date Description Amount" in line
                        or "Balance:" in line
                        or "New Charges" in line
                        or "Earned this period" in line
                    )
                    
                    # Special handling for "Total Earned:" - only skip if it's a standalone summary line
                    # Don't skip if:
                    # 1. Previous line is a merchant description (indicating multi-line transaction)
                    # 2. A MEXICAN PESO line appears within next 3 lines (foreign currency transaction)
                    # 3. Line is a valid transaction with amount before "Total Earned:" text
                    if "Total Earned:" in line:
                        # Check if this is a valid transaction line (starts with date and has amount before "Total Earned:")
                        # Example: "02/19 02/19 QT 1499 OUTSIDE TUCSON AZ $32.10 Total Earned: $61.68"
                        is_valid_transaction = False
                        if re.match(r"^\d{1,2}/\d{1,2}", line_stripped):
                            # Check if there's an amount before "Total Earned:"
                            before_total_earned = line_stripped.split("Total Earned:")[0]
                            if re.search(r"\$[\d,]+\.\d{2}", before_total_earned):
                                is_valid_transaction = True
                        
                        # Check if previous line is a description (no date, looks like merchant name)
                        prev_is_description = False
                        if i > 0:
                            prev_line = lines[i-1].strip()
                            # Previous line is a description if it doesn't start with a date and is substantial
                            if (prev_line and not re.match(r"^\d{1,2}/\d{1,2}", prev_line) 
                                and len(prev_line) > 5
                                and "MEXICAN PESO" not in prev_line
                                and prev_line[0].isupper()):
                                prev_is_description = True
                        
                        # Check if a MEXICAN PESO line follows (foreign currency transaction)
                        has_peso_following = False
                        for j in range(1, min(4, len(lines) - i)):
                            next_line = lines[i+j].strip()
                            if "MEXICAN PESO" in next_line:
                                has_peso_following = True
                                break
                        
                        # Only skip if it's NOT part of a multi-line or foreign currency transaction
                        # AND not a valid transaction with amount before "Total Earned:"
                        if not prev_is_description and not has_peso_following and not is_valid_transaction:
                            should_skip_header = True
                    
                    if should_skip_header:
                        continue
                    
                    # Check if this is just a date on its own line (for multi-line descriptions)
                    # Example: Description line, then "12/20", then location, then amount
                    # Or: "12/21 for more information" where the date is at the start
                    # BUT skip if it looks like "01/03 REST TABU..." which should be handled as PARTIAL
                    # ALSO skip if we have a pending_description - that should be handled by the pending_description logic
                    # ALSO skip if it has a merchant name followed by reward text (e.g., "05/10 1335 HERMOSILLO... +$29.54")
                    # which should be treated as a PARTIAL transaction, not a date-only line
                    date_only_match = re.match(r"^(\d{1,2}/\d{1,2})\s*(.*)$", line_stripped)
                    
                    # Check if this looks like a transaction with a merchant name (not just date + info text)
                    # A merchant name would have uppercase letters and be reasonably long
                    # Example: "05/10 1335 HERMOSILLO HERMOSILLO SOMX 1% on all other purchases +$29.54"
                    has_merchant_name = False
                    if date_only_match:
                        extra_text = date_only_match.group(2).strip()
                        # Check if there's a merchant name (uppercase text or digits+uppercase) before any reward text
                        # Look for pattern: uppercase/digit words followed by reward text like "1% on..." or "Total Earned"
                        # Allow merchant names starting with digits (like "1335 HERMOSILLO")
                        merchant_match = re.match(r"^([A-Z0-9][A-Z0-9\s\*\-]+?)(?:\s+\d+%\s+on\s+|\s+Total\s+Earned)", extra_text)
                        if merchant_match and len(merchant_match.group(1).strip()) > 5:
                            has_merchant_name = True
                    
                    if date_only_match and not re.match(r"^\d{1,2}/\d{1,2}\s+\d{1,2}/\d{1,2}", line_stripped) and not in_payments_section and not pending_description and not has_merchant_name:
                        # This line starts with a date but not two dates
                        potential_date = date_only_match.group(1)
                        extra_text = date_only_match.group(2).strip()
                        
                        # Skip if the extra text looks like it's part of a regular transaction
                        # (has an amount or is a known vendor pattern)
                        # OR if it looks like a merchant description (uppercase letters, long enough)
                        # BUT allow lines with reward/informational text like "Total Earned:", "1% on all other"
                        # IMPORTANT: Check for amount BEFORE checking for info text - if there's an amount before
                        # "for more information", it's a regular transaction (e.g., "04/19 DOLLAR GENERAL $7.75 for more information")
                        has_amount_in_text = re.search(r"\$[\d,]+\.\d{2}", extra_text)
                        is_reward_or_info_text = ("Total Earned" in extra_text or 
                                                   "on all other" in extra_text or
                                                   ("for more information" in extra_text.lower() and not has_amount_in_text))
                        
                        # Allow lines with amounts if they're reward text (e.g., "Total Earned: $63.02")
                        has_transaction_amount = (has_amount_in_text and not is_reward_or_info_text)
                        
                        # Check if this looks like a merchant name (multiple uppercase words or digits+uppercase)
                        # Examples: "1335 HERMOSILLO HERMOSILLO SOMX", "COSTCO WHSE #1079"
                        # NOT merchant names: "for more information", "Total Earned: $100"
                        looks_like_merchant = (
                            len(extra_text) > 10 
                            and (extra_text[0].isupper() or extra_text[0].isdigit())
                            and len([w for w in extra_text.split() if w and (w[0].isupper() or w[0].isdigit())]) >= 2
                        )
                        
                        if (not has_transaction_amount
                            and not extra_text.startswith("AUTOPAY")
                            and not looks_like_merchant
                            and (is_reward_or_info_text or not (len(extra_text) > 10 and extra_text[0].isupper()))):
                            # Check if previous line was a description (no date at start)
                            if i > 0:
                                prev_line = lines[i-1].strip()
                                # Skip MEXICAN PESO lines - they are amounts, not descriptions
                                if (prev_line and not re.match(r"^\d{1,2}/\d{1,2}", prev_line) 
                                    and len(prev_line) > 5
                                    and "MEXICAN PESO" not in prev_line):
                                    # This looks like a date following a description
                                    # Store it and the description together
                                    pending_description = f"{potential_date} {prev_line}"
                            continue

                    # Only process if we're in a transaction section
                    if not in_transaction_section:
                        continue
                    
                    # Check if this is a description-only line (no date at start, looks like vendor name)
                    # This handles cases like:
                    # 1. "BREW CITY BRAND - AIRPORTMILWAUKEE" followed by "02/28 02/28 $23.74"
                    # 2. "THE WINDOW DEPOT BRANCH 3520-7753142" followed by "01/24 $1,373.97 Total Earned: $100.73"
                    # 3. "GOB EDO SONORA E COM HERMOSILLO" followed by "12/20 Total Earned: $63.02" then "SOMX" then peso amount
                    # BUT exclude continuation lines like "WWW.AMAZON.COWA" (URL fragments, all uppercase single word)
                    if (not re.match(r"^\d{1,2}/\d{1,2}", line_stripped) 
                        and len(line_stripped) > 5
                        and not line_stripped.lower().startswith("cont'd")
                        and not line_stripped.startswith("Page ")
                        and line_stripped[0].isupper()
                        and not re.match(r"^WWW\.", line_stripped, re.IGNORECASE)  # Exclude URL fragments
                        and len(line_stripped.split()) >= 2):  # Must have at least 2 words (not just "SOMX" or "WWW.AMAZON.COWA")
                        # Check if next line has the pattern: two dates + amount only OR single date + amount
                        # OR if next line starts with date AND a MEXICAN PESO line follows (foreign currency)
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            # Pattern 1: two dates + amount only (e.g., "02/28 02/28 $23.74")
                            if re.match(r"^\d{1,2}/\d{1,2}\s+\d{1,2}/\d{1,2}\s+(-?\$?[\d,]+\.\d{2})\s*$", next_line):
                                # This is a description for the next line's transaction
                                pending_description = line_stripped
                                continue
                            # Pattern 2: single date + amount (with optional extra text after)
                            # e.g., "01/24 $1,373.97 Total Earned: $100.73" or "01/25 $156.53"
                            elif re.match(r"^\d{1,2}/\d{1,2}\s+(-?\$?[\d,]+\.\d{2})", next_line):
                                # This is a description for the next line's transaction
                                # We'll use date_only_match logic to handle it, but mark description as pending
                                pending_description = line_stripped
                                continue
                            # Pattern 3: next line starts with date AND a MEXICAN PESO line follows within 3 lines
                            # This handles foreign currency transactions with multi-line descriptions
                            elif re.match(r"^\d{1,2}/\d{1,2}", next_line):
                                # Check if a MEXICAN PESO line appears within next few lines
                                has_peso_following = False
                                for j in range(1, min(5, len(lines) - i)):
                                    check_line = lines[i+j].strip()
                                    if "MEXICAN PESO" in check_line:
                                        has_peso_following = True
                                        break
                                
                                if has_peso_following:
                                    # Save as pending description with the date from next line
                                    date_match = re.match(r"^(\d{1,2}/\d{1,2})", next_line)
                                    if date_match:
                                        pending_description = f"{date_match.group(1)} {line_stripped}"
                                        # Skip the next line (the date + text line) since we extracted the date from it
                                        skip_next_line = True
                                        continue

                    # Check if we have a pending description and current line is date + amount
                    # This handles: description on previous line, then "MM/DD $Amount [optional extra text]"
                    # Example: "THE WINDOW DEPOT BRANCH..." followed by "01/24 $1,373.97 Total Earned: $100.73"
                    # IMPORTANT: Only match single date + amount, NOT two dates (Format 1 transactions)
                    # Use negative lookahead to exclude lines with two dates
                    if pending_description and re.match(r"^\d{1,2}/\d{1,2}\s+(?!\d{1,2}/\d{1,2})(-?\$?[\d,]+\.\d{2})", line_stripped):
                        date_amount_match = re.match(r"^(\d{1,2}/\d{1,2})\s+(-?\$?[\d,]+\.\d{2})", line_stripped)
                        if date_amount_match:
                            transaction_date = date_amount_match.group(1)
                            amount_str = date_amount_match.group(2)
                            amount = float(amount_str.replace(",", "").replace("$", ""))
                            
                            transaction = {
                                "Date": f"{transaction_date}/{year}",
                                "Description": pending_description,
                                "Debit": amount if amount >= 0 else None,
                                "Credit": abs(amount) if amount < 0 else None,
                            }
                            
                            # Adjust year for transactions in the previous year
                            trans_month = int(transaction_date.split("/")[0])
                            if trans_month > statement_month_num:
                                prev_year = str(int(year) - 1)
                                transaction["Date"] = transaction["Date"].replace(f"/{year}", f"/{prev_year}")
                            
                            transactions.append(transaction)
                            logger.debug(f"Parsed transaction with pending description for {current_cardholder}: {transaction}")
                            pending_description = None
                            continue

                    # Try to parse the line as a transaction
                    transaction = self._parse_citi_transaction_line(line, year)
                    
                    if transaction == "PARTIAL":
                        # This is a line with date and description but no amount
                        # Save the description for the next line
                        # BUT don't overwrite if already set (e.g., by Pattern 3 in description-only detection)
                        if not pending_description:
                            pending_description = line_stripped
                        continue
                    elif transaction and isinstance(transaction, dict):
                        # Check if this transaction needs a description from previous line
                        if transaction.get("Description") == "PENDING_DESCRIPTION":
                            if pending_description:
                                # Extract description from the pending line
                                desc_match = re.match(r"^\d{1,2}/\d{1,2}\s+(.*)", pending_description)
                                if desc_match:
                                    transaction["Description"] = desc_match.group(1).strip()
                                else:
                                    transaction["Description"] = pending_description
                                pending_description = None
                            else:
                                # Try to find description in previous lines
                                # Look back a few lines for a description
                                for j in range(max(0, i-3), i):
                                    prev_line = lines[j].strip()
                                    # Skip MEXICAN PESO lines - they are amounts, not descriptions
                                    if (prev_line and not re.match(r"^\d{1,2}/\d{1,2}", prev_line) 
                                        and len(prev_line) > 5
                                        and "MEXICAN PESO" not in prev_line):
                                        # This might be the description
                                        transaction["Description"] = prev_line
                                        break
                        else:
                            # Reset pending description if we got a complete transaction
                            pending_description = None
                        
                        # Adjust year for transactions in the previous year
                        # (e.g., December transactions in a January statement)
                        trans_date = transaction["Date"]
                        trans_month = int(trans_date.split("/")[0])
                        
                        # If transaction month is greater than statement month, 
                        # it's from the previous year
                        if trans_month > statement_month_num:
                            prev_year = str(int(year) - 1)
                            transaction["Date"] = trans_date.replace(f"/{year}", f"/{prev_year}")
                        
                        transactions.append(transaction)
                        logger.debug(
                            f"Parsed transaction for {current_cardholder}: {transaction}"
                        )

        if not transactions:
            logger.warning(f"No transactions found in PDF: {filename}")
            raise ValueError(f"No transactions found in PDF: {filename}")

        df = pd.DataFrame(transactions)
        df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")
        df["Debit"] = pd.to_numeric(df["Debit"], errors="coerce")
        df["Credit"] = pd.to_numeric(df["Credit"], errors="coerce")

        # Sort by date
        df = df.sort_values("Date").reset_index(drop=True)

        return df

    @staticmethod
    def load_expenses(filename):
        """Load only expenses (debits) from a PDF file."""
        loader = CitiFileLoader()
        df = loader._extract_transactions_from_pdf(filename)
        return df[df["Debit"].notnull()]

    @staticmethod
    def load_credits(filename):
        """Load only credits from a PDF file."""
        loader = CitiFileLoader()
        df = loader._extract_transactions_from_pdf(filename)
        return df[df["Credit"].notnull()]

    @staticmethod
    def load_expenses_and_credits(filename):
        """
        Load both expenses (debits) and credits from a PDF file and combine them.
        Returns a DataFrame with both debits and credits.
        """
        loader = CitiFileLoader()
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
        citi_file_loader = CitiFileLoader()

        for filename in file_list:
            if os.path.exists(filename):
                df = citi_file_loader.load_expenses_and_credits(filename)
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
