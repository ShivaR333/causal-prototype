import json
import logging
import boto3
import os
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda function to handle simple data queries.
    This function executes basic data queries and returns results.
    """
    logger.info(f"Data query event: {json.dumps(event)}")
    
    try:
        # Extract parameters from the event
        session_id = event.get('sessionId')
        tool_selection = event.get('toolSelection', {})
        parameters = tool_selection.get('parameters', {})
        
        # Mock data query execution for development
        # In production, this would connect to actual data sources
        query_type = parameters.get('query_type', 'basic')
        data_source = parameters.get('data_source', 'default')
        
        logger.info(f"Executing {query_type} query on {data_source} for session {session_id}")
        
        # Mock query result
        mock_result = {
            "query_type": query_type,
            "data_source": data_source,
            "rows_returned": 100,
            "execution_time_ms": 250,
            "columns": ["id", "value", "timestamp"],
            "sample_data": [
                {"id": 1, "value": 42.5, "timestamp": "2025-06-23T08:00:00Z"},
                {"id": 2, "value": 38.2, "timestamp": "2025-06-23T08:01:00Z"},
                {"id": 3, "value": 45.1, "timestamp": "2025-06-23T08:02:00Z"}
            ],
            "metadata": {
                "table_name": "sample_data",
                "query_executed": f"SELECT * FROM {data_source} LIMIT 100"
            }
        }
        
        response = {
            "statusCode": 200,
            "result": mock_result,
            "executionId": context.aws_request_id if hasattr(context, 'aws_request_id') else 'local-dev',
            "timestamp": event.get('timestamp', '2025-06-23T08:00:00Z')
        }
        
        logger.info(f"Data query completed successfully for session {session_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in data query: {str(e)}")
        return {
            "statusCode": 500,
            "error": str(e),
            "errorType": "DataQueryError",
            "executionId": context.aws_request_id if hasattr(context, 'aws_request_id') else 'local-dev'
        }