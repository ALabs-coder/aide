#!/usr/bin/env python3
"""
AWS Lambda handler for Excel Export API
Fetches processed JSON data from S3 and converts to Excel format for download
"""

import json
import logging
from datetime import datetime
import os
import boto3
from decimal import Decimal
import base64
from io import BytesIO

# Import shared formatting utilities
from formatters.excel_formatter import (
    create_excel_workbook,
    get_statement_filename
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom JSON encoder for DynamoDB Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

# Configuration - fail fast if environment variables are missing
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
JOBS_TABLE_NAME = os.getenv('JOBS_TABLE_NAME')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')  # AWS region can have a reasonable default

# Validate required environment variables
if not S3_BUCKET_NAME:
    raise ValueError("S3_BUCKET_NAME environment variable is required")
if not JOBS_TABLE_NAME:
    raise ValueError("JOBS_TABLE_NAME environment variable is required")

# Initialize AWS clients
s3_client = boto3.client('s3', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

def handler(event, context):
    """
    AWS Lambda entry point for Excel Export API

    Args:
        event: API Gateway event data
        context: Lambda context object

    Returns:
        API Gateway response with Excel content
    """
    try:
        # Extract request details
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')

        logger.info(f"Excel Export request: {http_method} {path}")

        # CORS headers for all responses
        cors_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, X-API-Key, Authorization'
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
                'headers': {**cors_headers, 'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Method Not Allowed',
                    'message': 'Only GET method is supported'
                })
            }

        # Extract job_id from path parameters
        path_parameters = event.get('pathParameters') or {}
        job_id = path_parameters.get('job_id')

        if not job_id:
            return {
                'statusCode': 400,
                'headers': {**cors_headers, 'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Bad Request',
                    'message': 'job_id is required as path parameter'
                }, cls=DecimalEncoder)
            }

        return handle_excel_export(job_id, cors_headers)

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

def handle_excel_export(job_id, cors_headers):
    """Handle Excel export request"""
    try:
        # Get job details from DynamoDB (same logic as statement_data Lambda)
        table = dynamodb.Table(JOBS_TABLE_NAME)
        response = table.get_item(Key={'job_id': job_id})

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {**cors_headers, 'Content-Type': 'application/json'},
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
                'headers': {**cors_headers, 'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Processing not complete',
                    'message': f'Statement processing status: {job_item.get("status", "unknown")}',
                    'status': job_item.get('status', 'unknown'),
                    'job_id': job_id
                }, cls=DecimalEncoder)
            }

        # Check if Excel file already exists in S3
        excel_s3_key = job_item.get('excel_s3_key')

        if excel_s3_key:
            # Excel file exists, generate presigned URL for direct download
            try:
                logger.info(f"Excel file exists in S3: {excel_s3_key}")

                # Check if file actually exists in S3
                try:
                    s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=excel_s3_key)
                except s3_client.exceptions.NoSuchKey:
                    logger.warning(f"Excel file not found in S3, will generate on-demand: {excel_s3_key}")
                    excel_s3_key = None

                if excel_s3_key:
                    # Generate filename using metadata
                    statement_metadata = job_item.get('statement_metadata', {})
                    filename = get_statement_filename(statement_metadata, job_id, 'xlsx')

                    # Generate presigned URL for download (valid for 1 hour)
                    presigned_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': S3_BUCKET_NAME, 'Key': excel_s3_key},
                        ExpiresIn=3600,  # 1 hour
                        HttpMethod='GET'
                    )

                    logger.info(f"Generated presigned URL for Excel download: {job_id}")

                    # Return redirect to presigned URL
                    return {
                        'statusCode': 302,
                        'headers': {
                            **cors_headers,
                            'Location': presigned_url,
                            'Content-Disposition': f'attachment; filename="{filename}"'
                        },
                        'body': json.dumps({
                            'download_url': presigned_url,
                            'filename': filename,
                            'job_id': job_id
                        }, cls=DecimalEncoder)
                    }

            except Exception as e:
                logger.error(f"Error generating presigned URL: {e}", exc_info=True)
                # Fall through to on-demand generation

        # Excel file doesn't exist or error occurred, fall back to on-demand generation
        logger.info(f"Excel file not available in S3, generating on-demand for job {job_id}")

        # Get the S3 results key for JSON data
        results_s3_key = job_item.get('results_s3_key')

        if not results_s3_key:
            return {
                'statusCode': 404,
                'headers': {**cors_headers, 'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Results not found',
                    'message': 'No results file available for this statement',
                    'job_id': job_id
                }, cls=DecimalEncoder)
            }

        # Fetch the JSON data from S3 (same logic as statement_data Lambda)
        try:
            logger.info(f"Fetching data from S3 for Excel export: bucket={S3_BUCKET_NAME}, key={results_s3_key}")

            s3_response = s3_client.get_object(
                Bucket=S3_BUCKET_NAME,
                Key=results_s3_key
            )

            # Read and parse the JSON content
            content = s3_response['Body'].read().decode('utf-8')
            statement_data = json.loads(content)

            # Extract transactions
            transactions = statement_data.get('transactions', [])

            if not transactions:
                return {
                    'statusCode': 404,
                    'headers': {**cors_headers, 'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'error': 'No transactions found',
                        'message': 'This statement contains no transaction data',
                        'job_id': job_id
                    }, cls=DecimalEncoder)
                }

            # Generate Excel content using shared formatter
            logger.info(f"About to call create_excel_workbook with {len(transactions)} transactions")
            try:
                excel_buffer = create_excel_workbook(transactions)
                logger.info("Excel generation completed successfully")
            except Exception as e:
                logger.error(f"Error in create_excel_workbook: {e}", exc_info=True)
                raise

            # Store Excel file in S3 for future use
            excel_s3_key = f"results/{job_id}/statement.xlsx"
            try:
                s3_client.put_object(
                    Bucket=S3_BUCKET_NAME,
                    Key=excel_s3_key,
                    Body=excel_buffer.getvalue(),
                    ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                logger.info(f"Stored Excel file in S3 for future use: {excel_s3_key}")

                # Update job record with Excel S3 key
                try:
                    table = dynamodb.Table(JOBS_TABLE_NAME)
                    table.update_item(
                        Key={'job_id': job_id},
                        UpdateExpression="SET excel_s3_key = :excel_key",
                        ExpressionAttributeValues={':excel_key': excel_s3_key}
                    )
                    logger.info(f"Updated job record with Excel S3 key: {job_id}")
                except Exception as update_error:
                    logger.error(f"Failed to update job record with Excel S3 key: {update_error}")

            except Exception as store_error:
                logger.error(f"Failed to store Excel file in S3: {store_error}")
                # Continue with on-demand response even if storage fails

            # Generate filename using metadata
            statement_metadata = job_item.get('statement_metadata', {})
            filename = get_statement_filename(statement_metadata, job_id, 'xlsx')

            logger.info(f"Generated Excel with {len(transactions)} transactions for job {job_id}")

            # Convert BytesIO to base64 string for API Gateway
            excel_bytes = excel_buffer.getvalue()
            excel_base64 = base64.b64encode(excel_bytes).decode('utf-8')

            # Return Excel response
            return {
                'statusCode': 200,
                'headers': {
                    **cors_headers,
                    'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'Content-Disposition': f'attachment; filename="{filename}"',
                    'Cache-Control': 'no-cache'
                },
                'body': excel_base64,
                'isBase64Encoded': True
            }

        except s3_client.exceptions.NoSuchKey:
            logger.error(f"S3 file not found: {results_s3_key}")
            return {
                'statusCode': 404,
                'headers': {**cors_headers, 'Content-Type': 'application/json'},
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
                'headers': {**cors_headers, 'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Invalid data format',
                    'message': 'The results file contains invalid JSON',
                    'job_id': job_id
                }, cls=DecimalEncoder)
            }

        except Exception as e:
            logger.error(f"S3 access error: {e}", exc_info=True)
            return {
                'statusCode': 500,
                'headers': {**cors_headers, 'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Storage access error',
                    'message': 'Failed to retrieve data from storage',
                    'job_id': job_id
                }, cls=DecimalEncoder)
            }

    except Exception as e:
        logger.error(f"Error in handle_excel_export: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {**cors_headers, 'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Internal Server Error',
                'message': 'Failed to generate Excel export',
                'job_id': job_id
            }, cls=DecimalEncoder)
        }