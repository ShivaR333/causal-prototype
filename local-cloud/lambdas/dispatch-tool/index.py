import json
import boto3
import os
from datetime import datetime

# Initialize AWS services
s3 = boto3.client('s3', endpoint_url=os.environ.get('S3_ENDPOINT'))
dynamodb = boto3.resource('dynamodb', endpoint_url=os.environ.get('DYNAMODB_ENDPOINT'))
jobs_table = dynamodb.Table('causal-analysis-dev-jobs')

def handler(event, context):
    """
    Dispatch the appropriate tool based on LLM response.
    
    Input:
        - sessionId: Session identifier
        - tool: Tool name to execute
        - parameters: Tool parameters
        
    Output:
        - tool: Selected tool for Step Functions routing
        - parameters: Prepared parameters for tool execution
    """
    print(f"Event: {json.dumps(event)}")
    
    try:
        session_id = event['sessionId']
        tool_name = event.get('tool', '')
        parameters = event.get('parameters', {})
        
        # Create job record
        job_id = f"{session_id}-{int(datetime.now().timestamp())}"
        job_record = {
            'jobId': job_id,
            'sessionId': session_id,
            'tool': tool_name,
            'parameters': parameters,
            'status': 'dispatched',
            'createdAt': int(datetime.now().timestamp() * 1000),
            'ttl': int(datetime.now().timestamp()) + (7 * 24 * 60 * 60)  # 7 days TTL
        }
        
        jobs_table.put_item(Item=job_record)
        
        # Prepare tool execution parameters
        if tool_name == 'eda_analysis':
            # Prepare S3 paths
            input_path = f"s3://causal-analysis-dev-rawdata/{parameters.get('data_file', 'sample_data/eCommerce_sales.csv')}"
            output_path = f"s3://causal-analysis-dev-artifacts/eda/{job_id}/"
            
            return {
                'tool': 'eda_analysis',
                'parameters': {
                    'inputPath': input_path,
                    'outputPath': output_path,
                    'analysisType': parameters.get('analysis_type', 'comprehensive'),
                    'jobId': job_id
                }
            }
            
        elif tool_name == 'causal_analysis':
            # Prepare causal analysis parameters
            return {
                'tool': 'causal_analysis',
                'parameters': {
                    'jobId': job_id,
                    'treatment': parameters.get('treatment'),
                    'outcome': parameters.get('outcome'),
                    'confounders': parameters.get('confounders', []),
                    'method': parameters.get('method', 'backdoor'),
                    'dataFile': parameters.get('data_file', 'sample_data/eCommerce_sales.csv'),
                    'dagFile': parameters.get('dag_file', 'sample_dag.json')
                }
            }
            
        elif tool_name == 'data_query':
            # Simple data query tool
            return {
                'tool': 'data_query',
                'parameters': {
                    'query': parameters.get('query'),
                    'dataFile': parameters.get('data_file')
                }
            }
            
        else:
            # Unknown tool
            return {
                'tool': 'unknown',
                'error': f"Unknown tool: {tool_name}"
            }
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'tool': 'error',
            'error': str(e)
        }