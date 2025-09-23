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
from decimal import Decimal

# Import the extraction function (it's in the same package now)
from extract_pdf_data import extract_bank_statement_data

# Setup basic logging for Lambda
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# AWS clients
s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

# Environment variables
JOBS_TABLE_NAME = os.getenv('JOBS_TABLE_NAME', 'pdf-extractor-jobs')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'pdf-extractor-storage')

def convert_floats_to_decimal(obj):
    """Convert float values to Decimal for DynamoDB compatibility"""
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    else:
        return obj

def get_job_data(job_id):
    """Retrieve job data from DynamoDB"""
    try:
        table = dynamodb.Table(JOBS_TABLE_NAME)
        response = table.get_item(Key={'job_id': job_id})

        if 'Item' not in response:
            raise ValueError(f"Job not found: {job_id}")

        return response['Item']
    except Exception as e:
        logger.error(f"Failed to retrieve job data: {e}")
        raise


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

        logger.info("Processing SQS message", extra={
            "message_id": message_id,
            "message_body": message_body
        })

        job_id = message_body.get('job_id')
        s3_key = message_body.get('s3_key')
        user_id = message_body.get('user_id')

        if not job_id or not s3_key:
            logger.error("Invalid SQS message format", extra={
                "message_id": message_id,
                "job_id": job_id,
                "s3_key": s3_key,
                "message_body": message_body
            })
            raise ValueError(f"Missing required job_id or s3_key in message. job_id: {job_id}, s3_key: {s3_key}")

        # Retrieve job data from DynamoDB to get password
        job_data = get_job_data(job_id)

        # Get password if exists
        password = job_data.get('password')
        if password:
            logger.info(f"Password found for job: {job_id}, length: {len(password)}")
        else:
            logger.info(f"No password for job: {job_id}")
        
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
            # Use enhanced extraction to get complete statement data
            extraction_result = extract_bank_statement_data(tmp_file_path, password, enhanced=True)

            # Handle both enhanced (dict) and legacy (list) results
            if isinstance(extraction_result, dict):
                # Enhanced extraction with metadata
                transactions = extraction_result.get('transactions', [])
                statement_metadata = extraction_result.get('statement_metadata', {})
                financial_summary = extraction_result.get('financial_summary', {})

                # Upload complete results to S3
                results_key = f"results/{job_id}/transactions.json"
                upload_complete_results_to_s3(results_key, extraction_result)

                # Update job status with enhanced metadata
                update_data = {
                    "completed_at": context.aws_request_id,
                    "total_transactions": len(transactions),
                    "results_s3_key": results_key,
                    "statement_metadata": statement_metadata,
                    "financial_summary": financial_summary
                }

            else:
                # Legacy extraction (list of transactions)
                transactions = extraction_result if extraction_result else []

                # Upload legacy results to S3
                results_key = f"results/{job_id}/transactions.json"
                upload_results_to_s3(results_key, transactions)

                # Update job status (legacy format)
                update_data = {
                    "completed_at": context.aws_request_id,
                    "total_transactions": len(transactions),
                    "results_s3_key": results_key
                }

            update_job_status(job_id, "completed", update_data)
            
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
        
        # Update job status to failed (only if we have a valid job_id)
        if 'job_id' in locals() and job_id:
            try:
                update_job_status(job_id, "failed", {
                    "failed_at": context.aws_request_id,
                    "error": str(e)
                })
            except Exception as update_error:
                logger.error("Failed to update job status to failed", extra={
                    "job_id": job_id,
                    "original_error": str(e),
                    "update_error": str(update_error)
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
    """Upload extraction results to S3 (legacy format)"""
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

def upload_complete_results_to_s3(s3_key: str, complete_data: Dict) -> None:
    """Upload complete enhanced extraction results to S3"""
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(complete_data, default=str, indent=2),
            ContentType='application/json'
        )
        logger.info(f"Uploaded complete results to S3: {s3_key}")
    except Exception as e:
        logger.error(f"Failed to upload complete results to S3: {s3_key}", exc_info=True)
        raise

def update_job_status(job_id: str, status: str, additional_data: Dict = None) -> None:
    """Update job status in DynamoDB"""
    if not job_id:
        logger.error("Cannot update job status: job_id is None or empty")
        return

    try:
        table = dynamodb.Table(JOBS_TABLE_NAME)
        
        update_expression = "SET #status = :status"
        expression_attribute_names = {"#status": "status"}
        expression_attribute_values = {":status": status}
        
        if additional_data:
            for key, value in additional_data.items():
                update_expression += f", #{key} = :{key}"
                expression_attribute_names[f"#{key}"] = key
                expression_attribute_values[f":{key}"] = convert_floats_to_decimal(value)
        
        table.update_item(
            Key={"job_id": job_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )
        
        logger.info(f"Updated job status to {status}", extra={"job_id": job_id})
        
    except Exception as e:
        logger.error(f"Failed to update job status in DynamoDB: {job_id} - {e}", exc_info=True)
        # Don't raise here as this is not critical to the processing