#!/usr/bin/env python3
"""
AWS Lambda handler for processing Dead Letter Queue (DLQ) messages
Handles failed processing jobs for retry or manual intervention
"""

import json
import boto3
import os
import sys
from datetime import datetime
from typing import Dict, List
import logging

# Add parent directories to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from logging_config import setup_logging

# Setup logging for Lambda
setup_logging()
logger = logging.getLogger(__name__)

# AWS clients
s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')

# Environment variables - fail fast if missing
JOBS_TABLE_NAME = os.getenv('JOBS_TABLE_NAME')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
ALERT_SNS_TOPIC = os.getenv('ALERT_SNS_TOPIC')
MAX_RETRY_COUNT = int(os.getenv('MAX_RETRY_COUNT', '3'))  # Reasonable default for retry count

# Validate required environment variables
if not JOBS_TABLE_NAME:
    raise ValueError("JOBS_TABLE_NAME environment variable is required")
if not S3_BUCKET_NAME:
    raise ValueError("S3_BUCKET_NAME environment variable is required")

def handler(event, context):
    """
    AWS Lambda entry point for DLQ message processing
    
    Args:
        event: SQS DLQ event containing failed message records
        context: Lambda context object
        
    Returns:
        Processing results
    """
    try:
        logger.info("DLQ Processor Lambda invocation started", extra={
            "request_id": context.aws_request_id,
            "function_name": context.function_name,
            "records_count": len(event.get('Records', []))
        })
        
        results = []
        critical_failures = []
        
        # Process each DLQ message
        for record in event.get('Records', []):
            try:
                result = process_dlq_message(record, context)
                results.append(result)
                
                # Track critical failures for alerting
                if result.get("action") == "critical_failure":
                    critical_failures.append(result)
                    
            except Exception as e:
                logger.error("Failed to process DLQ record", extra={
                    "request_id": context.aws_request_id,
                    "message_id": record.get('messageId'),
                    "error": str(e)
                }, exc_info=True)
                
                critical_failures.append({
                    "messageId": record.get('messageId'),
                    "status": "processing_failed",
                    "error": str(e)
                })
        
        # Send alerts for critical failures
        if critical_failures and ALERT_SNS_TOPIC:
            send_failure_alert(critical_failures, context)
        
        logger.info("DLQ Processor Lambda completed", extra={
            "request_id": context.aws_request_id,
            "processed": len(results),
            "critical_failures": len(critical_failures)
        })
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "processed": len(results),
                "critical_failures": len(critical_failures),
                "results": results
            })
        }
        
    except Exception as e:
        logger.error("DLQ Processor Lambda failed", extra={
            "request_id": context.aws_request_id,
            "error": str(e)
        }, exc_info=True)
        
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "DLQ processing failed",
                "message": str(e)
            })
        }

def process_dlq_message(record: Dict, context) -> Dict:
    """
    Process individual DLQ message
    
    Args:
        record: SQS DLQ message record
        context: Lambda context
        
    Returns:
        Processing result with recommended action
    """
    message_id = record.get('messageId')
    receipt_handle = record.get('receiptHandle')
    
    try:
        # Parse the original failed message
        message_body = json.loads(record['body'])
        
        job_id = message_body.get('job_id')
        s3_key = message_body.get('s3_key')
        user_id = message_body.get('user_id')
        
        # Get additional attributes from SQS
        attributes = record.get('attributes', {})
        approximate_receive_count = int(attributes.get('ApproximateReceiveCount', 1))
        
        logger.info("Processing DLQ message", extra={
            "job_id": job_id,
            "message_id": message_id,
            "user_id": user_id,
            "receive_count": approximate_receive_count
        })
        
        # Analyze the failure
        failure_analysis = analyze_failure(job_id, message_body, attributes)
        
        # Determine action based on failure type and retry count
        if approximate_receive_count >= MAX_RETRY_COUNT:
            action = "critical_failure"
            # Mark job as permanently failed
            update_job_status(job_id, "permanently_failed", {
                "failed_at": datetime.utcnow().isoformat(),
                "failure_reason": failure_analysis.get("reason"),
                "dlq_message_id": message_id,
                "retry_count": approximate_receive_count
            })
        elif failure_analysis.get("retryable", False):
            action = "retry"
            # Could implement retry logic here or send back to main queue
            update_job_status(job_id, "retry_scheduled", {
                "retry_scheduled_at": datetime.utcnow().isoformat(),
                "retry_count": approximate_receive_count,
                "failure_reason": failure_analysis.get("reason")
            })
        else:
            action = "manual_review"
            # Mark for manual intervention
            update_job_status(job_id, "requires_manual_review", {
                "review_required_at": datetime.utcnow().isoformat(),
                "failure_reason": failure_analysis.get("reason"),
                "dlq_message_id": message_id
            })
        
        return {
            "messageId": message_id,
            "job_id": job_id,
            "action": action,
            "failure_analysis": failure_analysis,
            "retry_count": approximate_receive_count,
            "status": "processed"
        }
        
    except Exception as e:
        logger.error("Error processing DLQ message", extra={
            "message_id": message_id,
            "error": str(e)
        }, exc_info=True)
        
        return {
            "messageId": message_id,
            "status": "processing_failed",
            "error": str(e),
            "action": "critical_failure"
        }

def analyze_failure(job_id: str, message_body: Dict, attributes: Dict) -> Dict:
    """
    Analyze the failure to determine if it's retryable and the root cause
    
    Args:
        job_id: Job identifier
        message_body: Original message content
        attributes: SQS message attributes
        
    Returns:
        Failure analysis results
    """
    try:
        # Get job details from DynamoDB
        table = dynamodb.Table(JOBS_TABLE_NAME)
        response = table.get_item(Key={'job_id': job_id})
        job_data = response.get('Item', {})
        
        # Common failure patterns
        failure_patterns = {
            "timeout": {
                "retryable": True,
                "reason": "Processing timeout - possibly large file or resource constraints"
            },
            "memory": {
                "retryable": False,
                "reason": "Memory limit exceeded - file too large for processing"
            },
            "pdf_password": {
                "retryable": False,
                "reason": "PDF password protection or corruption"
            },
            "s3_access": {
                "retryable": True,
                "reason": "S3 access issues - temporary connectivity problem"
            },
            "permission": {
                "retryable": False,
                "reason": "Permission denied - IAM role misconfiguration"
            },
            "unknown": {
                "retryable": True,
                "reason": "Unknown error - worth retrying once"
            }
        }
        
        # Try to determine failure type from job status and error messages
        last_error = job_data.get('last_error', '').lower()
        
        if 'timeout' in last_error or 'time limit exceeded' in last_error:
            failure_type = "timeout"
        elif 'memory' in last_error or 'out of memory' in last_error:
            failure_type = "memory"
        elif 'password' in last_error or 'decrypt' in last_error:
            failure_type = "pdf_password"
        elif 's3' in last_error or 'bucket' in last_error:
            failure_type = "s3_access"
        elif 'permission' in last_error or 'access denied' in last_error:
            failure_type = "permission"
        else:
            failure_type = "unknown"
        
        analysis = failure_patterns.get(failure_type, failure_patterns["unknown"])
        analysis["failure_type"] = failure_type
        analysis["job_data"] = {
            "status": job_data.get("status"),
            "created_at": job_data.get("created_at"),
            "file_size_mb": job_data.get("file_size_mb"),
            "last_error": job_data.get("last_error", "")[:200]  # Truncate for logging
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"Failed to analyze failure for job {job_id}", exc_info=True)
        return {
            "failure_type": "analysis_failed",
            "retryable": False,
            "reason": f"Could not analyze failure: {str(e)}"
        }

def update_job_status(job_id: str, status: str, additional_data: Dict = None) -> None:
    """Update job status in DynamoDB"""
    try:
        table = dynamodb.Table(JOBS_TABLE_NAME)
        
        update_expression = "SET #status = :status, last_updated = :updated"
        expression_attribute_names = {"#status": "status"}
        expression_attribute_values = {
            ":status": status,
            ":updated": datetime.utcnow().isoformat()
        }
        
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

def send_failure_alert(critical_failures: List[Dict], context) -> None:
    """
    Send SNS alert for critical failures
    
    Args:
        critical_failures: List of critical failure records
        context: Lambda context
    """
    try:
        if not ALERT_SNS_TOPIC:
            logger.warning("No SNS topic configured for alerts")
            return
        
        alert_message = {
            "timestamp": datetime.utcnow().isoformat(),
            "lambda_function": context.function_name,
            "request_id": context.aws_request_id,
            "critical_failures_count": len(critical_failures),
            "failures": critical_failures[:5]  # Limit to first 5 for readability
        }
        
        sns_client.publish(
            TopicArn=ALERT_SNS_TOPIC,
            Subject=f"PDF Extractor DLQ - {len(critical_failures)} Critical Failures",
            Message=json.dumps(alert_message, indent=2, default=str)
        )
        
        logger.info(f"Sent failure alert for {len(critical_failures)} critical failures")
        
    except Exception as e:
        logger.error("Failed to send failure alert", exc_info=True)