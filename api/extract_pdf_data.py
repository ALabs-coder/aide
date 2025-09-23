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

logger = logging.getLogger(__name__)


def extract_bank_statement_data(pdf_path: str, password: Optional[str] = None, enhanced: bool = True) -> Union[Dict, List]:
    """
    Main function to extract bank statement data from PDF

    Args:
        pdf_path (str): Path to the PDF file
        password (str, optional): Password for encrypted PDFs
        enhanced (bool): If True, return enhanced format with metadata

    Returns:
        Union[Dict, List]: Enhanced format (Dict) or legacy format (List)
    """
    try:
        logger.info(f"Starting extraction for PDF: {pdf_path}")

        # For now, default to Union Bank extractor
        # TODO: Implement bank classification system to auto-detect bank type

        # Use Union Bank extractor
        result = extract_union_bank_statement(pdf_path, password)

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


def detect_bank_type(pdf_path: str, password: Optional[str] = None) -> str:
    """
    Detect the bank type from PDF content

    Args:
        pdf_path (str): Path to the PDF file
        password (str, optional): Password for encrypted PDFs

    Returns:
        str: Detected bank name
    """
    # TODO: Implement bank classification logic
    # For now, default to Union Bank
    logger.info("Bank detection not implemented yet, defaulting to Union Bank")
    return "Union Bank of India"


def get_supported_banks() -> List[str]:
    """
    Get list of supported banks

    Returns:
        List[str]: List of supported bank names
    """
    return [
        "Union Bank of India"
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
def extract_transactions_from_pdf(pdf_path: str, password: Optional[str] = None) -> List[Dict]:
    """
    Legacy function for backward compatibility

    Args:
        pdf_path (str): Path to the PDF file
        password (str, optional): Password for encrypted PDFs

    Returns:
        List[Dict]: List of transactions
    """
    logger.warning("Using deprecated function extract_transactions_from_pdf. Use extract_bank_statement_data instead.")
    return extract_bank_statement_data(pdf_path, password, enhanced=False)


if __name__ == "__main__":
    # Test the extraction function
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extract_pdf_data.py <pdf_path> [password]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        result = extract_bank_statement_data(pdf_path, password, enhanced=True)
        print(f"Extraction successful!")
        print(f"Bank: {result.get('statement_metadata', {}).get('bank_name', 'Unknown')}")
        print(f"Total transactions: {result.get('total_transactions', 0)}")
        print(f"Date range: {result.get('financial_summary', {}).get('date_range', 'Unknown')}")
    except Exception as e:
        print(f"Extraction failed: {e}")
        sys.exit(1)