#!/usr/bin/env python3
"""
AWS Lambda handler for processing SQS messages containing PDF extraction jobs
"""

import json
import boto3
import os
import sys
from typing import Dict, List
import logging

# Add parent directories to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from extract_pdf_to_csv import extract_bank_statement_data
from logging_config import setup_logging
from config import settings

# Setup logging for Lambda
setup_logging()
logger = logging.getLogger(__name__)

# AWS clients
s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

# Environment variables
JOBS_TABLE_NAME = os.getenv('JOBS_TABLE_NAME', 'pdf-extractor-jobs')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'pdf-extractor-storage')

def handler(event, context):
    """
    AWS Lambda entry point for SQS message processing
    
    Args:
        event: SQS event containing message records
        context: Lambda context object
        
    Returns:
        Processing results
    """
    try:
        logger.info("Processor Lambda invocation started", extra={
            "request_id": context.aws_request_id,
            "function_name": context.function_name,
            "records_count": len(event.get('Records', []))
        })
        
        results = []
        
        # Process each SQS message
        for record in event.get('Records', []):
            try:
                result = process_message(record, context)
                results.append(result)
            except Exception as e:
                logger.error("Failed to process SQS record", extra={
                    "request_id": context.aws_request_id,
                    "message_id": record.get('messageId'),
                    "error": str(e)
                }, exc_info=True)
                results.append({
                    "messageId": record.get('messageId'),
                    "status": "failed",
                    "error": str(e)
                })
        
        logger.info("Processor Lambda completed", extra={
            "request_id": context.aws_request_id,
            "processed": len(results),
            "successful": len([r for r in results if r.get("status") == "success"])
        })
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "processed": len(results),
                "results": results
            })
        }
        
    except Exception as e:
        logger.error("Processor Lambda failed", extra={
            "request_id": context.aws_request_id,
            "error": str(e)
        }, exc_info=True)
        
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Processing failed",
                "message": str(e)
            })
        }

def process_message(record: Dict, context) -> Dict:
    """
    Process individual SQS message containing PDF processing job
    
    Args:
        record: SQS message record
        context: Lambda context
        
    Returns:
        Processing result
    """
    message_id = record.get('messageId')
    
    try:
        # Parse SQS message body
        message_body = json.loads(record['body'])
        
        job_id = message_body.get('job_id')
        s3_key = message_body.get('s3_key')
        password = message_body.get('password')
        user_id = message_body.get('user_id')
        
        if not job_id or not s3_key:
            raise ValueError("Missing required job_id or s3_key in message")
        
        logger.info("Processing PDF job", extra={
            "job_id": job_id,
            "s3_key": s3_key,
            "user_id": user_id,
            "message_id": message_id
        })
        
        # Update job status to processing
        update_job_status(job_id, "processing", {"started_at": context.aws_request_id})
        
        # Download PDF from S3
        pdf_content = download_from_s3(s3_key)
        
        # Extract transactions
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(pdf_content)
            tmp_file_path = tmp_file.name
        
        try:
            transactions = extract_bank_statement_data(tmp_file_path, password)
            
            # Upload results back to S3
            results_key = f"results/{job_id}/transactions.json"
            upload_results_to_s3(results_key, transactions)
            
            # Update job status to completed
            update_job_status(job_id, "completed", {
                "completed_at": context.aws_request_id,
                "total_transactions": len(transactions),
                "results_s3_key": results_key
            })
            
            logger.info("Successfully processed PDF job", extra={
                "job_id": job_id,
                "transactions_found": len(transactions),
                "results_s3_key": results_key
            })
            
            return {
                "messageId": message_id,
                "job_id": job_id,
                "status": "success",
                "transactions_count": len(transactions),
                "results_s3_key": results_key
            }
            
        finally:
            # Clean up temp file
            os.unlink(tmp_file_path)
        
    except Exception as e:
        logger.error("Error processing message", extra={
            "message_id": message_id,
            "job_id": job_id if 'job_id' in locals() else None,
            "error": str(e)
        }, exc_info=True)
        
        # Update job status to failed
        if 'job_id' in locals():
            update_job_status(job_id, "failed", {
                "failed_at": context.aws_request_id,
                "error": str(e)
            })
        
        raise

def download_from_s3(s3_key: str) -> bytes:
    """Download file from S3"""
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        return response['Body'].read()
    except Exception as e:
        logger.error(f"Failed to download from S3: {s3_key}", exc_info=True)
        raise

def upload_results_to_s3(s3_key: str, transactions: List[Dict]) -> None:
    """Upload extraction results to S3"""
    try:
        results_data = {
            "total_transactions": len(transactions),
            "transactions": transactions,
            "processed_at": context.aws_request_id
        }
        
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(results_data, default=str),
            ContentType='application/json'
        )
    except Exception as e:
        logger.error(f"Failed to upload results to S3: {s3_key}", exc_info=True)
        raise

def update_job_status(job_id: str, status: str, additional_data: Dict = None) -> None:
    """Update job status in DynamoDB"""
    try:
        table = dynamodb.Table(JOBS_TABLE_NAME)
        
        update_expression = "SET #status = :status"
        expression_attribute_names = {"#status": "status"}
        expression_attribute_values = {":status": status}
        
        if additional_data:
            for key, value in additional_data.items():
                update_expression += f", #{key} = :{key}"
                expression_attribute_names[f"#{key}"] = key
                expression_attribute_values[f":{key}"] = value
        
        table.update_item(
            Key={"job_id": job_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )
        
        logger.info(f"Updated job status to {status}", extra={"job_id": job_id})
        
    except Exception as e:
        logger.error(f"Failed to update job status in DynamoDB: {job_id}", exc_info=True)
        # Don't raise here as this is not critical to the processing