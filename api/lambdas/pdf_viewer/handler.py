#!/usr/bin/env python3
"""
PDF Viewer Lambda handler for retrieving and unlocking PDFs from S3
"""

import json
import logging
import os
import boto3
from decimal import Decimal
import base64
import pypdf
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
    AWS Lambda entry point for PDF viewer API

    Args:
        event: API Gateway event data
        context: Lambda context object

    Returns:
        API Gateway response with PDF content
    """
    try:
        # Extract request details
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        path_parameters = event.get('pathParameters') or {}

        # Extract job_id from path parameters
        job_id = path_parameters.get('job_id')

        logger.info(f"PDF Viewer Request: {http_method} {path}, job_id: {job_id}")

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

        # Validate job_id
        if not job_id:
            return {
                'statusCode': 400,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Bad Request',
                    'message': 'job_id is required'
                })
            }

        return handle_get_pdf(job_id, cors_headers)

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

def handle_get_pdf(job_id, cors_headers):
    """Handle PDF retrieval and unlocking"""
    try:
        table = dynamodb.Table(JOBS_TABLE_NAME)

        # Get job details from DynamoDB
        try:
            response = table.get_item(Key={'job_id': job_id})
            if 'Item' not in response:
                return {
                    'statusCode': 404,
                    'headers': cors_headers,
                    'body': json.dumps({
                        'error': 'Not Found',
                        'message': f'Job {job_id} not found'
                    })
                }

            job_data = response['Item']
            s3_key = job_data.get('s3_key')
            password = job_data.get('password')

            if not s3_key:
                return {
                    'statusCode': 400,
                    'headers': cors_headers,
                    'body': json.dumps({
                        'error': 'Bad Request',
                        'message': 'No PDF file associated with this job'
                    })
                }

        except ClientError as e:
            logger.error(f"Error getting job from DynamoDB: {e}")
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Internal Server Error',
                    'message': 'Failed to retrieve job data'
                })
            }

        # Download PDF from S3
        try:
            response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
            pdf_content = response['Body'].read()

        except ClientError as e:
            logger.error(f"Error downloading PDF from S3: {e}")
            return {
                'statusCode': 500,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Internal Server Error',
                    'message': 'Failed to retrieve PDF from storage'
                })
            }

        # If PDF is password protected, unlock it
        if password:
            try:
                # Create a PDF reader
                pdf_reader = pypdf.PdfReader(io.BytesIO(pdf_content))

                # Check if PDF is encrypted
                if pdf_reader.is_encrypted:
                    # Try to decrypt with stored password
                    result = pdf_reader.decrypt(password)
                    if not result:
                        # Try trimmed password
                        trimmed_password = password.strip()
                        if trimmed_password != password:
                            result = pdf_reader.decrypt(trimmed_password)

                        if not result:
                            return {
                                'statusCode': 401,
                                'headers': cors_headers,
                                'body': json.dumps({
                                    'error': 'Unauthorized',
                                    'message': 'Failed to unlock PDF with stored password'
                                })
                            }

                    # Create a new PDF writer with unlocked content
                    pdf_writer = pypdf.PdfWriter()
                    for page_num in range(len(pdf_reader.pages)):
                        pdf_writer.add_page(pdf_reader.pages[page_num])

                    # Write unlocked PDF to bytes
                    unlocked_pdf_io = io.BytesIO()
                    pdf_writer.write(unlocked_pdf_io)
                    pdf_content = unlocked_pdf_io.getvalue()

            except Exception as e:
                logger.error(f"Error unlocking PDF: {e}")
                return {
                    'statusCode': 500,
                    'headers': cors_headers,
                    'body': json.dumps({
                        'error': 'Internal Server Error',
                        'message': 'Failed to unlock PDF'
                    })
                }

        # Return PDF as base64 encoded content
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')

        return {
            'statusCode': 200,
            'headers': cors_headers,
            'body': json.dumps({
                'success': True,
                'job_id': job_id,
                'pdf_content': pdf_base64,
                'content_type': 'application/pdf',
                'filename': job_data.get('original_filename', 'document.pdf')
            }, cls=DecimalEncoder)
        }

    except Exception as e:
        logger.error(f"Error in handle_get_pdf: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': cors_headers,
            'body': json.dumps({
                'error': 'Internal Server Error',
                'message': 'Failed to retrieve PDF'
            })
        }