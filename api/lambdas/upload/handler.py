#!/usr/bin/env python3
"""
AWS Lambda handler for PDF Upload functionality
Handles file upload and storage to S3
"""

import json
import base64
import logging
from datetime import datetime, timezone, timedelta
import uuid
import os
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration - fail fast if environment variables are missing
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
JOBS_TABLE_NAME = os.getenv('JOBS_TABLE_NAME')
PROCESSING_QUEUE_URL = os.getenv('PROCESSING_QUEUE_URL')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')  # AWS region can have a reasonable default

# Validate required environment variables
if not S3_BUCKET_NAME:
    raise ValueError("S3_BUCKET_NAME environment variable is required")
if not JOBS_TABLE_NAME:
    raise ValueError("JOBS_TABLE_NAME environment variable is required")
if not PROCESSING_QUEUE_URL:
    raise ValueError("PROCESSING_QUEUE_URL environment variable is required")

# Initialize AWS clients
s3_client = boto3.client('s3', region_name=AWS_REGION)
sqs_client = boto3.client('sqs', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)

def handler(event, context):
    """
    AWS Lambda entry point for PDF upload

    Args:
        event: API Gateway event data
        context: Lambda context object

    Returns:
        API Gateway response
    """
    try:
        # Extract request details
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '/upload')
        headers = event.get('headers', {})

        logger.info(f"Upload request: {http_method} {path}")

        # CORS headers for all responses
        cors_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, X-API-Key, Authorization',
            'Content-Type': 'application/json'
        }


        # Only handle POST requests
        if http_method != 'POST':
            return {
                'statusCode': 405,
                'headers': cors_headers,
                'body': json.dumps({
                    'error': 'Method Not Allowed',
                    'message': 'Only POST method is supported'
                })
            }

        return handle_upload(event)

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


def parse_multipart_data(body, content_type):
    """Parse multipart form data from API Gateway event"""
    try:
        # Extract boundary from content-type header
        boundary = None
        if 'boundary=' in content_type:
            boundary = content_type.split('boundary=')[1].strip()

        if not boundary:
            raise ValueError("No boundary found in content-type")

        # Parse the multipart data
        file_data = None
        filename = None
        password = None

        # Split by boundary
        parts = body.split(f'--{boundary}')

        for part in parts:
            if not part.strip() or part.strip() == '--':
                continue

            # Split headers from body
            if '\r\n\r\n' in part:
                headers_section, content = part.split('\r\n\r\n', 1)
            elif '\n\n' in part:
                headers_section, content = part.split('\n\n', 1)
            else:
                continue

            # Parse headers
            headers = {}
            for line in headers_section.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()

            content_disposition = headers.get('content-disposition', '')

            # Check if this is a file upload
            if 'filename=' in content_disposition and 'name="file"' in content_disposition:
                # Extract filename
                filename_match = content_disposition.split('filename="')[1].split('"')[0]
                filename = filename_match
                # Remove trailing boundary markers and whitespace
                content = content.rstrip().rstrip(f'--{boundary}').rstrip('--').rstrip()
                file_data = content.encode('latin-1')  # Preserve binary data

            # Check if this is the password field
            elif 'name="password"' in content_disposition:
                # Extract password value more carefully to avoid truncation
                logger.info(f"Boundary used: '{boundary}'")

                # Remove boundary markers more precisely to avoid truncating password
                password = content.strip()
                if password.endswith(f'--{boundary}'):
                    password = password[:-len(f'--{boundary}')]
                elif password.endswith('--'):
                    password = password[:-2]
                password = password.strip()

                logger.info(f"Password field found in upload. Length: {len(password) if password else 0}")

        return file_data, filename, password

    except Exception as e:
        logger.error(f"Error parsing multipart data: {e}")
        raise ValueError(f"Failed to parse multipart data: {e}")

def upload_to_s3(file_data, s3_key, content_type, metadata=None):
    """Upload file to S3 bucket"""
    try:
        upload_args = {
            'Bucket': S3_BUCKET_NAME,
            'Key': s3_key,
            'Body': file_data,
            'ContentType': content_type
        }

        if metadata:
            upload_args['Metadata'] = metadata

        s3_client.put_object(**upload_args)
        return True
    except Exception as e:
        logger.error(f"S3 upload error: {e}")
        raise

def save_to_dynamodb(job_data):
    """Save job metadata to DynamoDB"""
    try:
        table = dynamodb.Table(JOBS_TABLE_NAME)
        table.put_item(Item=job_data)
        return True
    except Exception as e:
        logger.error(f"DynamoDB save error: {e}")
        raise

def trigger_processing(job_id, s3_key, user_id, filename):
    """Send SQS message to trigger PDF processing"""
    try:
        if not PROCESSING_QUEUE_URL:
            logger.warning("PROCESSING_QUEUE_URL not configured, skipping automatic processing")
            return False

        message_body = {
            'job_id': job_id,
            's3_key': s3_key,
            'user_id': user_id,
            'password': None,
            'original_filename': filename
        }

        response = sqs_client.send_message(
            QueueUrl=PROCESSING_QUEUE_URL,
            MessageBody=json.dumps(message_body),
            MessageAttributes={
                'job_id': {
                    'StringValue': job_id,
                    'DataType': 'String'
                },
                'user_id': {
                    'StringValue': user_id,
                    'DataType': 'String'
                }
            }
        )

        logger.info(f"SQS message sent successfully", extra={
            'job_id': job_id,
            'message_id': response['MessageId'],
            'filename': filename
        })

        return True

    except Exception as e:
        logger.error(f"Failed to send SQS message for processing", extra={
            'job_id': job_id,
            'error': str(e)
        }, exc_info=True)
        # Don't fail the upload if SQS fails - processing can be triggered manually later
        return False

def handle_upload(event):
    """Handle POST /upload endpoint"""
    try:
        # Get headers (case-insensitive)
        headers = event.get('headers', {})
        content_type = None
        for key, value in headers.items():
            if key.lower() == 'content-type':
                content_type = value
                break

        if not content_type or 'multipart/form-data' not in content_type:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Bad Request',
                    'message': 'Content-Type must be multipart/form-data'
                })
            }

        # Get body (handle base64 encoding if needed)
        body = event.get('body', '')
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(body).decode('latin-1')

        # Parse multipart data
        file_data, filename, password = parse_multipart_data(body, content_type)

        if not file_data or not filename:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Bad Request',
                    'message': 'No file uploaded'
                })
            }

        # Generate a default user ID for now
        default_user_id = "default-user"

        # Validate file type
        if not filename.lower().endswith('.pdf'):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Bad Request',
                    'message': 'Only PDF files are supported'
                })
            }

        # Check file size (25MB limit)
        file_size = len(file_data)
        file_size_mb = file_size / (1024 * 1024)
        if file_size_mb > 25:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Bad Request',
                    'message': f'File too large: {file_size_mb:.1f}MB (max 25MB)'
                })
            }

        # Generate unique job ID for tracking this upload throughout the system
        job_id = str(uuid.uuid4())
        upload_timestamp = datetime.now(timezone.utc)

        # Create organized S3 key with hierarchical structure for efficient storage and retrieval
        # Format: uploads/YYYY/MM/DD/uuid_originalfilename.pdf
        # Example: uploads/2025/09/15/abc123-def456-ghi789_bank-statement.pdf
        # Benefits:
        # - Date-based partitioning enables efficient S3 lifecycle policies
        # - UUID prefix prevents filename conflicts and ensures uniqueness
        # - Original filename preserved for user reference and download
        # - Hierarchical structure supports efficient querying and organization
        s3_key = f"uploads/{upload_timestamp.strftime('%Y/%m/%d')}/{job_id}_{filename}"

        # Upload to S3
        upload_to_s3(
            file_data=file_data,
            s3_key=s3_key,
            content_type='application/pdf',
            metadata={
                'original_filename': filename,
                'uploaded_by': default_user_id,
                'upload_timestamp': upload_timestamp.isoformat(),
                'job_id': job_id
            }
        )

        # Store password if provided
        plain_password = None
        if password and password.strip():
            plain_password = password.strip()
            logger.info(f"Password will be stored for job: {job_id} (length: {len(plain_password)})")

        # Save to DynamoDB
        ttl = int((upload_timestamp + timedelta(days=60)).timestamp())  # 60 days TTL
        job_data = {
            'job_id': job_id,
            'user_id': default_user_id,
            'created_at': upload_timestamp.isoformat(),
            'status': 'uploaded',
            'job_type': 'file_upload',
            'original_filename': filename,
            's3_key': s3_key,
            'file_size_bytes': file_size,
            'file_size_mb': Decimal(str(round(file_size_mb, 2))),
            'content_type': 'application/pdf',
            'upload_timestamp': upload_timestamp.isoformat(),
            'ttl': ttl,
            'metadata': {
                'upload_source': 'aws_api_gateway',
                'api_version': '2.0.0',
                'has_password': plain_password is not None
            }
        }

        # Add password if provided
        if plain_password:
            job_data['password'] = plain_password

        save_to_dynamodb(job_data)

        # Automatically trigger processing
        processing_triggered = trigger_processing(job_id, s3_key, default_user_id, filename)

        # Update status to processing if SQS message sent successfully
        if processing_triggered:
            try:
                table = dynamodb.Table(JOBS_TABLE_NAME)
                table.update_item(
                    Key={'job_id': job_id},
                    UpdateExpression='SET #status = :status, processing_started_at = :timestamp',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'processing',
                        ':timestamp': datetime.now(timezone.utc).isoformat()
                    }
                )
                logger.info(f"Updated job status to processing: {job_id}")
            except Exception as e:
                logger.error(f"Failed to update job status to processing: {e}")

        logger.info(f"File upload successful: {filename} -> {s3_key}")

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'success',
                'message': f"File '{filename}' uploaded successfully",
                'job_id': job_id,
                'filename': filename,
                'file_size_mb': round(file_size_mb, 2),
                's3_key': s3_key,
                'upload_timestamp': upload_timestamp.isoformat(),
                'file_metadata': {
                    'job_id': job_id,
                    'original_filename': filename,
                    'status': 'uploaded',
                    'file_size_bytes': file_size,
                    'file_size_mb': round(file_size_mb, 2)
                }
            })
        }

    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Upload Failed',
                'message': str(e)
            })
        }