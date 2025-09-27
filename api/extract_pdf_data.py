#!/usr/bin/env python3
"""
Main PDF Data Extraction Module
Routes to appropriate bank extractors and provides unified interface
"""

import logging
from typing import Dict, List, Optional, Union
from pathlib import Path

# Import bank-specific extractors
from extractors.union_bank_extractor import extract_union_bank_statement
from extractors.canara_bank_extractor import extract_canara_bank_statement

logger = logging.getLogger(__name__)


def extract_bank_statement_data(pdf_path: str, password: Optional[str] = None, enhanced: bool = True, bank_name: str = None) -> Union[Dict, List]:
    """
    Main function to extract bank statement data from PDF

    Args:
        pdf_path (str): Path to the PDF file
        password (str, optional): Password for encrypted PDFs
        enhanced (bool): If True, return enhanced format with metadata
        bank_name (str): Required bank name selected by user

    Returns:
        Union[Dict, List]: Enhanced format (Dict) or legacy format (List)

    Raises:
        ValueError: If the bank type is not recognized/supported
    """
    try:
        logger.info(f"Starting extraction for PDF: {pdf_path}")

        # Validate required bank_name parameter
        if not bank_name:
            raise ValueError(f"Bank name is required. Currently supported banks: {', '.join(get_supported_banks())}")

        logger.info(f"Using user-selected bank: {bank_name}")

        # Route to appropriate extractor based on selected bank
        if bank_name == "Canara Bank":
            result = extract_canara_bank_statement(pdf_path, password)
        elif bank_name == "Union Bank of India":
            result = extract_union_bank_statement(pdf_path, password)
        else:
            # Raise error for unrecognized bank types
            raise ValueError(f"Unrecognized bank statement format. Bank: {bank_name}. Currently supported banks: {', '.join(get_supported_banks())}")

        if enhanced:
            # Return the complete enhanced format
            logger.info(f"Enhanced extraction completed: {result.get('total_transactions', 0)} transactions")
            return result
        else:
            # Return legacy format (just the transactions list)
            transactions = result.get('transactions', [])
            logger.info(f"Legacy extraction completed: {len(transactions)} transactions")
            return transactions

    except Exception as e:
        logger.error(f"Error extracting bank statement data: {e}")
        raise




def get_supported_banks() -> List[str]:
    """
    Get list of supported banks

    Returns:
        List[str]: List of supported bank names
    """
    return [
        "Union Bank of India",
        "Canara Bank"
        # TODO: Add other banks as extractors are implemented
        # "HDFC Bank",
        # "State Bank of India",
        # "ICICI Bank",
        # "Axis Bank"
    ]


def validate_pdf_file(pdf_path: str) -> bool:
    """
    Validate if the file is a valid PDF

    Args:
        pdf_path (str): Path to the PDF file

    Returns:
        bool: True if valid PDF, False otherwise
    """
    try:
        path = Path(pdf_path)
        if not path.exists():
            logger.error(f"PDF file does not exist: {pdf_path}")
            return False

        if not path.suffix.lower() == '.pdf':
            logger.error(f"File is not a PDF: {pdf_path}")
            return False

        # Basic file size check
        if path.stat().st_size == 0:
            logger.error(f"PDF file is empty: {pdf_path}")
            return False

        return True

    except Exception as e:
        logger.error(f"Error validating PDF file: {e}")
        return False


# Legacy function for backward compatibility
def extract_transactions_from_pdf(pdf_path: str, password: Optional[str] = None, bank_name: str = None) -> List[Dict]:
    """
    Legacy function for backward compatibility

    Args:
        pdf_path (str): Path to the PDF file
        password (str, optional): Password for encrypted PDFs
        bank_name (str): Required bank name selected by user

    Returns:
        List[Dict]: List of transactions
    """
    logger.warning("Using deprecated function extract_transactions_from_pdf. Use extract_bank_statement_data instead.")
    return extract_bank_statement_data(pdf_path, password, enhanced=False, bank_name=bank_name)


if __name__ == "__main__":
    # Test the extraction function
    import sys

    if len(sys.argv) < 3:
        print("Usage: python extract_pdf_data.py <pdf_path> <bank_name> [password]")
        print(f"Supported banks: {', '.join(get_supported_banks())}")
        sys.exit(1)

    pdf_path = sys.argv[1]
    bank_name = sys.argv[2]
    password = sys.argv[3] if len(sys.argv) > 3 else None

    try:
        result = extract_bank_statement_data(pdf_path, password, enhanced=True, bank_name=bank_name)
        print(f"Extraction successful!")
        print(f"Bank: {result.get('statement_metadata', {}).get('bank_name', 'Unknown')}")
        print(f"Total transactions: {result.get('total_transactions', 0)}")
        print(f"Date range: {result.get('financial_summary', {}).get('date_range', 'Unknown')}")
    except Exception as e:
        print(f"Extraction failed: {e}")
        sys.exit(1)