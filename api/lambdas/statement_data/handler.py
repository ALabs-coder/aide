#!/usr/bin/env python3
"""
AWS Lambda handler for Statement Data API
Fetches processed JSON data from S3 for completed PDF extractions
"""

import json
import logging
from datetime import datetime, timezone
import os
import boto3
from decimal import Decimal

# Import shared formatting utilities
from formatters.transaction_formatter import format_transactions_for_ui

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom JSON encoder for DynamoDB Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

# Configuration
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'pdf-extractor-api-storage')
JOBS_TABLE_NAME = os.getenv('JOBS_TABLE_NAME', 'pdf-extractor-api-jobs')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

# Initialize AWS clients
s3_client = boto3.client('s3', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

def handler(event, context):
    """
    AWS Lambda entry point for Statement Data API

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

        logger.info(f"Statement Data request: {http_method} {path}")

        # CORS headers for all responses
        cors_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
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

        # Only handle GET requests
        if http_method != 'GET':
            return {
                'statusCode': 405,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Method Not Allowed',
                    'message': 'Only GET method is supported'
                })
            }

        # Extract job_id from path parameters or query parameters
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}

        job_id = path_parameters.get('job_id') or query_parameters.get('job_id')

        if not job_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Bad Request',
                    'message': 'job_id is required as path or query parameter'
                }, cls=DecimalEncoder)
            }

        return handle_get_statement_data(job_id, cors_headers)

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

def handle_get_statement_data(job_id, cors_headers):
    """Handle GET request for statement data"""
    try:
        # Get job details from DynamoDB
        table = dynamodb.Table(JOBS_TABLE_NAME)

        response = table.get_item(Key={'job_id': job_id})

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Statement not found',
                    'message': f'No statement found with ID: {job_id}'
                }, cls=DecimalEncoder)
            }

        job_item = response['Item']

        # Check if processing is complete
        if job_item.get('status') != 'completed':
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Processing not complete',
                    'message': f'Statement processing status: {job_item.get("status", "unknown")}',
                    'status': job_item.get('status', 'unknown'),
                    'job_id': job_id
                }, cls=DecimalEncoder)
            }

        # Get the S3 results key
        results_s3_key = job_item.get('results_s3_key')

        if not results_s3_key:
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Results not found',
                    'message': 'No results file available for this statement',
                    'job_id': job_id
                }, cls=DecimalEncoder)
            }

        # Fetch the JSON data from S3
        try:
            logger.info(f"Fetching data from S3: bucket={S3_BUCKET_NAME}, key={results_s3_key}")

            s3_response = s3_client.get_object(
                Bucket=S3_BUCKET_NAME,
                Key=results_s3_key
            )

            # Read and parse the JSON content
            content = s3_response['Body'].read().decode('utf-8')
            statement_data = json.loads(content)

            # Format transactions for UI consistency
            if 'transactions' in statement_data and statement_data['transactions']:
                logger.info(f"Formatting {len(statement_data['transactions'])} transactions for UI")
                statement_data['transactions'] = format_transactions_for_ui(statement_data['transactions'])

            logger.info(f"Successfully retrieved data for job {job_id}")

            # Return the complete data with metadata
            return {
                'statusCode': 200,
                'headers': cors_headers,
                'body': json.dumps({
                    'status': 'success',
                    'job_id': job_id,
                    'statement_metadata': job_item.get('statement_metadata', {}),
                    'financial_summary': job_item.get('financial_summary', {}),
                    'original_filename': job_item.get('original_filename'),
                    'processing_completed_at': job_item.get('completed_at'),
                    'upload_timestamp': job_item.get('upload_timestamp'),
                    'total_transactions': job_item.get('total_transactions'),
                    'data': statement_data
                }, cls=DecimalEncoder)
            }

        except s3_client.exceptions.NoSuchKey:
            logger.error(f"S3 file not found: {results_s3_key}")
            return {
                'statusCode': 404,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Results file not found',
                    'message': 'The results file has been moved or deleted',
                    'job_id': job_id,
                    's3_key': results_s3_key
                }, cls=DecimalEncoder)
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from S3: {e}")
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Invalid data format',
                    'message': 'The results file contains invalid JSON',
                    'job_id': job_id
                }, cls=DecimalEncoder)
            }

        except Exception as e:
            logger.error(f"S3 access error: {e}")
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Storage access error',
                    'message': 'Failed to retrieve data from storage',
                    'job_id': job_id
                }, cls=DecimalEncoder)
            }

    except Exception as e:
        logger.error(f"Error in handle_get_statement_data: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'error': 'Internal Server Error',
                'message': 'Failed to retrieve statement data',
                'job_id': job_id
            }, cls=DecimalEncoder)
        }