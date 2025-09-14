#!/usr/bin/env python3
"""
Simple local server that bypasses complex configuration for testing
"""

import sys
import os
import uvicorn
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import logging
import datetime
import uuid
import os
import boto3
from botocore.exceptions import ClientError

# Add current directory to path
sys.path.insert(0, os.getcwd())

# Simple logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# DynamoDB setup based on serverless.yml configuration
STAGE = os.getenv('STAGE', 'dev')
SERVICE = 'pdf-extractor-api'
JOBS_TABLE_NAME = f"{SERVICE}-{STAGE}-jobs"
S3_BUCKET_NAME = f"{SERVICE}-{STAGE}-storage"

def get_dynamodb_resource():
    """Get DynamoDB resource - local or AWS based on environment"""
    try:
        # For local development, try to use DynamoDB Local first
        if os.getenv('AWS_ENDPOINT_URL'):
            return boto3.resource(
                'dynamodb',
                endpoint_url=os.getenv('AWS_ENDPOINT_URL'),
                region_name='us-east-1',
                aws_access_key_id='dummy',
                aws_secret_access_key='dummy'
            )
        else:
            # Use AWS DynamoDB (requires proper AWS credentials)
            return boto3.resource('dynamodb', region_name='us-east-1')
    except Exception as e:
        logger.warning(f"Could not connect to DynamoDB: {e}")
        return None

def get_s3_client():
    """Get S3 client - local or AWS based on environment"""
    try:
        if os.getenv('AWS_ENDPOINT_URL'):
            return boto3.client(
                's3',
                endpoint_url=os.getenv('AWS_ENDPOINT_URL'),
                region_name='us-east-1',
                aws_access_key_id='dummy',
                aws_secret_access_key='dummy'
            )
        else:
            # Use AWS S3 (requires proper AWS credentials)
            return boto3.client('s3', region_name='us-east-1')
    except Exception as e:
        logger.warning(f"Could not connect to S3: {e}")
        return None

async def init_database():
    """Initialize DynamoDB table for file uploads"""
    try:
        dynamodb = get_dynamodb_resource()
        if not dynamodb:
            logger.warning("DynamoDB not available, uploads will work but metadata won't be stored")
            return

        # Check if table exists
        try:
            table = dynamodb.Table(JOBS_TABLE_NAME)
            table.meta.client.describe_table(TableName=JOBS_TABLE_NAME)
            logger.info(f"DynamoDB table '{JOBS_TABLE_NAME}' already exists")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Create table matching serverless.yml schema
                table = dynamodb.create_table(
                    TableName=JOBS_TABLE_NAME,
                    BillingMode='PAY_PER_REQUEST',
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'job_id',
                            'AttributeType': 'S'
                        },
                        {
                            'AttributeName': 'user_id',
                            'AttributeType': 'S'
                        },
                        {
                            'AttributeName': 'created_at',
                            'AttributeType': 'S'
                        }
                    ],
                    KeySchema=[
                        {
                            'AttributeName': 'job_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'user-id-created-at-index',
                            'KeySchema': [
                                {
                                    'AttributeName': 'user_id',
                                    'KeyType': 'HASH'
                                },
                                {
                                    'AttributeName': 'created_at',
                                    'KeyType': 'RANGE'
                                }
                            ],
                            'Projection': {
                                'ProjectionType': 'ALL'
                            }
                        }
                    ]
                )
                table.wait_until_exists()
                logger.info(f"Created DynamoDB table '{JOBS_TABLE_NAME}'")
            else:
                logger.error(f"Error checking table: {e}")
                raise
    except Exception as e:
        logger.warning(f"Could not initialize DynamoDB table: {e}")
        logger.info("Uploads will work but metadata won't be stored in DynamoDB")

async def create_database_entry(
    file_id: str,
    original_filename: str,
    s3_key: str,
    file_size_bytes: int,
    content_type: str,
    upload_timestamp: datetime.datetime,
    uploaded_by: str,
    local_path: str
):
    """Create a new file upload entry in DynamoDB JobsTable"""
    file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
    
    try:
        dynamodb = get_dynamodb_resource()
        if not dynamodb:
            logger.warning("DynamoDB not available, returning metadata without storing")
            return create_fallback_response(file_id, original_filename, s3_key, file_size_bytes, 
                                          content_type, upload_timestamp, uploaded_by, local_path)

        table = dynamodb.Table(JOBS_TABLE_NAME)
        
        # Create item matching serverless.yml JobsTable schema
        current_time = datetime.datetime.utcnow()
        ttl = int((current_time + datetime.timedelta(days=60)).timestamp())  # 60 days TTL
        
        item = {
            'job_id': file_id,  # Using file_id as job_id (primary key)
            'user_id': uploaded_by,
            'created_at': upload_timestamp.isoformat(),
            'status': 'uploaded',
            'job_type': 'file_upload',
            'original_filename': original_filename,
            's3_key': s3_key,
            'file_size_bytes': file_size_bytes,
            'file_size_mb': file_size_mb,
            'content_type': content_type,
            'upload_timestamp': upload_timestamp.isoformat(),
            'local_simulation_path': local_path,  # Only for local dev
            'ttl': ttl,
            'metadata': {
                'upload_source': 'local_dev_server',
                'api_version': '1.0.0-local'
            }
        }
        
        table.put_item(Item=item)
        logger.info(f"Created DynamoDB entry for job: {file_id}")
        
        return item
        
    except Exception as e:
        logger.error(f"Failed to create DynamoDB entry: {e}")
        return create_fallback_response(file_id, original_filename, s3_key, file_size_bytes, 
                                      content_type, upload_timestamp, uploaded_by, local_path, str(e))

def create_fallback_response(file_id, original_filename, s3_key, file_size_bytes, 
                           content_type, upload_timestamp, uploaded_by, local_path, error=None):
    """Create fallback response when DynamoDB is not available"""
    return {
        "job_id": file_id,
        "original_filename": original_filename,
        "s3_key": s3_key,
        "file_size_bytes": file_size_bytes,
        "file_size_mb": round(file_size_bytes / (1024 * 1024), 2),
        "content_type": content_type,
        "upload_timestamp": upload_timestamp.isoformat(),
        "uploaded_by": uploaded_by,
        "status": "uploaded",
        "local_simulation_path": local_path,
        "note": f"DynamoDB not available{': ' + error if error else ''}, but file upload succeeded"
    }

# Create FastAPI app
app = FastAPI(
    title="PDF Extractor API - Local Dev",
    description="Local development version of PDF bank statement extractor",
    version="1.0.0-local"
)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_database()

# Simple CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple API key validation
def validate_api_key(api_key: Optional[str] = None):
    """Simple API key validation for local testing"""
    valid_keys = ["test-key-123", "local-dev-key", "demo-key"]
    if not api_key or api_key not in valid_keys:
        raise HTTPException(
            status_code=401, 
            detail=f"Invalid API key. Use one of: {', '.join(valid_keys)}"
        )
    return {"user_id": f"user-{api_key}", "roles": ["user"]}

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "pdf-extractor-api",
        "environment": "local",
        "endpoints": {
            "sync_extract": "POST /extract",
            "s3_upload": "POST /upload",
            "health": "GET /",
            "docs": "GET /docs"
        },
        "auth": {
            "header": "X-API-KEY",
            "test_keys": ["test-key-123", "local-dev-key", "demo-key"]
        }
    }

@app.post("/extract")
async def extract_pdf(
    file: UploadFile = File(..., description="PDF file to process"),
    password: Optional[str] = Form(None, description="PDF password if protected"),
    api_key: Optional[str] = Form(None, alias="X-API-KEY")
):
    """
    Simple PDF extraction endpoint for local testing
    """
    try:
        # Validate API key
        user = validate_api_key(api_key)
        logger.info(f"Processing request from user: {user['user_id']}")
        
        # Basic file validation
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Read file content
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        if file_size_mb > 25:
            raise HTTPException(status_code=400, detail=f"File too large: {file_size_mb:.1f}MB (max 25MB)")
        
        logger.info(f"Processing PDF: {file.filename} ({file_size_mb:.1f}MB)")
        
        # Import and use the extraction logic
        try:
            from extract_pdf_to_csv import extract_bank_statement_data
            import tempfile
            import os
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            try:
                # Extract data
                transactions = extract_bank_statement_data(tmp_file_path, password)
                
                return {
                    "status": "success",
                    "filename": file.filename,
                    "file_size_mb": round(file_size_mb, 2),
                    "password_protected": bool(password),
                    "total_transactions": len(transactions),
                    "transactions": transactions[:10],  # Return first 10 for demo
                    "message": f"Successfully extracted {len(transactions)} transactions. Showing first 10 in demo mode."
                }
                
            finally:
                # Clean up temp file
                os.unlink(tmp_file_path)
                
        except ImportError as e:
            logger.error(f"Could not import extraction module: {e}")
            return {
                "status": "mock_success",
                "filename": file.filename,
                "file_size_mb": round(file_size_mb, 2),
                "message": "PDF received successfully. Extraction module not available in demo mode.",
                "mock_data": {
                    "total_transactions": 42,
                    "sample_transaction": {
                        "date": "2024-01-15",
                        "description": "Sample transaction",
                        "amount": "-50.00",
                        "balance": "1000.00"
                    }
                }
            }
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise HTTPException(status_code=500, detail=f"PDF extraction failed: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/upload")
async def upload_to_s3(
    file: UploadFile = File(..., description="PDF file to upload to S3"),
    api_key: Optional[str] = Form(None, alias="X-API-KEY")
):
    """
    Upload PDF file to S3 bucket and save metadata to database
    """
    try:
        # Validate API key
        user = validate_api_key(api_key)
        logger.info(f"Processing upload request from user: {user['user_id']}")
        
        # Basic file validation
        if not file.filename or not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Read file content
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        if file_size_mb > 25:
            raise HTTPException(status_code=400, detail=f"File too large: {file_size_mb:.1f}MB (max 25MB)")
        
        logger.info(f"Uploading PDF: {file.filename} ({file_size_mb:.1f}MB)")
        
        # Upload to S3 and save to DynamoDB
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        upload_timestamp = datetime.datetime.utcnow()
        
        # Create S3 key
        s3_key = f"uploads/{upload_timestamp.strftime('%Y/%m/%d')}/{file_id}_{file.filename}"
        
        # Try to upload to S3
        s3_client = get_s3_client()
        local_path = None
        
        if s3_client:
            try:
                # Upload to S3
                s3_client.put_object(
                    Bucket=S3_BUCKET_NAME,
                    Key=s3_key,
                    Body=content,
                    ContentType=file.content_type,
                    Metadata={
                        'original_filename': file.filename,
                        'uploaded_by': user['user_id'],
                        'upload_timestamp': upload_timestamp.isoformat()
                    }
                )
                logger.info(f"Uploaded to S3: s3://{S3_BUCKET_NAME}/{s3_key}")
                local_path = f"s3://{S3_BUCKET_NAME}/{s3_key}"
            except Exception as e:
                logger.warning(f"S3 upload failed: {e}, falling back to local storage")
                s3_client = None
        
        if not s3_client:
            # Fallback to local storage simulation
            upload_dir = "/tmp/nst-bucket-simulation"
            os.makedirs(upload_dir, exist_ok=True)
            local_path = os.path.join(upload_dir, f"{file_id}_{file.filename}")
            
            with open(local_path, "wb") as f:
                f.write(content)
            logger.info(f"Saved locally (S3 simulation): {local_path}")
        
        # Create database entry
        file_metadata = await create_database_entry(
            file_id=file_id,
            original_filename=file.filename,
            s3_key=s3_key,
            file_size_bytes=len(content),
            content_type=file.content_type,
            upload_timestamp=upload_timestamp,
            uploaded_by=user['user_id'],
            local_path=local_path
        )
        
        logger.info(f"File uploaded successfully: {file_metadata}")
        
        return {
            "status": "success",
            "message": f"File '{file.filename}' uploaded successfully to NST bucket",
            "job_id": file_id,
            "s3_key": s3_key,
            "file_metadata": file_metadata,
            "s3_bucket": S3_BUCKET_NAME,
            "dynamodb_table": JOBS_TABLE_NAME,
            "note": "File uploaded to S3 and metadata saved to DynamoDB. For local dev, may fall back to local storage and in-memory data."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Simple PDF Extractor API...")
    print("📍 API available at: http://localhost:8000")
    print("📚 Interactive docs: http://localhost:8000/docs")
    print("🔑 Test API keys: test-key-123, local-dev-key, demo-key")
    print("📝 Test command:")
    print("curl -X POST \"http://localhost:8000/extract\" \\")
    print("     -H \"accept: application/json\" \\")
    print("     -F \"file=@your-file.pdf\" \\")
    print("     -F \"X-API-KEY=test-key-123\"")
    print("-" * 60)
    
    uvicorn.run(
        "simple_local_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )