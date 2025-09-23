#!/usr/bin/env python3
"""
Shared transaction formatting utilities
Used by both statement_data and csv_export Lambda functions to ensure consistency
"""

import re
from typing import Dict, List, Any
from datetime import datetime


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

    # Remove (Dr), (Cr), Dr, Cr indicators and extra whitespace
    cleaned = re.sub(r'\s*\(?\s*(DR|dr|Dr|CR|cr|Cr)\s*\)?\s*', '', amount_str)

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
    Format a transaction for consistent display in both UI and CSV export

    Args:
        transaction: Raw transaction data from JSON

    Returns:
        Formatted transaction data
    """
    return {
        'serial_no': transaction.get('S.No', ''),
        'txn_date': convert_date_format(transaction.get('Date', ''), "DD/MM/YYYY", "DD-MM-YYYY"),
        'value_date': convert_date_format(transaction.get('Date', ''), "DD/MM/YYYY", "DD-MM-YYYY"),
        'description': transaction.get('Remarks', ''),
        'debit': clean_amount(transaction.get('Amount', '')) if transaction.get('Transaction_Type') == 'Debit' else '',
        'credit': clean_amount(transaction.get('Amount', '')) if transaction.get('Transaction_Type') == 'Credit' else '',
        'balance': clean_amount(transaction.get('Balance', '')),
        'raw_transaction': transaction  # Keep original for reference
    }


def format_transactions_for_csv(transactions: List[Dict[str, Any]]) -> List[List[str]]:
    """
    Format transactions specifically for CSV export

    Args:
        transactions: List of raw transaction data

    Returns:
        List of CSV rows (each row is a list of strings)
    """
    csv_rows = []

    # Add header row
    csv_rows.append([
        'Txn Date',
        'Value Date',
        'Description',
        'Debit',
        'Credit',
        'Balance'
    ])

    # Add data rows
    for transaction in transactions:
        formatted = format_transaction_for_display(transaction)
        csv_rows.append([
            formatted['txn_date'],
            formatted['value_date'],
            formatted['description'],
            formatted['debit'],
            formatted['credit'],
            formatted['balance']
        ])

    return csv_rows


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
        ui_transaction.update({
            'formatted_txn_date': formatted['txn_date'],
            'formatted_value_date': formatted['value_date'],
            'formatted_debit': formatted['debit'],
            'formatted_credit': formatted['credit'],
            'formatted_balance': formatted['balance'],
            # Add specific fields for frontend consumption
            'formatted_amount': clean_amount(transaction.get('Amount', '')),
            'debit_amount': clean_amount(transaction.get('Amount', '')) if transaction.get('Transaction_Type') == 'Debit' else '',
            'credit_amount': clean_amount(transaction.get('Amount', '')) if transaction.get('Transaction_Type') == 'Credit' else ''
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
    return {
        **transaction,  # Keep all original fields
        'formatted_amount': clean_amount(transaction.get('Amount', '')),
        'formatted_balance': clean_amount(transaction.get('Balance', '')),
        'formatted_date': convert_date_format(transaction.get('Date', ''), "DD/MM/YYYY", "DD-MM-YYYY"),
        'debit_amount': clean_amount(transaction.get('Amount', '')) if transaction.get('Transaction_Type') == 'Debit' else '',
        'credit_amount': clean_amount(transaction.get('Amount', '')) if transaction.get('Transaction_Type') == 'Credit' else ''
    }


def generate_csv_content(transactions: List[Dict[str, Any]]) -> str:
    """
    Generate complete CSV content as string

    Args:
        transactions: List of raw transaction data

    Returns:
        CSV content as string
    """
    csv_rows = format_transactions_for_csv(transactions)

    # Convert to CSV string
    csv_lines = []
    for row_index, row in enumerate(csv_rows):
        # Escape any fields that contain commas or quotes
        escaped_row = []
        for field_index, field in enumerate(row):
            field_str = str(field)

            # Always use Excel formula format for date fields (Txn Date and Value Date - columns 0 and 1)
            # Skip header row (row_index == 0)
            is_date_field = row_index > 0 and field_index in [0, 1]

            if is_date_field:
                # Use Excel formula format to force text interpretation: ="DD-MM-YYYY"
                field_str = '="' + field_str.replace('"', '""') + '"'
            elif ',' in field_str or '"' in field_str or '\n' in field_str:
                # Escape quotes and wrap in quotes for non-date fields that need it
                field_str = '"' + field_str.replace('"', '""') + '"'
            escaped_row.append(field_str)

        csv_lines.append(','.join(escaped_row))

    return '\n'.join(csv_lines)


def get_statement_filename(statement_metadata: Dict[str, Any], job_id: str) -> str:
    """
    Generate appropriate filename for CSV export

    Args:
        statement_metadata: Statement metadata from processing
        job_id: Job ID for fallback

    Returns:
        Filename for CSV download
    """
    try:
        bank_name = statement_metadata.get('bank_name', 'Bank')
        account_number = statement_metadata.get('account_number', '')
        statement_period = statement_metadata.get('statement_period', {})

        # Clean bank name for filename
        bank_clean = re.sub(r'[^\w\s-]', '', bank_name).strip()
        bank_clean = re.sub(r'\s+', '_', bank_clean)

        # Get date range
        from_date = statement_period.get('from_date', '')
        to_date = statement_period.get('to_date', '')

        if from_date and to_date:
            # Convert dates to YYYY-MM-DD format for filename
            try:
                from_formatted = datetime.strptime(from_date, "%d/%m/%Y").strftime("%Y-%m-%d")
                to_formatted = datetime.strptime(to_date, "%d/%m/%Y").strftime("%Y-%m-%d")
                date_range = f"{from_formatted}_to_{to_formatted}"
            except:
                date_range = f"{from_date.replace('/', '-')}_to_{to_date.replace('/', '-')}"
        else:
            date_range = datetime.now().strftime("%Y-%m-%d")

        # Build filename
        if account_number:
            acc_suffix = account_number[-4:] if len(account_number) >= 4 else account_number
            filename = f"{bank_clean}_Statement_AC_{acc_suffix}_{date_range}.csv"
        else:
            filename = f"{bank_clean}_Statement_{date_range}.csv"

        return filename

    except Exception:
        # Fallback to simple filename
        return f"bank_statement_{job_id}.csv"