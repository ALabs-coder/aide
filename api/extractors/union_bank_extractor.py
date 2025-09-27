#!/usr/bin/env python3
"""
Union Bank PDF Statement Extractor
Specialized extractor for Union Bank of India PDF statements
"""

import pypdf
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from .base_extractor import BaseBankExtractor

logger = logging.getLogger(__name__)


class UnionBankExtractor(BaseBankExtractor):
    """Extract comprehensive data from Union Bank PDF statements"""

    def __init__(self):
        # Initialize parent class first
        super().__init__()
        self.statement_metadata = {}
        self.financial_summary = {}
        self.transactions = []

    def get_bank_name(self) -> str:
        """Return the bank name this extractor handles"""
        return "Union Bank of India"

    def get_version(self) -> str:
        """Return the version of this extractor"""
        return "1.0.0"

    def get_supported_capabilities(self) -> List[str]:
        """Return list of capabilities supported by this extractor"""
        return ["password_protected", "multi_page", "transactions", "account_metadata", "statement_period"]

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
                        logger.info(f"Union Bank PDF is encrypted, attempting to decrypt with provided password (length: {len(password)})")
                        result = pdf_reader.decrypt(password)
                        if result == 0:
                            # Only try whitespace variations - password is case sensitive!
                            trimmed_password = password.strip()
                            if trimmed_password != password:
                                logger.info(f"Trying Union Bank trimmed password (removed whitespace)")
                                result = pdf_reader.decrypt(trimmed_password)
                                if result != 0:
                                    logger.info(f"Union Bank PDF decrypted successfully with trimmed password")
                                else:
                                    raise ValueError(f"Failed to decrypt Union Bank PDF with provided password (length: {len(password)}). Note: PDF passwords are case-sensitive.")
                            else:
                                raise ValueError(f"Failed to decrypt Union Bank PDF with provided password (length: {len(password)}). Note: PDF passwords are case-sensitive.")
                        else:
                            logger.info("Union Bank PDF decrypted successfully with original password")
                    else:
                        raise ValueError("Union Bank PDF is encrypted but no password provided")

                logger.info(f"Processing Union Bank statement with {len(pdf_reader.pages)} pages")

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
            logger.error(f"Error extracting Union Bank statement: {e}")
            raise

    def _extract_statement_metadata(self, first_page_text: str) -> Dict:
        """Extract account and statement metadata from first page"""
        metadata = {
            "bank_name": self.bank_name,
            "currency": "INR"
        }

        lines = first_page_text.split('\n')

        # Extract customer information
        for i, line in enumerate(lines):
            line = line.strip()

            # Customer Name (appears after "Name" keyword)
            if line.startswith('Name') and len(line.split()) > 1:
                # Format: "Name KONALA SURREDDY Customer/CIF ID 32582219"
                name_match = re.search(r'Name\s+([A-Z\s]+)\s+Customer/CIF', line)
                if name_match:
                    metadata["customer_name"] = name_match.group(1).strip()

                # Extract CIF ID
                cif_match = re.search(r'Customer/CIF ID\s+(\d+)', line)
                if cif_match:
                    metadata["customer_cif_id"] = cif_match.group(1)

            # Account Number
            if 'Account Number' in line:
                acc_match = re.search(r'Account Number\s+(\d+)', line)
                if acc_match:
                    metadata["account_number"] = acc_match.group(1)

            # Account Type
            if 'Account Type' in line:
                acc_type_match = re.search(r'Account Type\s+([A-Za-z\s]+)', line)
                if acc_type_match:
                    metadata["account_type"] = acc_type_match.group(1).strip()

            # IFSC Code
            if 'IFSC' in line:
                ifsc_match = re.search(r'IFSC\s+([A-Z0-9]+)', line)
                if ifsc_match:
                    metadata["ifsc_code"] = ifsc_match.group(1)

            # Statement Date
            if 'Statement Date' in line:
                date_match = re.search(r'Statement Date\s+(\d{2}/\d{2}/\d{4})', line)
                if date_match:
                    metadata["statement_date"] = date_match.group(1)

            # Statement Period
            if 'Statement Period' in line:
                # Look for pattern like "01/04/2024 To 31/03" or full pattern with year
                full_period_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+To\s+(\d{2}/\d{2}/\d{4})', line)
                partial_period_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+To\s+(\d{2}/\d{2})', line)

                if full_period_match:
                    # Full dates with years
                    from_date = full_period_match.group(1)
                    to_date = full_period_match.group(2)
                elif partial_period_match:
                    from_date = partial_period_match.group(1)
                    to_partial = partial_period_match.group(2)

                    # Look for the year - first check current line, then subsequent lines
                    to_year = None

                    # Check current line first for /YYYY pattern AFTER the partial to_date
                    # Look for year pattern that comes after the "To 31/03" part
                    to_section = line[line.find(to_partial):]
                    year_match = re.search(r'/(\d{4})', to_section)
                    if year_match:
                        to_year = int(year_match.group(1))
                    else:
                        # Look in the next few lines
                        from_year = int(from_date.split('/')[-1])
                        for j in range(i + 1, min(i + 4, len(lines))):
                            next_line = lines[j].strip()
                            # Look for /YYYY pattern or standalone YYYY that's different from from_year
                            year_matches = re.findall(r'(?:/)?(\d{4})', next_line)
                            for year_str in year_matches:
                                candidate_year = int(year_str)
                                # Accept if it's different from from_year (likely the to_year)
                                if candidate_year != from_year:
                                    to_year = candidate_year
                                    break
                            if to_year:
                                break

                    # Only set statement_period if we found both dates with years
                    if to_year is not None:
                        to_date = f"{to_partial}/{to_year}"
                        metadata["statement_period"] = {
                            "from_date": from_date,
                            "to_date": to_date
                        }
                    else:
                        logger.error(f"Could not find complete year for statement period. Found: '{from_date} To {to_partial}' but missing year.")
                        # Don't set statement_period if we can't find the complete date
                else:
                    # For full period match, set it normally
                    metadata["statement_period"] = {
                        "from_date": from_date,
                        "to_date": to_date
                    }

            # Mobile Number
            if 'Mobile No' in line:
                mobile_match = re.search(r'Mobile No\s+(\d+)', line)
                if mobile_match:
                    metadata["mobile_number"] = mobile_match.group(1)

            # Home Branch
            if 'Home branch' in line:
                branch_match = re.search(r'Home branch\s+([A-Z\s]+)', line)
                if branch_match:
                    metadata["home_branch"] = branch_match.group(1).strip()

            # Extract address information (multiple lines)
            if 'Address' in line:
                # Address can span multiple lines
                address_parts = []
                j = i
                while j < len(lines) and j < i + 5:  # Look at next few lines
                    addr_line = lines[j].strip()
                    if addr_line and not any(keyword in addr_line for keyword in
                                           ['Account Type', 'Account Number', 'Currency', 'City']):
                        if 'Address' in addr_line:
                            addr_line = addr_line.replace('Address', '').strip()
                        if addr_line:
                            address_parts.append(addr_line)
                    j += 1

                if address_parts:
                    metadata["address"] = ", ".join(address_parts[:3])  # Take first 3 parts

        return metadata

    def _extract_all_transactions(self, pdf_reader) -> List[Dict]:
        """Extract transactions from all pages"""
        all_transactions = []

        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            if not page_text:
                continue

            page_transactions = self._extract_transactions_from_page(page_text, page_num + 1)
            all_transactions.extend(page_transactions)

        return all_transactions

    def _extract_transactions_from_page(self, page_text: str, page_num: int) -> List[Dict]:
        """Extract transactions from a single page"""
        transactions = []
        lines = page_text.split('\n')

        for i, line in enumerate(lines):
            line = line.strip()

            # Look for transaction pattern: "S.No Date Transaction Id Remarks Amount(Rs.) Balance(Rs.)"
            # Skip header line
            if 'S.No' in line and 'Date' in line and 'Transaction Id' in line:
                continue

            # Match transaction pattern: starts with number
            line_pattern = r'^(\d+)\s+(\d{1,2}/\d{1,2}/\d{4})\s+([A-Z0-9]+)'
            line_match = re.match(line_pattern, line)

            if line_match:
                try:
                    # Combine lines if transaction spans multiple lines
                    combined_line = self._combine_transaction_lines(lines, i)

                    transaction = self._parse_transaction_line(combined_line, page_num)
                    if transaction:
                        transactions.append(transaction)

                except Exception as e:
                    logger.warning(f"Error parsing transaction on page {page_num}: {line[:50]}... - {e}")

        return transactions

    def _combine_transaction_lines(self, lines: List[str], start_index: int) -> str:
        """Combine transaction lines that span multiple rows"""
        combined_line = lines[start_index].strip()

        # Pattern to match amount format: number (Dr) or (Cr)
        amount_pattern = r'(\d+\.?\d*)\s*\((Dr|Cr)\)'

        # Keep combining lines until we have both amount and balance
        j = start_index + 1
        while j < len(lines) and len(re.findall(amount_pattern, combined_line)) < 2:
            next_line = lines[j].strip()
            # Stop if we hit the next transaction (starts with number) or empty line
            if next_line and not re.match(r'^\d+\s+\d{1,2}/\d{1,2}/\d{4}', next_line):
                combined_line += " " + next_line
                j += 1
            else:
                break

        return combined_line

    def _parse_transaction_line(self, line: str, page_num: int) -> Optional[Dict]:
        """Parse individual transaction line"""
        try:
            # Extract basic components
            line_pattern = r'^(\d+)\s+(\d{1,2}/\d{1,2}/\d{4})\s+([A-Z0-9]+)'
            line_match = re.match(line_pattern, line)

            if not line_match:
                return None

            s_no = line_match.group(1)
            date = line_match.group(2)
            transaction_id = line_match.group(3)

            # Find amounts with (Dr) or (Cr)
            amount_pattern = r'(\d+\.?\d*)\s*\((Dr|Cr)\)'
            amount_matches = re.findall(amount_pattern, line)

            if len(amount_matches) < 2:
                return None

            # First match is transaction amount, last match is balance
            amount_value, amount_type = amount_matches[0]
            balance_value, balance_type = amount_matches[-1]

            # Extract remarks (between transaction_id and first amount)
            remarks_start = line.find(transaction_id) + len(transaction_id)
            remarks_end = line.find(f"{amount_value} ({amount_type})")
            remarks = line[remarks_start:remarks_end].strip()

            # Convert to numeric values for calculations
            amount_numeric = float(amount_value)
            if amount_type == 'Dr':
                amount_numeric = -amount_numeric

            balance_numeric = float(balance_value)
            # Union Bank typically shows positive balances, but handle both cases
            if balance_type == 'Dr':
                balance_numeric = -balance_numeric

            transaction = {
                'S.No': s_no,
                'Date': date,
                'Transaction_ID': transaction_id,
                'Remarks': remarks,
                'Amount': f"{amount_value} ({amount_type})",
                'Balance': f"{balance_value} ({balance_type})",
                'Amount_Numeric': amount_numeric,
                'Balance_Numeric': balance_numeric,
                'Transaction_Type': 'Credit' if amount_type == 'Cr' else 'Debit',
                'Page_Number': page_num
            }

            return transaction

        except Exception as e:
            logger.error(f"Error parsing transaction line: {line[:50]}... - {e}")
            return None

    def _calculate_financial_summary(self) -> Dict:
        """Calculate financial summary from transactions"""
        if not self.transactions:
            return {}

        # Get opening and closing balances
        opening_balance = self.transactions[-1]['Balance_Numeric']  # Last transaction chronologically
        closing_balance = self.transactions[0]['Balance_Numeric']   # First transaction (most recent)

        # Calculate totals
        total_debits = sum(t['Amount_Numeric'] for t in self.transactions if t['Amount_Numeric'] < 0)
        total_credits = sum(t['Amount_Numeric'] for t in self.transactions if t['Amount_Numeric'] > 0)
        net_change = total_credits + total_debits  # debits are already negative

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


def extract_union_bank_statement(pdf_path: str, password: Optional[str] = None) -> Dict:
    """
    Main function to extract Union Bank statement data

    Args:
        pdf_path (str): Path to Union Bank PDF statement
        password (str): Password if PDF is encrypted

    Returns:
        Dict: Complete statement data including metadata, summary, and transactions
    """
    extractor = UnionBankExtractor()
    return extractor.extract_complete_statement(pdf_path, password)


