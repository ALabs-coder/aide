#!/usr/bin/env python3
"""
Base Extractor Interface for Bank Statement PDF Extraction
Ensures all bank extractors follow a standardized contract for consistency
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import logging


class BaseBankExtractor(ABC):
    """
    Abstract base class for all bank statement extractors

    This interface ensures consistency across all bank extractors and provides
    a standardized contract for the dynamic loading system.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.bank_name = self.get_bank_name()
        self.version = self.get_version()
        self.logger.info(f"Initialized {self.__class__.__name__} v{self.version} for {self.bank_name}")

    @abstractmethod
    def get_bank_name(self) -> str:
        """
        Return the bank name this extractor handles

        Returns:
            str: Bank name (e.g., "Union Bank of India", "Canara Bank")
        """
        pass

    @abstractmethod
    def get_version(self) -> str:
        """
        Return the version of this extractor

        Returns:
            str: Version string (e.g., "1.0.0")
        """
        pass

    @abstractmethod
    def get_supported_capabilities(self) -> List[str]:
        """
        Return list of capabilities supported by this extractor

        Returns:
            List[str]: List of capabilities (e.g., ["password_protected", "multi_page", "transactions"])
        """
        pass

    @abstractmethod
    def extract_complete_statement(self, pdf_path: str, password: Optional[str] = None) -> Dict:
        """
        Main extraction method that must return standardized format

        Args:
            pdf_path (str): Path to the PDF file
            password (str, optional): Password for encrypted PDFs

        Returns:
            Dict: Standardized extraction result with required fields:
                - total_transactions (int)
                - processed_at (str)
                - statement_metadata (dict)
                - financial_summary (dict)
                - transactions (list)
        """
        pass

    def validate_pdf(self, pdf_path: str) -> bool:
        """
        Optional: Validate if PDF is compatible with this extractor

        Args:
            pdf_path (str): Path to the PDF file

        Returns:
            bool: True if PDF is compatible, False otherwise
        """
        return True

    def get_extraction_metadata(self) -> Dict:
        """
        Return metadata about this extractor instance

        Returns:
            Dict: Extractor metadata including name, version, capabilities
        """
        return {
            "bank_name": self.bank_name,
            "version": self.version,
            "capabilities": self.get_supported_capabilities(),
            "extractor_class": self.__class__.__name__
        }

    def supports_capability(self, capability: str) -> bool:
        """
        Check if this extractor supports a specific capability

        Args:
            capability (str): Capability to check

        Returns:
            bool: True if capability is supported
        """
        return capability in self.get_supported_capabilities()

    def get_max_file_size_mb(self) -> int:
        """
        Return maximum supported file size in MB
        Override in subclasses if different from default

        Returns:
            int: Maximum file size in MB (default: 50)
        """
        return 50

    def __str__(self) -> str:
        """String representation of the extractor"""
        return f"{self.__class__.__name__} v{self.version} ({self.bank_name})"

    def __repr__(self) -> str:
        """Detailed string representation"""
        return f"{self.__class__.__name__}(bank='{self.bank_name}', version='{self.version}', capabilities={self.get_supported_capabilities()})"


class SecurityError(Exception):
    """Custom exception for security-related errors in dynamic loading"""
    pass


# Standard response format constants for consistency
STANDARD_RESPONSE_SCHEMA = {
    "total_transactions": int,
    "processed_at": str,
    "statement_metadata": {
        "bank_name": str,
        "customer_name": str,
        "account_number": str,
        "account_type": str,
        "statement_period": dict,
        "currency": str
    },
    "financial_summary": {
        "opening_balance": float,
        "closing_balance": float,
        "total_credits": float,
        "total_debits": float,
        "net_change": float,
        "transaction_count": int
    },
    "transactions": list,
    "extractor_metadata": dict
}

# Standard capabilities that extractors can support
STANDARD_CAPABILITIES = [
    "password_protected",    # Supports encrypted PDFs
    "multi_page",           # Handles multi-page statements
    "transactions",         # Extracts transaction details
    "financial_summary",    # Calculates financial summaries
    "account_metadata",     # Extracts account information
    "statement_period",     # Identifies statement date range
    "balance_calculation",  # Calculates running balances
    "transaction_types"     # Identifies debit/credit types
]