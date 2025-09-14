#!/usr/bin/env python3
"""
PDF Bank Statement to CSV Extractor
Extracts transaction data from Union Bank PDF statements and saves to CSV
"""

import pdfplumber
import pandas as pd
import re
from datetime import datetime

def extract_bank_statement_data(pdf_path, password=None):
    """
    Extract transaction data from Union Bank PDF statement
    
    Args:
        pdf_path (str): Path to the PDF file
        password (str): Password to unlock PDF if protected
    
    Returns:
        pd.DataFrame: DataFrame containing transaction data
    """
    transactions = []
    
    with pdfplumber.open(pdf_path, password=password) as pdf:
        print(f"Processing {len(pdf.pages)} pages...")
        
        for page_num, page in enumerate(pdf.pages):
            print(f"Processing page {page_num + 1}...")
            
            # Extract text from the page
            text = page.extract_text()
            if not text:
                continue
                
            lines = text.split('\n')
            
            # Find the start of transaction data
            start_parsing = False
            
            for line in lines:
                line = line.strip()
                
                # Look for header row
                if 'S.No' in line and 'Date' in line and 'Transaction Id' in line:
                    start_parsing = True
                    print(f"Found transaction header on page {page_num + 1}")
                    continue
                
                if start_parsing and line:
                    # Try to parse transaction line
                    # Pattern: S.No Date TransactionId Remarks Amount Balance
                    parts = line.split()
                    
                    if len(parts) >= 6 and parts[0].isdigit():
                        try:
                            s_no = parts[0]
                            date = parts[1]
                            transaction_id = parts[2]
                            
                            # Find amount and balance (look for patterns like 90000.00 (Dr) or 61946.80 (Cr))
                            amount_pattern = r'(\d+\.?\d*)\s*\((Dr|Cr)\)'
                            balance_pattern = r'(\d+\.?\d*)\s*\((Dr|Cr)\)'
                            
                            amount_match = re.search(amount_pattern, line)
                            # Find balance (usually the last monetary amount)
                            balance_matches = re.findall(balance_pattern, line)
                            balance_match = balance_matches[-1] if balance_matches else None
                            
                            if amount_match and balance_match:
                                amount_value = amount_match.group(1)
                                amount_type = amount_match.group(2)
                                balance_value = balance_match[0]
                                balance_type = balance_match[1]
                                
                                # Extract remarks (everything between transaction_id and amount)
                                remarks_start = line.find(transaction_id) + len(transaction_id)
                                remarks_end = line.find(amount_value)
                                remarks = line[remarks_start:remarks_end].strip()
                                
                                transaction = {
                                    'S.No': s_no,
                                    'Date': date,
                                    'Transaction_ID': transaction_id,
                                    'Remarks': remarks,
                                    'Amount': f"{amount_value} ({amount_type})",
                                    'Balance': f"{balance_value} ({balance_type})"
                                }
                                
                                transactions.append(transaction)
                                print(f"Extracted transaction {s_no}: {date}")
                                
                        except Exception as e:
                            print(f"Error parsing line: {line[:50]}... - {e}")
                            continue
    
    return pd.DataFrame(transactions)

def clean_transaction_data(df):
    """
    Clean and format transaction data
    
    Args:
        df (pd.DataFrame): Raw transaction data
    
    Returns:
        pd.DataFrame: Cleaned transaction data
    """
    if df.empty:
        return df
    
    # Convert date format
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
    
    # Clean amount and balance columns
    def clean_amount(amount_str):
        if not amount_str:
            return 0.0
        
        # Remove currency symbols and extract numeric value
        amount_str = str(amount_str).replace('(', '-').replace(')', '').replace(',', '')
        
        # Extract debit/credit indicators
        if 'Dr' in amount_str:
            amount_str = amount_str.replace('Dr', '').strip()
            multiplier = -1
        elif 'Cr' in amount_str:
            amount_str = amount_str.replace('Cr', '').strip()
            multiplier = 1
        else:
            multiplier = 1
        
        # Extract numeric value
        try:
            amount = float(re.findall(r'[\d.]+', amount_str)[0]) * multiplier
        except (IndexError, ValueError):
            amount = 0.0
        
        return amount
    
    df['Amount_Numeric'] = df['Amount'].apply(clean_amount)
    df['Balance_Numeric'] = df['Balance'].apply(lambda x: clean_amount(str(x).replace('Cr', '').replace('Dr', '')) if x else 0.0)
    
    # Add transaction type
    df['Transaction_Type'] = df['Amount_Numeric'].apply(lambda x: 'Credit' if x > 0 else 'Debit' if x < 0 else 'Unknown')
    
    # Sort by date
    df = df.sort_values('Date').reset_index(drop=True)
    
    return df

def save_to_csv(df, output_path):
    """
    Save DataFrame to CSV file
    
    Args:
        df (pd.DataFrame): Transaction data
        output_path (str): Output CSV file path
    """
    df.to_csv(output_path, index=False)
    print(f"Data saved to {output_path}")
    print(f"Total transactions: {len(df)}")

def main():
    """Main function to process PDF and create CSV"""
    pdf_path = "/Users/ramanjaneyulumedikonda/dev/aide/public/Statement_XXXX XXXX 7499_2Sep2025_17_18.pdf"
    password = "KONA0101"
    output_path = "/Users/ramanjaneyulumedikonda/dev/aide/bank_statement_transactions.csv"
    
    print("Starting PDF extraction...")
    
    # Extract data
    df = extract_bank_statement_data(pdf_path, password)
    
    if df.empty:
        print("No transaction data found in PDF")
        return
    
    print(f"Extracted {len(df)} raw transactions")
    
    # Clean data
    df_clean = clean_transaction_data(df)
    
    # Save to CSV
    save_to_csv(df_clean, output_path)
    
    # Display sample data
    print("\nSample data:")
    print(df_clean.head().to_string())
    
    print(f"\nData extraction complete!")

if __name__ == "__main__":
    main()