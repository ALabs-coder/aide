#!/usr/bin/env python3
"""
AWS Lambda handler for the PDF Extractor API
"""

import json
import base64
from mangum import Mangum
from main import app
from logging_config import setup_logging
import logging

# Setup logging for Lambda
setup_logging()
logger = logging.getLogger(__name__)

# Create the Lambda handler using Mangum
handler = Mangum(app, lifespan="off")

def lambda_handler(event, context):
    """
    AWS Lambda entry point
    
    Args:
        event: Lambda event data
        context: Lambda context object
        
    Returns:
        API Gateway response
    """
    try:
        # Log the incoming event (excluding sensitive data)
        logger.info("Lambda invocation started", extra={
            "request_id": context.aws_request_id,
            "function_name": context.function_name,
            "memory_limit": context.memory_limit_in_mb,
            "remaining_time": context.get_remaining_time_in_millis(),
            "http_method": event.get("httpMethod"),
            "path": event.get("path"),
            "headers": {k: v for k, v in event.get("headers", {}).items() 
                      if k.lower() not in ["authorization", "x-api-key"]}
        })
        
        # Handle the request using Mangum
        response = handler(event, context)
        
        logger.info("Lambda invocation completed successfully", extra={
            "request_id": context.aws_request_id,
            "status_code": response.get("statusCode"),
            "response_size": len(json.dumps(response)) if response else 0
        })
        
        return response
        
    except Exception as e:
        logger.error("Lambda invocation failed", extra={
            "request_id": context.aws_request_id,
            "error": str(e),
            "error_type": type(e).__name__
        }, exc_info=True)
        
        # Return a generic error response
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "X-Request-ID": context.aws_request_id
            },
            "body": json.dumps({
                "error": "Internal server error",
                "request_id": context.aws_request_id
            })
        }