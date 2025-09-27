#!/usr/bin/env python3
"""
Canara Bank PDF Statement Extractor
Specialized extractor for Canara Bank PDF statements
"""

import pypdf
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from .base_extractor import BaseBankExtractor

logger = logging.getLogger(__name__)


class CanaraBankExtractor(BaseBankExtractor):
    """Extract comprehensive data from Canara Bank PDF statements"""

    def __init__(self):
        # Initialize parent class first
        super().__init__()
        self.statement_metadata = {}
        self.financial_summary = {}
        self.transactions = []

    def get_bank_name(self) -> str:
        """Return the bank name this extractor handles"""
        return "Canara Bank"

    def get_version(self) -> str:
        """Return the version of this extractor"""
        return "1.0.0"

    def get_supported_capabilities(self) -> List[str]:
        """Return list of capabilities supported by this extractor"""
        return ["password_protected", "multi_page", "transactions", "financial_summary", "account_metadata", "statement_period"]

    def extract_complete_statement(self, pdf_path: str, password: Optional[str] = None) -> Dict:
        """
        Extract complete statement data including metadata, summary, and transactions

        Args:
            pdf_path (str): Path to the PDF file
            password (str): Password to unlock PDF if protected

        Returns:
            Dict: Complete statement data
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)

                # Decrypt first if encrypted
                if pdf_reader.is_encrypted:
                    if password:
                        logger.info(f"Canara Bank PDF is encrypted, attempting to decrypt with provided password (length: {len(password)})")
                        result = pdf_reader.decrypt(password)
                        if result == 0:
                            # Only try whitespace variations - password is case sensitive!
                            trimmed_password = password.strip()
                            if trimmed_password != password:
                                logger.info(f"Trying Canara Bank trimmed password (removed whitespace)")
                                result = pdf_reader.decrypt(trimmed_password)
                                if result != 0:
                                    logger.info(f"Canara Bank PDF decrypted successfully with trimmed password")
                                else:
                                    raise ValueError(f"Failed to decrypt Canara Bank PDF with provided password (length: {len(password)}). Note: PDF passwords are case-sensitive.")
                            else:
                                raise ValueError(f"Failed to decrypt Canara Bank PDF with provided password (length: {len(password)}). Note: PDF passwords are case-sensitive.")
                        else:
                            logger.info("Canara Bank PDF decrypted successfully with original password")
                    else:
                        raise ValueError("Canara Bank PDF is encrypted but no password provided")

                logger.info(f"Processing Canara Bank statement with {len(pdf_reader.pages)} pages")

                # Extract metadata from first page
                first_page_text = pdf_reader.pages[0].extract_text()
                self.statement_metadata = self._extract_statement_metadata(first_page_text)

                # Extract all transactions from all pages
                self.transactions = self._extract_all_transactions(pdf_reader)

                # Calculate financial summary
                self.financial_summary = self._calculate_financial_summary()

                return {
                    "total_transactions": len(self.transactions),
                    "processed_at": datetime.now().isoformat(),
                    "statement_metadata": self.statement_metadata,
                    "financial_summary": self.financial_summary,
                    "transactions": self.transactions
                }

        except Exception as e:
            logger.error(f"Error extracting Canara Bank statement: {e}")
            raise

    def _extract_statement_metadata(self, first_page_text: str) -> Dict:
        """Extract account and statement metadata from first page"""
        metadata = {
            "bank_name": self.bank_name,
            "currency": "INR"
        }

        lines = first_page_text.split('\n')

        for i, line in enumerate(lines):
            line = line.strip()

            # Extract account number from statement header
            # Format: "Statement for A/c 4477101002157 between 01-Apr-2024 and 31-Mar-2025"
            if line.startswith('Statement for A/c'):
                acc_match = re.search(r'Statement for A/c\s+(\d+)', line)
                if acc_match:
                    metadata["account_number"] = acc_match.group(1)

                # Extract statement period from same line
                period_match = re.search(r'between\s+(\d{2}-[A-Za-z]{3}-\d{4})\s+and\s+(\d{2}-[A-Za-z]{3}-\d{4})', line)
                if period_match:
                    metadata["statement_period"] = {
                        "from_date": period_match.group(1),
                        "to_date": period_match.group(2)
                    }

            # Extract customer ID (map to Union Bank's field name)
            if line.startswith('Customer Id'):
                cid_match = re.search(r'Customer Id\s+(\d+)', line)
                if cid_match:
                    metadata["customer_cif_id"] = cid_match.group(1)

            # Extract customer name
            if line.startswith('Name'):
                name_match = re.search(r'Name\s+(.+)', line)
                if name_match:
                    metadata["customer_name"] = name_match.group(1).strip()

            # Extract phone number (map to Union Bank's field name)
            if line.startswith('Phone'):
                phone_match = re.search(r'Phone\s+(\+?\d+)', line)
                if phone_match:
                    metadata["mobile_number"] = phone_match.group(1)

            # Extract address (multi-line)
            if line.startswith('Address'):
                address_parts = []
                address_line = line.replace('Address', '').strip()
                if address_line:
                    address_parts.append(address_line)

                # Check next few lines for address continuation
                j = i + 1
                while j < len(lines) and j < i + 4:  # Look at next 3 lines max
                    next_line = lines[j].strip()
                    if next_line and not any(keyword in next_line for keyword in
                                           ['Branch Code', 'Branch Name', 'IFSC', 'Date']):
                        address_parts.append(next_line)
                    else:
                        break
                    j += 1

                if address_parts:
                    metadata["address"] = " ".join(address_parts)

            # Extract branch code
            if 'Branch Code' in line:
                branch_code_match = re.search(r'Branch Code\s+(\d+)', line)
                if branch_code_match:
                    metadata["branch_code"] = branch_code_match.group(1)

            # Extract branch name (map to Union Bank's field name)
            if 'Branch Name' in line:
                branch_name_match = re.search(r'Branch Name\s+(.+)', line)
                if branch_name_match:
                    metadata["home_branch"] = branch_name_match.group(1).strip()

            # Extract IFSC code
            if 'IFSC Code' in line:
                ifsc_match = re.search(r'IFSC Code\s+([A-Z0-9]+)', line)
                if ifsc_match:
                    metadata["ifsc_code"] = ifsc_match.group(1)

        return metadata

    def _extract_all_transactions(self, pdf_reader) -> List[Dict]:
        """Extract transactions from all pages"""
        all_transactions = []
        opening_balance = None

        # First extract opening balance from first page
        first_page_text = pdf_reader.pages[0].extract_text()
        opening_balance = self._extract_opening_balance(first_page_text)

        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            if not page_text:
                continue

            page_transactions = self._extract_transactions_from_page(page_text, page_num + 1, opening_balance)
            all_transactions.extend(page_transactions)

        return all_transactions

    def _extract_opening_balance(self, first_page_text: str) -> float:
        """Extract opening balance from first page"""
        lines = first_page_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('Opening Balance'):
                # Extract number from "Opening Balance 9,374.06"
                balance_match = re.search(r'Opening Balance\s+([\d,]+\.?\d*)', line)
                if balance_match:
                    return float(balance_match.group(1).replace(',', ''))
        return 0.0

    def _extract_transactions_from_page(self, page_text: str, page_num: int, opening_balance: float = None) -> List[Dict]:
        """Extract transactions from a single page"""
        transactions = []
        lines = page_text.split('\n')
        transaction_counter = 1  # Add serial number counter

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip header lines
            if any(keyword in line for keyword in ['Date', 'Particulars', 'Deposits', 'Withdrawals', 'Balance']):
                i += 1
                continue

            # Skip opening balance line
            if line.startswith('Opening Balance'):
                i += 1
                continue

            # Look for transaction starting with date pattern DD-MM-YYYY
            date_pattern = r'^(\d{2}-\d{2}-\d{4})'
            date_match = re.match(date_pattern, line)

            if date_match:
                try:
                    # This is a transaction, combine all lines until next transaction or "Chq:" pattern
                    combined_transaction, amounts_line = self._combine_transaction_lines(lines, i)
                    transaction = self._parse_combined_transaction(combined_transaction, amounts_line, page_num, transaction_counter)

                    if transaction:
                        transactions.append(transaction)
                        transaction_counter += 1  # Increment counter for next transaction

                    # Skip to next potential transaction
                    i = self._find_next_transaction_start(lines, i)

                except Exception as e:
                    logger.warning(f"Error parsing transaction on page {page_num}: {line[:50]}... - {e}")
                    i += 1
            else:
                i += 1

        return transactions

    def _combine_transaction_lines(self, lines: List[str], start_index: int) -> Tuple[str, str]:
        """Combine transaction lines until we find the complete transaction"""
        combined_lines = []
        amounts_line = ""
        i = start_index

        # Keep combining lines until we find "Chq:" which indicates the end
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            combined_lines.append(line)

            # Stop if we find "Chq:" as it marks the end
            if line.startswith('Chq:'):
                # The next line should contain the amounts
                if i + 1 < len(lines):
                    amounts_line = lines[i + 1].strip()
                break

            # Stop if we hit next transaction (starts with date)
            if i > start_index and re.match(r'^\d{2}-\d{2}-\d{4}', line):
                combined_lines.pop()  # Remove this line as it's the next transaction
                break

            i += 1

        return " ".join(combined_lines), amounts_line

    def _find_next_transaction_start(self, lines: List[str], current_index: int) -> int:
        """Find the start of the next transaction"""
        i = current_index + 1

        while i < len(lines):
            line = lines[i].strip()
            if re.match(r'^\d{2}-\d{2}-\d{4}', line):
                return i
            i += 1

        return len(lines)  # End of page

    def _parse_combined_transaction(self, combined_text: str, amounts_line: str, page_num: int, serial_number: int) -> Optional[Dict]:
        """Parse a complete combined transaction text using improved non-regex approach"""
        try:
            # 1. Extract date from start of combined_text
            words = combined_text.split()
            if not words:
                return None

            transaction_date = words[0]  # First word should be the date

            # Validate date format
            if not (len(transaction_date) == 10 and transaction_date.count('-') == 2):
                return None

            # Note: This PDF has no Transaction_ID or UPI_Reference fields
            # Everything is just part of the Particulars column

            # 3. Extract amounts from the amounts_line using simple parsing
            amount_str = "0.00"
            balance_str = "0.00"

            if amounts_line:
                # Split amounts line and find numeric values
                amount_parts = amounts_line.split()
                numeric_values = []

                for part in amount_parts:
                    # Check if it's a monetary value (contains decimal and digits)
                    if '.' in part and part.replace(',', '').replace('.', '').isdigit():
                        numeric_values.append(part.replace(',', ''))

                if len(numeric_values) >= 2:
                    # First number is amount, second is balance
                    amount_str = numeric_values[0]
                    balance_str = numeric_values[1]
                elif len(numeric_values) == 1:
                    # Only one number, likely balance
                    balance_str = numeric_values[0]

            # 4. Determine transaction type
            transaction_type = "Credit"  # Default
            if '/DR/' in combined_text:
                transaction_type = "Debit"

            # 5. Extract particulars - the ENTIRE description from Particulars column
            # This includes everything between the date and before the amounts
            particulars_start = len(transaction_date) + 1  # Skip date and space
            particulars = combined_text[particulars_start:].strip()

            # 6. Prepare clean amounts for separate Debit/Credit fields
            debit_amount = ""
            credit_amount = ""

            if transaction_type == "Debit":
                debit_amount = amount_str
            else:
                credit_amount = amount_str

            transaction = {
                'S.No': str(serial_number),
                'Date': transaction_date,
                'Remarks': particulars,  # Complete Particulars column content
                'Debit': debit_amount,
                'Credit': credit_amount,
                'Balance': balance_str,
                'Transaction_Type': transaction_type,
                'Page_Number': page_num
            }

            return transaction

        except Exception as e:
            logger.error(f"Error parsing transaction: {combined_text[:50]}... amounts: {amounts_line} - {e}")
            return None

    def _calculate_financial_summary(self) -> Dict:
        """Calculate financial summary from transactions"""
        if not self.transactions:
            return {}

        # Sort transactions by date for proper calculation
        sorted_transactions = sorted(self.transactions, key=lambda x: datetime.strptime(x['Date'], '%d-%m-%Y'))

        # Get opening and closing balances from balance field
        first_transaction = sorted_transactions[0]
        last_transaction = sorted_transactions[-1]

        opening_balance = float(last_transaction['Balance'].replace(',', '')) if last_transaction['Balance'] else 0.0
        closing_balance = float(first_transaction['Balance'].replace(',', '')) if first_transaction['Balance'] else 0.0

        # Calculate totals from Debit and Credit fields
        total_debits = 0.0
        total_credits = 0.0

        for t in self.transactions:
            if t['Debit'] and t['Debit'] != "":
                total_debits += float(t['Debit'].replace(',', ''))
            if t['Credit'] and t['Credit'] != "":
                total_credits += float(t['Credit'].replace(',', ''))

        net_change = total_credits - total_debits

        # Get date range from transactions
        dates = [t['Date'] for t in self.transactions]

        return {
            "opening_balance": opening_balance,
            "closing_balance": closing_balance,
            "total_debits": total_debits,
            "total_credits": total_credits,
            "net_change": net_change,
            "transaction_count": len(self.transactions),
            "date_range": {
                "from_date": min(dates) if dates else None,
                "to_date": max(dates) if dates else None
            }
        }


def extract_canara_bank_statement(pdf_path: str, password: Optional[str] = None) -> Dict:
    """
    Main function to extract Canara Bank statement data

    Args:
        pdf_path (str): Path to Canara Bank PDF statement
        password (str): Password if PDF is encrypted

    Returns:
        Dict: Complete statement data including metadata, summary, and transactions
    """
    extractor = CanaraBankExtractor()
    return extractor.extract_complete_statement(pdf_path, password)


# Backward compatibility function for existing code
def extract_canara_bank_statement(pdf_path: str, password: Optional[str] = None) -> Dict:
    """
    Backward compatibility wrapper function

    Args:
        pdf_path (str): Path to the PDF file
        password (str, optional): Password for encrypted PDFs

    Returns:
        Dict: Complete statement data
    """
    extractor = CanaraBankExtractor()
    return extractor.extract_complete_statement(pdf_path, password)

