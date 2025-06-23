import json
import boto3
import os
from datetime import datetime

# Initialize AWS services
dynamodb = boto3.resource('dynamodb', endpoint_url=os.environ.get('DYNAMODB_ENDPOINT'))
s3 = boto3.client('s3', endpoint_url=os.environ.get('S3_ENDPOINT'))
sessions_table = dynamodb.Table('causal-analysis-dev-sessions')
jobs_table = dynamodb.Table('causal-analysis-dev-jobs')

def handler(event, context):
    """
    Append tool output to the conversation context for next LLM iteration.
    
    Input:
        - sessionId: Session identifier
        - toolOutput: Results from tool execution
        
    Output:
        - Updated context with tool results
    """
    print(f"Event: {json.dumps(event)}")
    
    try:
        session_id = event['sessionId']
        tool_output = event.get('toolOutput', {})
        
        # Get current session context
        session_response = sessions_table.get_item(Key={'sessionId': session_id})
        session_data = session_response.get('Item', {})
        conversation_context = session_data.get('context', {})
        
        # Initialize history if not present
        if 'history' not in conversation_context:
            conversation_context['history'] = []
        
        # Format tool output for context
        tool_summary = {
            'role': 'tool',
            'timestamp': datetime.now().isoformat(),
            'tool': tool_output.get('tool', 'unknown'),
            'status': tool_output.get('status', 'completed')
        }
        
        # Handle different tool outputs
        if tool_output.get('tool') == 'eda_analysis':
            # EDA produces files in S3
            tool_summary['results'] = {
                'summary': tool_output.get('summary', 'EDA completed'),
                'artifacts': tool_output.get('artifacts', []),
                'insights': tool_output.get('insights', [])
            }
        elif tool_output.get('tool') == 'causal_analysis':
            # Causal analysis produces structured results
            tool_summary['results'] = {
                'effect_size': tool_output.get('effect_size'),
                'confidence_interval': tool_output.get('confidence_interval'),
                'p_value': tool_output.get('p_value'),
                'method': tool_output.get('method'),
                'summary': tool_output.get('summary')
            }
        else:
            # Generic tool output
            tool_summary['results'] = tool_output.get('results', {})
        
        # Append to history
        conversation_context['history'].append(tool_summary)
        
        # Keep only last 10 interactions to manage context size
        if len(conversation_context['history']) > 10:
            conversation_context['history'] = conversation_context['history'][-10:]
        
        # Update session
        sessions_table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression='SET #ctx = :context, updatedAt = :timestamp',
            ExpressionAttributeNames={'#ctx': 'context'},
            ExpressionAttributeValues={
                ':context': conversation_context,
                ':timestamp': int(datetime.now().timestamp() * 1000)
            }
        )
        
        # Update job status if job ID is present
        if 'jobId' in tool_output:
            jobs_table.update_item(
                Key={'jobId': tool_output['jobId']},
                UpdateExpression='SET #s = :status, completedAt = :timestamp',
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={
                    ':status': 'completed',
                    ':timestamp': int(datetime.now().timestamp() * 1000)
                }
            )
        
        # Prepare prompt for next LLM iteration
        next_prompt = f"""Based on the tool execution results:

Tool: {tool_summary['tool']}
Results: {json.dumps(tool_summary['results'], indent=2)}

Please provide the next step or final answer to the user's query."""
        
        return {
            'sessionId': session_id,
            'context': conversation_context,
            'prompt': next_prompt,
            'toolExecuted': tool_summary['tool']
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'error': str(e),
            'sessionId': event.get('sessionId')
        }