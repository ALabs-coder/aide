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


def extract_bank_statement_data(pdf_path: str, password: Optional[str] = None, enhanced: bool = True) -> Union[Dict, List]:
    """
    Main function to extract bank statement data from PDF

    Args:
        pdf_path (str): Path to the PDF file
        password (str, optional): Password for encrypted PDFs
        enhanced (bool): If True, return enhanced format with metadata

    Returns:
        Union[Dict, List]: Enhanced format (Dict) or legacy format (List)

    Raises:
        ValueError: If the bank type is not recognized/supported
    """
    try:
        logger.info(f"Starting extraction for PDF: {pdf_path}")

        # Detect bank type from PDF content
        detected_bank = detect_bank_type(pdf_path, password)
        logger.info(f"Detected bank type: {detected_bank}")

        # Route to appropriate extractor based on detected bank
        if detected_bank == "Canara Bank":
            result = extract_canara_bank_statement(pdf_path, password)
        elif detected_bank == "Union Bank of India":
            result = extract_union_bank_statement(pdf_path, password)
        else:
            # Raise error for unrecognized bank types
            raise ValueError(f"Unrecognized bank statement format. Detected bank: {detected_bank}. Currently supported banks: {', '.join(get_supported_banks())}")

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
    try:
        import pypdf

        with open(pdf_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)

            # Handle encrypted PDFs
            if pdf_reader.is_encrypted:
                if password:
                    result = pdf_reader.decrypt(password)
                    if result == 0:
                        # Try trimmed password
                        trimmed_password = password.strip()
                        if trimmed_password != password:
                            result = pdf_reader.decrypt(trimmed_password)
                        if result == 0:
                            logger.warning("Failed to decrypt PDF for bank detection")
                            return "Union Bank of India"  # Default fallback
                else:
                    logger.warning("PDF is encrypted but no password provided for bank detection")
                    return "Union Bank of India"  # Default fallback

            # Extract text from first page for bank detection
            if len(pdf_reader.pages) > 0:
                first_page_text = pdf_reader.pages[0].extract_text().upper()

                # Check for Canara Bank indicators
                if any(indicator in first_page_text for indicator in [
                    "CANARA BANK",
                    "CNRB0",
                    "IFSC CODE CNRB"
                ]):
                    logger.info("Detected Canara Bank from PDF content")
                    return "Canara Bank"

                # Check for Union Bank indicators
                if any(indicator in first_page_text for indicator in [
                    "UNION BANK OF INDIA",
                    "UNION BANK",
                    "UBIN0"
                ]):
                    logger.info("Detected Union Bank of India from PDF content")
                    return "Union Bank of India"

        # Default fallback for unrecognized banks
        logger.info("Could not detect bank type from PDF content")
        return "Unknown"

    except Exception as e:
        logger.error(f"Error detecting bank type: {e}")
        return "Unknown"  # Default fallback


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