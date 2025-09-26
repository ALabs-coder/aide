#!/usr/bin/env python3
"""
Simple AWS Lambda handler for PDF Extractor API
Direct API Gateway integration without FastAPI
"""

import json
import logging
from datetime import datetime, timezone
import os
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal
import base64
import io
from botocore.exceptions import ClientError

# Custom JSON encoder for DynamoDB Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration - fail fast if environment variables are missing
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
JOBS_TABLE_NAME = os.getenv('JOBS_TABLE_NAME')
BANK_CONFIGURATIONS_TABLE = os.getenv('BANK_CONFIGURATIONS_TABLE')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')  # AWS region can have a reasonable default

# Validate required environment variables
if not S3_BUCKET_NAME:
    raise ValueError("S3_BUCKET_NAME environment variable is required")
if not JOBS_TABLE_NAME:
    raise ValueError("JOBS_TABLE_NAME environment variable is required")
if not BANK_CONFIGURATIONS_TABLE:
    raise ValueError("BANK_CONFIGURATIONS_TABLE environment variable is required")

# Initialize AWS clients
s3_client = boto3.client('s3', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

def handler(event, context):
    """
    AWS Lambda entry point for API Gateway events

    Args:
        event: API Gateway event data
        context: Lambda context object

    Returns:
        API Gateway response
    """
    try:
        # Extract request details
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        query_params = event.get('queryStringParameters') or {}
        body = event.get('body', '')

        logger.info(f"Request: {http_method} {path}")

        # CORS headers for all responses
        cors_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, X-API-Key, Authorization',
            'Content-Type': 'application/json'
        }

        # Handle OPTIONS (CORS preflight)
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({'message': 'CORS preflight'})
            }

        # Route based on path and method
        if path == '/' and http_method == 'GET':
            return handle_root()

        elif path == '/health' and http_method == 'GET':
            return handle_health()

        elif path == '/statements' and http_method == 'GET':
            return handle_get_statements(event)

        elif path.startswith('/pdf/') and http_method == 'GET':
            # Extract job_id from path /pdf/{job_id}
            job_id = path.split('/')[-1]
            return handle_get_pdf(job_id)

        elif path == '/configurations/banks' and http_method == 'GET':
            return handle_get_bank_configurations()

        else:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Not Found',
                    'message': f'Path {path} not found'
                })
            }

    except Exception as e:
        logger.error(f"Lambda error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal Server Error',
                'message': str(e),
                'request_id': context.aws_request_id
            })
        }

def handle_root():
    """Handle root endpoint"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': 'PDF Bank Statement Extraction API',
            'version': '2.0.0',
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    }

def handle_health():
    """Handle health check endpoint"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'status': 'healthy',
            'version': '2.0.0',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'environment': 'production'
        })
    }

def handle_get_statements(event):
    """Handle GET /statements endpoint"""
    try:
        table = dynamodb.Table(JOBS_TABLE_NAME)

        try:
            # Query by status using GSI - much more efficient than scan
            # Get items by common statuses to reduce RCUs
            items = []
            common_statuses = ['uploaded', 'processing', 'completed', 'failed']

            for status in common_statuses:
                response = table.query(
                    IndexName='status-index',
                    KeyConditionExpression='#status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':status': status},
                    ScanIndexForward=False  # Sort by created_at descending (newest first)
                )
                items.extend(response.get('Items', []))

                # Handle pagination for each status
                while 'LastEvaluatedKey' in response:
                    response = table.query(
                        IndexName='status-index',
                        KeyConditionExpression='#status = :status',
                        ExpressionAttributeNames={'#status': 'status'},
                        ExpressionAttributeValues={':status': status},
                        ScanIndexForward=False,
                        ExclusiveStartKey=response['LastEvaluatedKey']
                    )
                    items.extend(response.get('Items', []))

        except Exception as e:
            logger.error(f"Error querying DynamoDB: {e}")
            items = []

        # Transform DynamoDB items to frontend format
        statements = []
        for item in items:
            # Safe conversion with proper null checks
            file_size_mb = item.get('file_size_mb')
            if file_size_mb is not None:
                # Keep as Decimal for precision, convert to float only for JSON serialization
                file_size_mb_val = float(file_size_mb)
            else:
                file_size_mb_val = 0.0

            file_size_bytes = item.get('file_size_bytes')
            if file_size_bytes is not None:
                file_size_bytes_val = int(file_size_bytes)
            else:
                file_size_bytes_val = 0

            # Extract bank name from statement metadata if available
            statement_metadata = item.get('statement_metadata', {})
            bank_name = statement_metadata.get('bank_name')

            statement = {
                "id": item.get('job_id'),
                "documentName": item.get('original_filename', 'Unknown'),
                "dateUploaded": item.get('upload_timestamp', item.get('created_at', '')),
                "dateProcessed": item.get('completed_at'),
                "status": item.get('status', 'uploaded'),
                "bankName": bank_name,
                "customerName": None,  # Not available in current extraction
                "fileSize": file_size_mb_val,
                "fileSizeBytes": file_size_bytes_val,
                # New fields from job data
                "error": item.get('error'),
                "processing_started_at": item.get('processing_started_at'),
                "failed_at": item.get('failed_at'),
                "metadata": item.get('metadata', {}),
                "job_type": item.get('job_type'),
                "content_type": item.get('content_type'),
                # Financial and statement data from completed extractions
                "financial_summary": item.get('financial_summary'),
                "total_transactions": item.get('total_transactions'),
                "statement_metadata": statement_metadata
            }
            statements.append(statement)

        # Sort by upload timestamp (newest first)
        statements.sort(key=lambda x: x.get('dateUploaded', ''), reverse=True)

        logger.info(f"Retrieved {len(statements)} statements")

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'statements': statements,
                'total': len(statements),
                'status': 'success'
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error(f"Error in handle_get_statements: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal Server Error',
                'message': 'Failed to retrieve statements',
                'statements': [],
                'total': 0,
                'status': 'error'
            }, cls=DecimalEncoder)
        }


def handle_get_bank_configurations():
    """Handle GET /configurations/banks endpoint"""
    try:
        table = dynamodb.Table(BANK_CONFIGURATIONS_TABLE)

        # Query all bank configurations with status ACTIVE
        response = table.query(
            KeyConditionExpression=Key('PK').eq('BANK_CONFIG'),
            FilterExpression='#status = :status',
            ExpressionAttributeNames={
                '#status': 'Status'
            },
            ExpressionAttributeValues={
                ':status': 'ACTIVE'
            }
        )

        # Transform to minimal response format
        active_banks = []
        for item in response.get('Items', []):
            active_banks.append({
                'id': item.get('BankCode'),
                'name': item.get('BankName')
            })

        # Sort alphabetically by bank name
        active_banks.sort(key=lambda x: x['name'])

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-API-Key, Authorization'
            },
            'body': json.dumps({
                'status': 'success',
                'data': active_banks,
                'count': len(active_banks)
            })
        }

    except ClientError as e:
        logger.error(f"DynamoDB error in handle_get_bank_configurations: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'error',
                'error': 'Database Error',
                'message': 'Failed to retrieve bank configurations',
                'data': [],
                'count': 0
            })
        }
    except Exception as e:
        logger.error(f"Error in handle_get_bank_configurations: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'error',
                'error': 'Internal Server Error',
                'message': 'Failed to retrieve bank configurations',
                'data': [],
                'count': 0
            })
        }

