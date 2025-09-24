#!/usr/bin/env python3
"""
Shared transaction formatting utilities
Used by statement_data Lambda function for UI display formatting
"""

import re
from typing import Dict, List, Any


def convert_date_format(date_str: str, from_format: str = "DD/MM/YYYY", to_format: str = "DD-MM-YYYY") -> str:
    """
    Convert date from one format to another with proper normalization

    Args:
        date_str: Date string to convert
        from_format: Source format (default: DD/MM/YYYY)
        to_format: Target format (default: DD-MM-YYYY)

    Returns:
        Converted date string with leading zeros
    """
    if not date_str:
        return ""

    try:
        # Handle DD/MM/YYYY to DD-MM-YYYY conversion
        if from_format == "DD/MM/YYYY" and to_format == "DD-MM-YYYY":
            # Split by "/" and normalize with leading zeros
            parts = date_str.split("/")
            if len(parts) == 3:
                day = parts[0].zfill(2)
                month = parts[1].zfill(2)
                year = parts[2]
                return f"{day}-{month}-{year}"
            else:
                # Fallback to simple replacement if parsing fails
                return date_str.replace("/", "-")

        # Handle DD-MM-YYYY to DD/MM/YYYY conversion
        if from_format == "DD-MM-YYYY" and to_format == "DD/MM/YYYY":
            # Split by "-" and normalize with leading zeros
            parts = date_str.split("-")
            if len(parts) == 3:
                day = parts[0].zfill(2)
                month = parts[1].zfill(2)
                year = parts[2]
                return f"{day}/{month}/{year}"
            else:
                # Fallback to simple replacement if parsing fails
                return date_str.replace("-", "/")

        return date_str
    except Exception:
        return date_str


def clean_amount(amount_str: str) -> str:
    """
    Clean amount string by removing Dr/Cr indicators and normalizing format

    Args:
        amount_str: Amount string like "5000.00 (Dr)" or "1500.00 (Cr)"

    Returns:
        Clean numeric amount string like "5000.00"
    """
    if not amount_str:
        return ""

    # Remove (Dr), (Cr), (De), Dr, Cr, De indicators and extra whitespace
    cleaned = re.sub(r'\s*\(?\s*(DR|dr|Dr|De|DE|de|CR|cr|Cr)\s*\)?\s*', '', amount_str)

    # Remove any leading/trailing whitespace
    cleaned = cleaned.strip()

    # Ensure it's a valid number format
    try:
        float(cleaned)
        return cleaned
    except ValueError:
        # If can't convert to float, return as is
        return cleaned


def format_transaction_for_display(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a transaction for consistent display in UI

    Args:
        transaction: Raw transaction data from JSON

    Returns:
        Formatted transaction data
    """
    # Handle both new format (separate Debit/Credit fields) and legacy format (Amount + Transaction_Type)
    if 'Debit' in transaction or 'Credit' in transaction:
        # New format with separate Debit/Credit fields
        debit_amount = clean_amount(transaction.get('Debit', '')) if transaction.get('Debit') else ''
        credit_amount = clean_amount(transaction.get('Credit', '')) if transaction.get('Credit') else ''
    else:
        # Legacy format with Amount + Transaction_Type
        debit_amount = clean_amount(transaction.get('Amount', '')) if transaction.get('Transaction_Type') == 'Debit' else ''
        credit_amount = clean_amount(transaction.get('Amount', '')) if transaction.get('Transaction_Type') == 'Credit' else ''

    return {
        'serial_no': transaction.get('S.No', ''),
        'txn_date': convert_date_format(transaction.get('Date', ''), "DD/MM/YYYY", "DD-MM-YYYY"),
        'value_date': convert_date_format(transaction.get('Date', ''), "DD/MM/YYYY", "DD-MM-YYYY"),
        'description': transaction.get('Remarks', ''),
        'debit': debit_amount,
        'credit': credit_amount,
        'balance': clean_amount(transaction.get('Balance', '')),
        'raw_transaction': transaction  # Keep original for reference
    }


def format_transactions_for_ui(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format transactions for UI display (keeps original structure but adds formatted fields)

    Args:
        transactions: List of raw transaction data

    Returns:
        List of transactions with additional formatted fields
    """
    formatted_transactions = []

    for transaction in transactions:
        formatted = format_transaction_for_display(transaction)

        # Keep original transaction data and add formatted fields
        ui_transaction = {**transaction}

        # Handle both new format (separate Debit/Credit fields) and legacy format (Amount + Transaction_Type)
        if 'Debit' in transaction or 'Credit' in transaction:
            # New format with separate Debit/Credit fields
            debit_amount = clean_amount(transaction.get('Debit', '')) if transaction.get('Debit') else ''
            credit_amount = clean_amount(transaction.get('Credit', '')) if transaction.get('Credit') else ''
            formatted_amount = debit_amount or credit_amount or ''
        else:
            # Legacy format with Amount + Transaction_Type
            debit_amount = clean_amount(transaction.get('Amount', '')) if transaction.get('Transaction_Type') == 'Debit' else ''
            credit_amount = clean_amount(transaction.get('Amount', '')) if transaction.get('Transaction_Type') == 'Credit' else ''
            formatted_amount = clean_amount(transaction.get('Amount', ''))

        ui_transaction.update({
            'formatted_txn_date': formatted['txn_date'],
            'formatted_value_date': formatted['value_date'],
            'formatted_debit': formatted['debit'],
            'formatted_credit': formatted['credit'],
            'formatted_balance': formatted['balance'],
            # Add specific fields for frontend consumption
            'formatted_amount': formatted_amount,
            'debit_amount': debit_amount,
            'credit_amount': credit_amount
        })

        formatted_transactions.append(ui_transaction)

    return formatted_transactions


def format_transaction_for_frontend(transaction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a single transaction specifically for frontend display with cleaned amounts

    Args:
        transaction: Raw transaction data from JSON

    Returns:
        Transaction with frontend-friendly formatted fields
    """
    # Handle both new format (separate Debit/Credit fields) and legacy format (Amount + Transaction_Type)
    if 'Debit' in transaction or 'Credit' in transaction:
        # New format with separate Debit/Credit fields
        debit_amount = clean_amount(transaction.get('Debit', '')) if transaction.get('Debit') else ''
        credit_amount = clean_amount(transaction.get('Credit', '')) if transaction.get('Credit') else ''
        formatted_amount = debit_amount or credit_amount or ''
    else:
        # Legacy format with Amount + Transaction_Type
        debit_amount = clean_amount(transaction.get('Amount', '')) if transaction.get('Transaction_Type') == 'Debit' else ''
        credit_amount = clean_amount(transaction.get('Amount', '')) if transaction.get('Transaction_Type') == 'Credit' else ''
        formatted_amount = clean_amount(transaction.get('Amount', ''))

    return {
        **transaction,  # Keep all original fields
        'formatted_amount': formatted_amount,
        'formatted_balance': clean_amount(transaction.get('Balance', '')),
        'formatted_date': convert_date_format(transaction.get('Date', ''), "DD/MM/YYYY", "DD-MM-YYYY"),
        'debit_amount': debit_amount,
        'credit_amount': credit_amount
    }
