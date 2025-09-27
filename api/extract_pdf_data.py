#!/usr/bin/env python3
"""
Bank Statement PDF Data Extractor - Phase 3 Dynamic Architecture
Main function to extract bank statement data from PDF with database-driven routing
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union
from pathlib import Path
from bank_config import bank_config_service

logger = logging.getLogger(__name__)


def extract_bank_statement_data(pdf_path: str, password: Optional[str] = None,
                               enhanced: bool = True, bank_id: str = None, bank_name: str = None) -> Union[Dict, List]:
    """
    Phase 3: Fully dynamic bank statement extraction with database-driven routing

    Args:
        pdf_path (str): Path to the PDF file
        password (str, optional): Password for encrypted PDFs
        enhanced (bool): If True, return enhanced format with metadata
        bank_id (str): Required bank ID from database (e.g., 'UNION', 'CANARA')
        bank_name (str): Legacy parameter - converted to bank_id if provided

    Returns:
        Union[Dict, List]: Enhanced format (Dict) or legacy format (List)

    Raises:
        ValueError: If the bank_id is not provided, not recognized, or inactive
    """
    try:
        # Handle legacy bank_name parameter for backward compatibility
        if bank_name and not bank_id:
            bank_id = _convert_bank_name_to_id(bank_name)
            logger.info(f"Converted legacy bank_name '{bank_name}' to bank_id '{bank_id}'")

        # Validate required bank_id parameter
        if not bank_id:
            supported_banks = bank_config_service.get_supported_bank_ids()
            raise ValueError(f"bank_id is required. Currently supported banks: {', '.join(supported_banks)}")

        # Validate PDF file exists and is readable
        if not validate_pdf_file(pdf_path):
            raise ValueError(f"Invalid PDF file: {pdf_path}")

        logger.info(f"Starting extraction for bank: {bank_id}, enhanced: {enhanced}")

        # Optional compatibility pre-check
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # MB
            if not bank_config_service.validate_bank_compatibility(
                bank_id, file_size, bool(password)
            ):
                logger.warning(f"Compatibility check failed for {bank_id} (file size: {file_size:.2f}MB, password: {bool(password)})")

        # Get dynamic extractor from database configuration
        extractor = bank_config_service.get_extractor(bank_id)
        logger.info(f"Using extractor: {extractor.__class__.__name__} v{extractor.version}")

        # Execute extraction with the dynamic extractor
        result = extractor.extract_complete_statement(pdf_path, password)

        # Add extractor metadata to result
        result['extractor_metadata'] = extractor.get_extraction_metadata()
        result['processed_at'] = datetime.now().isoformat()

        if enhanced:
            # Return the complete enhanced format
            logger.info(f"Extraction completed successfully for {bank_id}. Total transactions: {result.get('total_transactions', 0)}")
            return result
        else:
            # Return legacy format for backward compatibility
            transactions = result.get('transactions', [])
            logger.info(f"Extraction completed successfully for {bank_id}. Total transactions: {len(transactions)} (legacy format)")
            return transactions

    except Exception as e:
        logger.error(f"Error extracting {bank_id or bank_name} statement from {pdf_path}: {e}")
        raise


def _convert_bank_name_to_id(bank_name: str) -> str:
    """
    Convert legacy bank name to bank ID for backward compatibility

    Args:
        bank_name (str): Legacy bank display name

    Returns:
        str: Corresponding bank ID

    Raises:
        ValueError: If bank name is not recognized
    """
    name_to_id_mapping = {
        "Union Bank of India": "UNION",
        "Canara Bank": "CANARA",
        # Add more mappings as needed
    }

    bank_id = name_to_id_mapping.get(bank_name)
    if not bank_id:
        supported_names = list(name_to_id_mapping.keys())
        raise ValueError(f"Unrecognized bank name: {bank_name}. Supported names: {', '.join(supported_names)}")

    return bank_id


def get_supported_banks() -> List[Dict]:
    """
    Get list of all supported banks with their capabilities and metadata

    Returns:
        List[Dict]: List of supported bank configurations
    """
    return bank_config_service.list_available_banks()


def get_supported_bank_ids() -> List[str]:
    """
    Get list of supported bank IDs only

    Returns:
        List[str]: List of bank IDs (e.g., ['UNION', 'CANARA'])
    """
    return bank_config_service.get_supported_bank_ids()


def get_supported_bank_names() -> List[str]:
    """
    Get list of supported bank display names for legacy compatibility

    Returns:
        List[str]: List of bank display names
    """
    banks = get_supported_banks()
    return [bank['name'] for bank in banks]


def reload_bank_extractor(bank_id: str) -> bool:
    """
    Hot reload extractor - useful for updates without Lambda restart

    Args:
        bank_id (str): Bank ID to reload

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        bank_config_service.reload_extractor(bank_id)
        logger.info(f"Successfully reloaded extractor for bank {bank_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to reload extractor for {bank_id}: {e}")
        return False


def validate_pdf_file(pdf_path: str) -> bool:
    """
    Validate if file exists and is a valid PDF

    Args:
        pdf_path (str): Path to the PDF file

    Returns:
        bool: True if valid PDF file
    """
    try:
        path = Path(pdf_path)

        if not path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
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


def validate_bank_compatibility(bank_id: str, file_size_mb: float, requires_password: bool = False) -> bool:
    """
    Validate if bank extractor can handle the requirements

    Args:
        bank_id (str): Bank identifier
        file_size_mb (float): File size in megabytes
        requires_password (bool): Whether PDF requires password

    Returns:
        bool: True if bank can handle the requirements
    """
    return bank_config_service.validate_bank_compatibility(bank_id, file_size_mb, requires_password)


def get_bank_info(bank_id: str) -> Dict:
    """
    Get detailed information about a specific bank

    Args:
        bank_id (str): Bank identifier

    Returns:
        Dict: Bank configuration and capabilities
    """
    try:
        config = bank_config_service.get_bank_config(bank_id)
        extractor = bank_config_service.get_extractor(bank_id)

        return {
            'id': bank_id,
            'name': config.get('BankName'),
            'version': config.get('Version'),
            'capabilities': list(config.get('Capabilities', [])),
            'max_file_size': int(config.get('MaxFileSize', 50)),
            'extractor_class': config.get('ExtractorClass'),
            'extractor_metadata': extractor.get_extraction_metadata()
        }
    except Exception as e:
        logger.error(f"Error getting bank info for {bank_id}: {e}")
        return {}


def get_cache_stats() -> Dict:
    """
    Get cache statistics for monitoring and debugging

    Returns:
        Dict: Cache statistics
    """
    return bank_config_service.get_cache_stats()


# Legacy function for backward compatibility
def extract_transactions_from_pdf(pdf_path: str, password: Optional[str] = None,
                                bank_id: str = None, bank_name: str = None) -> List[Dict]:
    """
    Legacy function for backward compatibility

    Args:
        pdf_path (str): Path to the PDF file
        password (str, optional): Password for encrypted PDFs
        bank_id (str): Bank ID (preferred)
        bank_name (str): Legacy bank name parameter

    Returns:
        List[Dict]: List of transactions
    """
    logger.warning("Using deprecated function extract_transactions_from_pdf. Use extract_bank_statement_data instead.")
    return extract_bank_statement_data(pdf_path, password, enhanced=False, bank_id=bank_id, bank_name=bank_name)


if __name__ == "__main__":
    # Test the extraction function
    import sys

    if len(sys.argv) < 3:
        print("Usage: python extract_pdf_data.py <pdf_path> <bank_id> [password]")
        print(f"Supported bank IDs: {', '.join(get_supported_bank_ids())}")
        print(f"Supported bank names: {', '.join(get_supported_bank_names())}")
        sys.exit(1)

    pdf_path = sys.argv[1]
    bank_identifier = sys.argv[2].upper()
    password = sys.argv[3] if len(sys.argv) > 3 else None

    try:
        # Try as bank_id first, then as bank_name for flexibility
        if bank_identifier in get_supported_bank_ids():
            result = extract_bank_statement_data(pdf_path, password, enhanced=True, bank_id=bank_identifier)
        else:
            # Try as bank name
            result = extract_bank_statement_data(pdf_path, password, enhanced=True, bank_name=bank_identifier)

        print(f"Extraction successful!")
        print(f"Bank: {result.get('statement_metadata', {}).get('bank_name', 'Unknown')}")
        print(f"Total transactions: {result.get('total_transactions', 0)}")
        print(f"Extractor: {result.get('extractor_metadata', {}).get('extractor_class', 'Unknown')}")

        # Show cache stats
        cache_stats = get_cache_stats()
        print(f"Cache stats: {cache_stats.get('memory_cache_size', 0)} configs, {cache_stats.get('extractor_cache_size', 0)} extractors cached")

    except Exception as e:
        print(f"Extraction failed: {e}")
        sys.exit(1)