#!/usr/bin/env python3
"""
PDF Bank Statement Extraction API - Enterprise Lambda Version
FastAPI server for extracting transaction data from bank statement PDFs
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import pandas as pd
import pdfplumber
import re
import io
import time
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

# Import our security and configuration modules
from config import settings
from auth import get_current_user, check_rate_limit, User, security_logger
from validators import validate_uploaded_file
from logging_config import (
    setup_logging, 
    set_request_context, 
    generate_request_id, 
    log_api_request, 
    log_api_response,
    log_performance,
    LoggerMixin
)
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app with enhanced metadata
app = FastAPI(
    title="PDF Bank Statement Extractor API",
    description="Enterprise-grade API for extracting transaction data from bank statement PDFs",
    version="2.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

# Enhanced CORS middleware with environment-based configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

# Request/Response middleware for logging and monitoring
@app.middleware("http")
async def add_request_logging(request: Request, call_next):
    """Add request logging and monitoring"""
    start_time = time.time()
    request_id = generate_request_id()
    
    # Set request context for logging
    set_request_context(request_id)
    
    # Log incoming request
    log_api_request(
        method=request.method,
        path=request.url.path,
        user_agent=request.headers.get("user-agent"),
        content_length=request.headers.get("content-length")
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    
    # Log response
    log_api_response(
        status_code=response.status_code,
        processing_time=processing_time
    )
    
    return response

# Response models
class Transaction(BaseModel):
    s_no: str
    date: str
    transaction_id: str
    remarks: str
    amount: str
    balance: str
    amount_numeric: float
    balance_numeric: float
    transaction_type: str

class ExtractionResponse(BaseModel):
    success: bool
    message: str
    total_transactions: int
    transactions: List[Transaction]

class ErrorResponse(BaseModel):
    success: bool
    error: str
    message: str

def extract_bank_statement_data(pdf_file_content: bytes, password: Optional[str] = None) -> pd.DataFrame:
    """
    Extract transaction data from Union Bank PDF statement
    
    Args:
        pdf_file_content (bytes): PDF file content as bytes
        password (str, optional): Password to unlock PDF if protected
    
    Returns:
        pd.DataFrame: DataFrame containing transaction data
    """
    transactions = []
    
    with pdfplumber.open(io.BytesIO(pdf_file_content), password=password) as pdf:
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
                    parts = line.split()
                    
                    if len(parts) >= 6 and parts[0].isdigit():
                        try:
                            s_no = parts[0]
                            date = parts[1]
                            transaction_id = parts[2]
                            
                            # Find amount and balance patterns
                            amount_pattern = r'(\d+\.?\d*)\s*\((Dr|Cr)\)'
                            balance_pattern = r'(\d+\.?\d*)\s*\((Dr|Cr)\)'
                            
                            amount_match = re.search(amount_pattern, line)
                            balance_matches = re.findall(balance_pattern, line)
                            balance_match = balance_matches[-1] if balance_matches else None
                            
                            if amount_match and balance_match:
                                amount_value = amount_match.group(1)
                                amount_type = amount_match.group(2)
                                balance_value = balance_match[0]
                                balance_type = balance_match[1]
                                
                                # Extract remarks
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

def clean_transaction_data(df: pd.DataFrame) -> pd.DataFrame:
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
        
        amount_str = str(amount_str).replace('(', '-').replace(')', '').replace(',', '')
        
        if 'Dr' in amount_str:
            amount_str = amount_str.replace('Dr', '').strip()
            multiplier = -1
        elif 'Cr' in amount_str:
            amount_str = amount_str.replace('Cr', '').strip()
            multiplier = 1
        else:
            multiplier = 1
        
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

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "PDF Bank Statement Extraction API",
        "version": "2.0.0",
        "status": "healthy",
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check for monitoring"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {
            "pdfplumber": "available",
            "pandas": "available"
        }
    }

@app.post("/extract", response_model=ExtractionResponse)
@log_performance
async def extract_pdf(
    file: UploadFile = File(..., description="PDF file to extract data from"),
    password: Optional[str] = Form(None, description="Password for protected PDFs"),
    current_user: User = Depends(check_rate_limit)
):
    """
    Extract transaction data from uploaded PDF bank statement
    
    Args:
        file: PDF file upload
        password: Optional password for protected PDFs
        current_user: Authenticated user
    
    Returns:
        JSON response with extracted transaction data
    """
    logger.info(f"PDF extraction request from user: {current_user.user_id}")
    
    try:
        # Comprehensive file validation
        pdf_content, file_hash = await validate_uploaded_file(file)
        
        logger.info(f"File validation successful", extra={
            "user_id": current_user.user_id,
            "filename": file.filename,
            "file_hash": file_hash[:16],
            "file_size": len(pdf_content)
        })
        
        # Extract data with error handling
        df = extract_bank_statement_data(pdf_content, password)
        
        if df.empty:
            security_logger.log_suspicious_activity(
                "Empty extraction result",
                user_id=current_user.user_id,
                filename=file.filename,
                file_hash=file_hash
            )
            raise HTTPException(status_code=422, detail="No transaction data found in PDF")
        
        # Clean data
        df_clean = clean_transaction_data(df)
        
        # Convert to response format
        transactions = []
        for _, row in df_clean.iterrows():
            transactions.append(Transaction(
                s_no=str(row['S.No']),
                date=row['Date'].strftime('%Y-%m-%d') if pd.notna(row['Date']) else '',
                transaction_id=str(row['Transaction_ID']),
                remarks=str(row['Remarks']),
                amount=str(row['Amount']),
                balance=str(row['Balance']),
                amount_numeric=float(row['Amount_Numeric']),
                balance_numeric=float(row['Balance_Numeric']),
                transaction_type=str(row['Transaction_Type'])
            ))
        
        logger.info(f"Successfully extracted {len(transactions)} transactions", extra={
            "user_id": current_user.user_id,
            "transaction_count": len(transactions),
            "file_hash": file_hash[:16]
        })
        
        return ExtractionResponse(
            success=True,
            message=f"Successfully extracted {len(transactions)} transactions",
            total_transactions=len(transactions),
            transactions=transactions
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (they're already handled)
        raise
    except Exception as e:
        logger.error(f"Error processing PDF", extra={
            "user_id": current_user.user_id,
            "filename": file.filename,
            "error": str(e)
        }, exc_info=True)
        
        if "Bad decrypt" in str(e) or "password" in str(e).lower():
            security_logger.log_auth_failure(
                reason="Invalid PDF password",
                method="pdf_password",
                user_id=current_user.user_id,
                filename=file.filename
            )
            raise HTTPException(status_code=401, detail="Invalid password or PDF is password protected")
        else:
            raise HTTPException(status_code=500, detail="Error processing PDF")

@app.post("/extract/csv")
@log_performance
async def extract_pdf_to_csv(
    file: UploadFile = File(..., description="PDF file to extract data from"),
    password: Optional[str] = Form(None, description="Password for protected PDFs"),
    current_user: User = Depends(check_rate_limit)
):
    """
    Extract transaction data from PDF and return as CSV file
    
    Args:
        file: PDF file upload
        password: Optional password for protected PDFs
    
    Returns:
        CSV file download
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Read file content
        pdf_content = await file.read()
        
        # Extract data
        df = extract_bank_statement_data(pdf_content, password)
        
        if df.empty:
            raise HTTPException(status_code=422, detail="No transaction data found in PDF")
        
        # Clean data
        df_clean = clean_transaction_data(df)
        
        # Convert to CSV
        csv_buffer = io.StringIO()
        df_clean.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
        # Return CSV file
        from fastapi.responses import Response
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
        
    except Exception as e:
        if "Bad decrypt" in str(e) or "password" in str(e).lower():
            raise HTTPException(status_code=401, detail="Invalid password or PDF is password protected")
        else:
            raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)