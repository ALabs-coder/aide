#!/usr/bin/env python3
"""
ANDHRA PRADESH GRAMEENA BANK (APGVB) PDF Statement Extractor
Specialized extractor for APGVB PDF statements
"""

import pypdf
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from .base_extractor import BaseBankExtractor

logger = logging.getLogger(__name__)


class APGVBExtractor(BaseBankExtractor):
    """Extract comprehensive data from APGVB PDF statements"""

    def __init__(self):
        # Initialize parent class first
        super().__init__()
        self.statement_metadata = {}
        self.financial_summary = {}
        self.transactions = []

    def get_bank_name(self) -> str:
        """Return the bank name this extractor handles"""
        return "Andhra Pradesh Grameena Bank"

    def get_version(self) -> str:
        """Return the version of this extractor"""
        return "1.0.0"

    def get_supported_capabilities(self) -> List[str]:
        """Return list of capabilities supported by this extractor"""
        return ["multi_page", "transactions", "financial_summary", "account_metadata", "statement_period", "balance_calculation", "transaction_types"]

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
                        logger.info(f"APGVB PDF is encrypted, attempting to decrypt with provided password (length: {len(password)})")
                        result = pdf_reader.decrypt(password)
                        if result == 0:
                            # Only try whitespace variations - password is case sensitive!
                            trimmed_password = password.strip()
                            if trimmed_password != password:
                                logger.info(f"Trying APGVB trimmed password (removed whitespace)")
                                result = pdf_reader.decrypt(trimmed_password)
                                if result != 0:
                                    logger.info(f"APGVB PDF decrypted successfully with trimmed password")
                                else:
                                    raise ValueError(f"Failed to decrypt APGVB PDF with provided password (length: {len(password)}). Note: PDF passwords are case-sensitive.")
                            else:
                                raise ValueError(f"Failed to decrypt APGVB PDF with provided password (length: {len(password)}). Note: PDF passwords are case-sensitive.")
                        else:
                            logger.info("APGVB PDF decrypted successfully with original password")
                    else:
                        raise ValueError("APGVB PDF is encrypted but no password provided")

                logger.info(f"Processing APGVB statement with {len(pdf_reader.pages)} pages")

                # Extract metadata from first few pages
                self.statement_metadata = self._extract_statement_metadata(pdf_reader)

                # Extract all transactions from all pages
                self.transactions = self._extract_all_transactions(pdf_reader)

                # Calculate financial summary
                self.financial_summary = self._calculate_financial_summary()

                return {
                    "total_transactions": len(self.transactions),
                    "processed_at": datetime.now().isoformat(),
                    "statement_metadata": self.statement_metadata,
                    "financial_summary": self.financial_summary,
                    "transactions": self.transactions,
                    "extractor_metadata": self.get_extraction_metadata()
                }

        except Exception as e:
            logger.error(f"Error extracting APGVB statement: {e}")
            raise

    def _extract_statement_metadata(self, pdf_reader) -> Dict:
        """Extract account and statement metadata from first few pages"""
        metadata = {
            "bank_name": self.bank_name,
            "currency": "INR"
        }

        # Get text from first two pages to extract all metadata
        combined_text = ""
        for i in range(min(2, len(pdf_reader.pages))):
            combined_text += pdf_reader.pages[i].extract_text() + "\n"

        lines = combined_text.split('\n')

        for i, line in enumerate(lines):
            line = line.strip()

            # Extract account number from "Account No : 716411100000441"
            if line.startswith('Account No') or 'Account No' in line:
                acc_match = re.search(r'Account No\s*:\s*(\d+)', line)
                if acc_match:
                    metadata["account_number"] = acc_match.group(1)

            # Extract customer name from "Account No : 716411100000441 INR KOVVURI SITA REDDY"
            if 'Account No' in line and 'INR' in line:
                # Pattern: Account No : 716411100000441 INR KOVVURI SITA REDDY
                name_match = re.search(r'Account No\s*:\s*\d+\s+INR\s+(.+)', line)
                if name_match:
                    metadata["customer_name"] = name_match.group(1).strip()

            # Extract account type from "Gl Sub Head Code : 12020 CURRENT DEPOSITS - OTHERS"
            if 'CURRENT DEPOSITS' in line or 'SAVINGS' in line:
                acc_type_match = re.search(r'\d+\s+(.+)', line)
                if acc_type_match:
                    metadata["account_type"] = acc_type_match.group(1).strip()

            # Extract service outlet/branch from "Service OutLet : 7164 POLAMURU EAST"
            if line.startswith('Service OutLet') or 'Service OutLet' in line:
                branch_match = re.search(r'Service OutLet\s*:\s*\d+\s+(.+)', line)
                if branch_match:
                    metadata["home_branch"] = branch_match.group(1).strip()

            # Extract statement period from "Period : 01-04-2024 to 31-03-2025"
            if line.startswith('Period') or 'Customer Account Ledger Report from' in line:
                # Handle both formats: "Period : 01-04-2024 to 31-03-2025" and "from 01-04-2024 to 31-03-2025"
                period_match = re.search(r'(?:Period\s*:\s*|from\s+)(\d{2}-\d{2}-\d{4})\s+to\s+(\d{2}-\d{2}-\d{4})', line)
                if period_match:
                    metadata["statement_period"] = {
                        "from_date": period_match.group(1),
                        "to_date": period_match.group(2)
                    }

            # Extract opening balance from "Opening Balance : 0"
            if line.startswith('Opening Balance'):
                balance_match = re.search(r'Opening Balance\s*:\s*([\d,]+(?:\.\d+)?)', line)
                if balance_match:
                    balance_str = balance_match.group(1).replace(',', '')
                    metadata["opening_balance"] = float(balance_str)

        return metadata

    def _extract_all_transactions(self, pdf_reader) -> List[Dict]:
        """Extract transactions from all pages"""
        all_transactions = []
        transaction_counter = 1

        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            if not page_text:
                continue

            page_transactions = self._extract_transactions_from_page(page_text, page_num + 1, transaction_counter)
            all_transactions.extend(page_transactions)
            transaction_counter += len(page_transactions)

        return all_transactions

    def _extract_transactions_from_page(self, page_text: str, page_num: int, start_counter: int) -> List[Dict]:
        """Extract transactions from a single page"""
        transactions = []
        lines = page_text.split('\n')
        transaction_counter = start_counter

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip header lines and non-transaction lines
            if any(keyword in line for keyword in [
                'GL.', 'Date', 'Value', 'Instrmnt', 'Particulars', 'Transaction',
                'Debit Amount', 'Credit Amount', 'Balance', 'Entry', 'Verified',
                'User Id', 'Order by GL. Date', 'Page Total', 'B/F Balance'
            ]):
                i += 1
                continue

            # Skip separator lines and empty lines
            if not line or line.startswith('---') or 'Page' in line:
                i += 1
                continue

            # Look for transaction pattern: DD-MM-YYYY DD-MM-YYYY TRANSACTION_DETAILS
            date_pattern = r'^(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(.+)'
            date_match = re.match(date_pattern, line)

            if date_match:
                try:
                    # This is a transaction line
                    gl_date = date_match.group(1)
                    # value_date = date_match.group(2)  # Not currently used
                    full_line_after_dates = date_match.group(3).strip()

                    # Find amounts in the transaction line or next few lines
                    amounts_info = self._extract_transaction_amounts(lines, i)
                    if amounts_info:
                        debit_amount, credit_amount, balance, amount_line_offset = amounts_info

                        # Extract clean transaction description (remove amounts, balance, user IDs)
                        transaction_details = self._clean_transaction_description(full_line_after_dates)

                        # Determine transaction type
                        transaction_type = "Credit" if credit_amount and credit_amount != "0.00" else "Debit"

                        transaction = {
                            'S.No': str(transaction_counter),
                            'Date': gl_date,
                            'Transaction_ID': '',  # APGVB doesn't have explicit transaction IDs
                            'Remarks': transaction_details,
                            'Debit': debit_amount if debit_amount and debit_amount != "0.00" else "",
                            'Credit': credit_amount if credit_amount and credit_amount != "0.00" else "",
                            'Balance': balance,
                            'Transaction_Type': transaction_type,
                            'Page_Number': page_num
                        }

                        transactions.append(transaction)
                        transaction_counter += 1

                        # Skip past the amount line
                        i += amount_line_offset + 1
                    else:
                        i += 1

                except Exception as e:
                    logger.warning(f"Error parsing transaction on page {page_num}: {line[:50]}... - {e}")
                    i += 1
            else:
                i += 1

        return transactions

    def _extract_transaction_amounts(self, lines: List[str], start_index: int) -> Optional[Tuple[str, str, str, int]]:
        """
        Extract debit amount, credit amount, and balance from transaction lines.
        Uses balance change calculation for sustainable debit/credit detection.
        """
        if not hasattr(self, '_previous_balance'):
            self._previous_balance = 0.0

        for offset in range(min(4, len(lines) - start_index)):
            line = lines[start_index + offset].strip()

            if not line or line.startswith('---'):
                continue

            balance_pattern = r'([\d,]+\.?\d*)Cr\s+'
            balance_match = re.search(balance_pattern, line)

            if balance_match:
                current_balance = float(balance_match.group(1).replace(',', ''))

                before_balance = line[:balance_match.start()].strip()
                amount_pattern = r'([\d,]+\.?\d*)'
                amounts = re.findall(amount_pattern, before_balance)

                if amounts:
                    clean_amounts = [float(amt.replace(',', '')) for amt in amounts
                                   if amt.replace(',', '').replace('.', '').isdigit()]

                    if len(clean_amounts) >= 1:
                        transaction_amount = clean_amounts[-1]
                        balance_change = current_balance - self._previous_balance
                        self._previous_balance = current_balance

                        if balance_change > 0:
                            return "0.00", str(transaction_amount), str(current_balance), offset
                        elif balance_change < 0:
                            return str(transaction_amount), "0.00", str(current_balance), offset
                        else:
                            return "0.00", str(transaction_amount), str(current_balance), offset

        return None

    def _clean_transaction_description(self, full_line: str) -> str:
        """Extract clean transaction description by removing amounts, balance, and user IDs."""
        amount_pattern = r'\s+[\d,]+\.?\d*\s'
        match = re.search(amount_pattern, full_line)

        if match:
            return full_line[:match.start()].strip()
        else:
            balance_pattern = r'\s+[\d,]+\.?\d*Cr.*$'
            return re.sub(balance_pattern, '', full_line).strip()

    def _calculate_financial_summary(self) -> Dict:
        """Calculate financial summary from transactions"""
        if not self.transactions:
            return {}

        # Get opening balance from metadata or first transaction
        opening_balance = self.statement_metadata.get("opening_balance", 0.0)

        # Get closing balance from last transaction
        closing_balance = 0.0
        if self.transactions:
            last_balance_str = self.transactions[-1]['Balance']
            if last_balance_str:
                closing_balance = float(last_balance_str.replace(',', ''))

        # Calculate totals from Debit and Credit fields
        total_debits = 0.0
        total_credits = 0.0

        for transaction in self.transactions:
            if transaction['Debit'] and transaction['Debit'] != "":
                total_debits += float(transaction['Debit'].replace(',', ''))
            if transaction['Credit'] and transaction['Credit'] != "":
                total_credits += float(transaction['Credit'].replace(',', ''))

        net_change = total_credits - total_debits

        # Get date range from transactions
        dates = [t['Date'] for t in self.transactions if t['Date']]

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


def extract_apgvb_statement(pdf_path: str, password: Optional[str] = None) -> Dict:
    """
    Main function to extract APGVB statement data

    Args:
        pdf_path (str): Path to APGVB PDF statement
        password (str): Password if PDF is encrypted

    Returns:
        Dict: Complete statement data including metadata, summary, and transactions
    """
    extractor = APGVBExtractor()
    return extractor.extract_complete_statement(pdf_path, password)