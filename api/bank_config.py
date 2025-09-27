#!/usr/bin/env python3
"""
Dynamic Bank Configuration Service with Multi-Level Caching
Provides database-driven, high-performance bank extractor management
"""

import importlib
import sys
import time
import os
from typing import Dict, List, Optional, Type
from functools import lru_cache
import boto3
from boto3.dynamodb.conditions import Key
import logging
from extractors.base_extractor import BaseBankExtractor, SecurityError

logger = logging.getLogger(__name__)


class BankConfigService:
    """
    Singleton service for dynamic bank extractor management with multi-level caching

    Performance Features:
    - Level 1: In-memory instance cache (0.1ms access)
    - Level 2: Python LRU cache (1ms access)
    - Level 3: DynamoDB with smart queries (50-100ms)
    """

    _instance = None
    _cache = {}
    _cache_timestamp = None
    _extractor_cache = {}
    CACHE_TTL = 300  # 5 minutes - balance between freshness and performance

    def __new__(cls):
        """Singleton pattern to ensure one instance per Lambda container"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize service only once per container"""
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.dynamodb = boto3.resource('dynamodb')
        table_name = os.getenv('BANK_CONFIGURATIONS_TABLE')
        if not table_name:
            raise ValueError("BANK_CONFIGURATIONS_TABLE environment variable is required")

        self.table = self.dynamodb.Table(table_name)
        self._initialized = True
        logger.info(f"BankConfigService initialized with table: {table_name}")

    @lru_cache(maxsize=128)
    def get_bank_config(self, bank_id: str) -> Dict:
        """
        Get bank configuration with intelligent multi-level caching

        Args:
            bank_id (str): Bank identifier (e.g., 'UNION', 'CANARA')

        Returns:
            Dict: Bank configuration from DynamoDB

        Raises:
            ValueError: If bank is not supported or inactive
        """
        try:
            # Level 1: Memory cache check
            if self._is_cache_valid() and bank_id in self._cache:
                logger.debug(f"Cache HIT (L1 Memory): {bank_id}")
                return self._cache[bank_id]

            # Level 3: Fetch from DynamoDB
            logger.debug(f"Cache MISS: Fetching {bank_id} from DynamoDB")
            start_time = time.time()

            response = self.table.query(
                KeyConditionExpression=Key('PK').eq('BANK_CONFIG'),
                FilterExpression='BankCode = :bank_code AND #status = :status',
                ExpressionAttributeNames={'#status': 'Status'},
                ExpressionAttributeValues={
                    ':bank_code': bank_id,
                    ':status': 'ACTIVE'
                }
            )

            query_time = (time.time() - start_time) * 1000
            logger.debug(f"DynamoDB query for {bank_id} took {query_time:.2f}ms")

            items = response.get('Items', [])
            if not items:
                supported_banks = self.get_supported_bank_ids()
                raise ValueError(f"Bank {bank_id} is not supported or inactive. Supported banks: {', '.join(supported_banks)}")

            config = items[0]

            # Update Level 1 cache
            self._cache[bank_id] = config
            self._cache_timestamp = time.time()

            logger.info(f"Loaded bank config for {bank_id} in {query_time:.2f}ms")
            return config

        except Exception as e:
            logger.error(f"Error fetching bank config for {bank_id}: {e}")
            raise

    def get_extractor(self, bank_id: str) -> BaseBankExtractor:
        """
        Get extractor instance with dynamic loading and caching

        Args:
            bank_id (str): Bank identifier

        Returns:
            BaseBankExtractor: Loaded and validated extractor instance

        Raises:
            ValueError: If bank is not supported
            TypeError: If extractor doesn't implement interface correctly
            ImportError: If extractor module cannot be loaded
        """
        start_time = time.time()

        try:
            # Level 1: Extractor instance cache check
            if bank_id in self._extractor_cache:
                load_time = (time.time() - start_time) * 1000
                logger.debug(f"Extractor cache HIT: {bank_id} in {load_time:.2f}ms")
                return self._extractor_cache[bank_id]

            # Get bank configuration (uses its own caching)
            config = self.get_bank_config(bank_id)

            # Dynamic loading with validation
            extractor_class = self._load_extractor_class(config)
            extractor_instance = extractor_class()

            # Validate extractor implements interface correctly
            if not isinstance(extractor_instance, BaseBankExtractor):
                raise TypeError(f"Extractor {config['ExtractorClass']} must inherit from BaseBankExtractor")

            # Cache the instance for future use
            self._extractor_cache[bank_id] = extractor_instance

            load_time = (time.time() - start_time) * 1000
            logger.info(f"Loaded extractor {config['ExtractorClass']} for bank {bank_id} in {load_time:.2f}ms")

            return extractor_instance

        except Exception as e:
            logger.error(f"Error loading extractor for bank {bank_id}: {e}")
            raise

    def _load_extractor_class(self, config: Dict) -> Type[BaseBankExtractor]:
        """
        Dynamically load extractor class with security validation

        Args:
            config (Dict): Bank configuration from DynamoDB

        Returns:
            Type[BaseBankExtractor]: Loaded extractor class

        Raises:
            ValueError: If module/class configuration is missing
            SecurityError: If module path is not in allowed extractors package
            ImportError: If module cannot be imported
            AttributeError: If class is not found in module
            TypeError: If class doesn't inherit from BaseBankExtractor
        """
        module_name = config.get('ExtractorModule', '')
        class_name = config.get('ExtractorClass', '')

        if not module_name or not class_name:
            raise ValueError(f"Missing ExtractorModule or ExtractorClass in config for {config.get('BankCode', 'unknown')}")

        # Security: Validate module path to prevent arbitrary code execution
        if not module_name.startswith('extractors.'):
            raise SecurityError(f"Extractor module must be in extractors package: {module_name}")

        try:
            # Dynamic import with reload capability for hot updates
            if module_name in sys.modules:
                logger.debug(f"Reloading existing module: {module_name}")
                module = importlib.reload(sys.modules[module_name])
            else:
                logger.debug(f"Importing new module: {module_name}")
                module = importlib.import_module(module_name)

            # Get the extractor class from the module
            extractor_class = getattr(module, class_name)

            # Validate inheritance
            if not issubclass(extractor_class, BaseBankExtractor):
                raise TypeError(f"Class {class_name} must inherit from BaseBankExtractor")

            logger.debug(f"Successfully loaded {module_name}.{class_name}")
            return extractor_class

        except ImportError as e:
            logger.error(f"Failed to import {module_name}.{class_name}: {e}")
            raise ImportError(f"Could not import extractor module {module_name}: {e}")
        except AttributeError as e:
            logger.error(f"Class {class_name} not found in {module_name}: {e}")
            raise AttributeError(f"Class {class_name} not found in module {module_name}")

    def reload_extractor(self, bank_id: str) -> BaseBankExtractor:
        """
        Hot reload extractor - useful for development and updates without Lambda restart

        Args:
            bank_id (str): Bank identifier to reload

        Returns:
            BaseBankExtractor: Newly loaded extractor instance
        """
        logger.info(f"Hot reloading extractor for bank {bank_id}")

        # Clear all caches for this bank
        if bank_id in self._extractor_cache:
            del self._extractor_cache[bank_id]

        # Clear LRU cache
        self.get_bank_config.cache_clear()

        # Clear memory cache
        self._cache.clear()
        self._cache_timestamp = None

        # Force reload
        return self.get_extractor(bank_id)

    def get_supported_bank_ids(self) -> List[str]:
        """
        Get list of supported bank IDs (fast, cached query)

        Returns:
            List[str]: List of active bank IDs (e.g., ['UNION', 'CANARA'])
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key('PK').eq('BANK_CONFIG'),
                FilterExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'Status'},
                ExpressionAttributeValues={':status': 'ACTIVE'},
                ProjectionExpression='BankCode'
            )
            bank_ids = [item['BankCode'] for item in response.get('Items', [])]
            logger.debug(f"Found {len(bank_ids)} active banks: {bank_ids}")
            return bank_ids
        except Exception as e:
            logger.error(f"Error fetching supported bank IDs: {e}")
            # Fallback to known banks
            return ['UNION', 'CANARA']

    def list_available_banks(self) -> List[Dict]:
        """
        List all active banks with their capabilities and metadata

        Returns:
            List[Dict]: List of bank configurations for frontend display
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key('PK').eq('BANK_CONFIG'),
                FilterExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'Status'},
                ExpressionAttributeValues={':status': 'ACTIVE'}
            )

            banks = []
            for item in response.get('Items', []):
                # Convert DynamoDB types to standard Python types
                capabilities = item.get('Capabilities', [])
                if hasattr(capabilities, '__iter__') and not isinstance(capabilities, str):
                    capabilities = list(capabilities)

                banks.append({
                    'id': item.get('BankCode'),
                    'name': item.get('BankName'),
                    'capabilities': capabilities,
                    'version': item.get('Version', '1.0.0'),
                    'max_file_size': int(item.get('MaxFileSize', 50))
                })

            # Sort alphabetically by bank name for consistent UI
            banks_sorted = sorted(banks, key=lambda x: x['name'])
            logger.info(f"Listed {len(banks_sorted)} available banks")
            return banks_sorted

        except Exception as e:
            logger.error(f"Error listing banks: {e}")
            # Return minimal fallback data
            return [
                {'id': 'UNION', 'name': 'Union Bank of India', 'capabilities': [], 'version': '1.0.0', 'max_file_size': 50},
                {'id': 'CANARA', 'name': 'Canara Bank', 'capabilities': [], 'version': '1.0.0', 'max_file_size': 50}
            ]

    def validate_bank_compatibility(self, bank_id: str, file_size_mb: float,
                                  requires_password: bool = False) -> bool:
        """
        Validate if bank extractor can handle the requirements

        Args:
            bank_id (str): Bank identifier
            file_size_mb (float): File size in megabytes
            requires_password (bool): Whether PDF requires password

        Returns:
            bool: True if bank can handle the requirements
        """
        try:
            config = self.get_bank_config(bank_id)

            # Check file size limit
            max_size = int(config.get('MaxFileSize', 50))
            if file_size_mb > max_size:
                logger.warning(f"File size {file_size_mb:.2f}MB exceeds max {max_size}MB for {bank_id}")
                return False

            # Check password capability
            if requires_password:
                capabilities = config.get('Capabilities', [])
                # Handle DynamoDB set type
                if hasattr(capabilities, '__iter__') and not isinstance(capabilities, str):
                    capabilities = list(capabilities)

                if 'password_protected' not in capabilities:
                    logger.warning(f"Bank {bank_id} does not support password-protected PDFs")
                    return False

            logger.debug(f"Compatibility check passed for {bank_id} (size: {file_size_mb:.2f}MB, password: {requires_password})")
            return True

        except Exception as e:
            logger.error(f"Error validating compatibility for {bank_id}: {e}")
            return False

    def _is_cache_valid(self) -> bool:
        """
        Check if memory cache is still valid based on TTL

        Returns:
            bool: True if cache is valid and not expired
        """
        if not self._cache_timestamp:
            return False
        return time.time() - self._cache_timestamp < self.CACHE_TTL

    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics for monitoring and debugging

        Returns:
            Dict: Cache statistics
        """
        return {
            'memory_cache_size': len(self._cache),
            'extractor_cache_size': len(self._extractor_cache),
            'cache_timestamp': self._cache_timestamp,
            'cache_age_seconds': time.time() - self._cache_timestamp if self._cache_timestamp else None,
            'cache_valid': self._is_cache_valid(),
            'lru_cache_info': self.get_bank_config.cache_info()._asdict() if hasattr(self.get_bank_config, 'cache_info') else None
        }

    def clear_all_caches(self) -> None:
        """Clear all caches - useful for development and testing"""
        logger.info("Clearing all caches")
        self._cache.clear()
        self._extractor_cache.clear()
        self._cache_timestamp = None
        self.get_bank_config.cache_clear()


# Global singleton instance for use across the application
bank_config_service = BankConfigService()