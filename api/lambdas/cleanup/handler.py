#!/usr/bin/env python3
"""
AWS Lambda handler for daily cleanup of old files and records
Runs on CloudWatch Events schedule (cron)
"""

import json
import boto3
import os
import sys
from datetime import datetime, timedelta
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
dynamodb = boto3.resource('dynamodb')

# Environment variables - fail fast if missing
JOBS_TABLE_NAME = os.getenv('JOBS_TABLE_NAME')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
CLEANUP_DAYS = int(os.getenv('CLEANUP_DAYS', '30'))  # Reasonable default for cleanup period

# Validate required environment variables
if not JOBS_TABLE_NAME:
    raise ValueError("JOBS_TABLE_NAME environment variable is required")
if not S3_BUCKET_NAME:
    raise ValueError("S3_BUCKET_NAME environment variable is required")

def handler(event, context):
    """
    AWS Lambda entry point for scheduled cleanup
    
    Args:
        event: CloudWatch Events event
        context: Lambda context object
        
    Returns:
        Cleanup results
    """
    try:
        logger.info("Cleanup Lambda invocation started", extra={
            "request_id": context.aws_request_id,
            "function_name": context.function_name,
            "cleanup_days": CLEANUP_DAYS
        })
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=CLEANUP_DAYS)
        
        # Perform cleanup operations
        results = {
            "dynamodb_cleanup": cleanup_old_jobs(cutoff_date),
            "s3_cleanup": cleanup_old_files(cutoff_date),
            "cleanup_date": cutoff_date.isoformat(),
            "total_days": CLEANUP_DAYS
        }
        
        logger.info("Cleanup Lambda completed successfully", extra={
            "request_id": context.aws_request_id,
            "jobs_deleted": results["dynamodb_cleanup"]["deleted_count"],
            "files_deleted": results["s3_cleanup"]["deleted_count"]
        })
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Cleanup completed successfully",
                "results": results
            }, default=str)
        }
        
    except Exception as e:
        logger.error("Cleanup Lambda failed", extra={
            "request_id": context.aws_request_id,
            "error": str(e)
        }, exc_info=True)
        
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Cleanup failed",
                "message": str(e)
            })
        }

def cleanup_old_jobs(cutoff_date: datetime) -> Dict:
    """
    Clean up old job records from DynamoDB
    
    Args:
        cutoff_date: Delete jobs older than this date
        
    Returns:
        Cleanup results
    """
    try:
        table = dynamodb.Table(JOBS_TABLE_NAME)
        deleted_count = 0
        errors = []
        
        # Scan for old jobs (this could be expensive for large tables)
        # In production, consider using a GSI with created_at as sort key
        response = table.scan(
            FilterExpression="created_at < :cutoff",
            ExpressionAttributeValues={
                ":cutoff": cutoff_date.isoformat()
            }
        )
        
        # Delete old jobs in batches
        with table.batch_writer() as batch:
            for item in response.get('Items', []):
                try:
                    batch.delete_item(Key={'job_id': item['job_id']})
                    deleted_count += 1
                    
                    logger.info("Deleted old job record", extra={
                        "job_id": item['job_id'],
                        "created_at": item.get('created_at'),
                        "status": item.get('status')
                    })
                    
                except Exception as e:
                    error_msg = f"Failed to delete job {item.get('job_id')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
        
        # Handle pagination if there are more records
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression="created_at < :cutoff",
                ExpressionAttributeValues={
                    ":cutoff": cutoff_date.isoformat()
                },
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            
            with table.batch_writer() as batch:
                for item in response.get('Items', []):
                    try:
                        batch.delete_item(Key={'job_id': item['job_id']})
                        deleted_count += 1
                    except Exception as e:
                        error_msg = f"Failed to delete job {item.get('job_id')}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
        
        return {
            "deleted_count": deleted_count,
            "errors": errors,
            "status": "success"
        }
        
    except Exception as e:
        logger.error("DynamoDB cleanup failed", exc_info=True)
        return {
            "deleted_count": 0,
            "errors": [str(e)],
            "status": "failed"
        }

def cleanup_old_files(cutoff_date: datetime) -> Dict:
    """
    Clean up old files from S3
    
    Args:
        cutoff_date: Delete files older than this date
        
    Returns:
        Cleanup results
    """
    try:
        deleted_count = 0
        errors = []
        
        # List objects in uploads/ and results/ prefixes
        prefixes = ['uploads/', 'results/']
        
        for prefix in prefixes:
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=S3_BUCKET_NAME, Prefix=prefix)
            
            objects_to_delete = []
            
            for page in pages:
                for obj in page.get('Contents', []):
                    # Check if file is older than cutoff date
                    if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                        objects_to_delete.append({'Key': obj['Key']})
                        
                        # Delete in batches of 1000 (S3 limit)
                        if len(objects_to_delete) >= 1000:
                            result = delete_s3_objects(objects_to_delete)
                            deleted_count += result['deleted']
                            errors.extend(result['errors'])
                            objects_to_delete = []
            
            # Delete remaining objects
            if objects_to_delete:
                result = delete_s3_objects(objects_to_delete)
                deleted_count += result['deleted']
                errors.extend(result['errors'])
        
        return {
            "deleted_count": deleted_count,
            "errors": errors,
            "status": "success"
        }
        
    except Exception as e:
        logger.error("S3 cleanup failed", exc_info=True)
        return {
            "deleted_count": 0,
            "errors": [str(e)],
            "status": "failed"
        }

def delete_s3_objects(objects: List[Dict]) -> Dict:
    """
    Delete a batch of S3 objects
    
    Args:
        objects: List of objects to delete
        
    Returns:
        Deletion results
    """
    try:
        response = s3_client.delete_objects(
            Bucket=S3_BUCKET_NAME,
            Delete={
                'Objects': objects,
                'Quiet': False
            }
        )
        
        deleted_count = len(response.get('Deleted', []))
        errors = []
        
        for error in response.get('Errors', []):
            error_msg = f"Failed to delete {error['Key']}: {error['Message']}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # Log successful deletions
        for deleted in response.get('Deleted', []):
            logger.info(f"Deleted old S3 object: {deleted['Key']}")
        
        return {
            "deleted": deleted_count,
            "errors": errors
        }
        
    except Exception as e:
        logger.error("Failed to delete S3 objects batch", exc_info=True)
        return {
            "deleted": 0,
            "errors": [str(e)]
        }