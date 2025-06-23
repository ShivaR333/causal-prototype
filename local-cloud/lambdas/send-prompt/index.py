import json
import boto3
import os
from datetime import datetime

# Initialize AWS services
dynamodb = boto3.resource('dynamodb', endpoint_url=os.environ.get('DYNAMODB_ENDPOINT'))
connections_table = dynamodb.Table('causal-analysis-dev-connections')
sessions_table = dynamodb.Table('causal-analysis-dev-sessions')

# For sending messages through API Gateway (in production)
# In local dev, the WebSocket gateway handles this directly
api_gateway_client = boto3.client('apigatewaymanagementapi', 
                                  endpoint_url=os.environ.get('WEBSOCKET_ENDPOINT'))

def handler(event, context):
    """
    Send a prompt to the user and wait for response (using Step Functions callback).
    
    Input:
        - sessionId: Session identifier
        - prompt: Question or clarification needed from user
        - taskToken: Step Functions task token for callback
        
    Output:
        - Waits for user response via callback
    """
    print(f"Event: {json.dumps(event)}")
    
    try:
        session_id = event['sessionId']
        prompt = event['prompt']
        task_token = event['taskToken']
        
        # Get session data to find connection
        session_response = sessions_table.get_item(Key={'sessionId': session_id})
        session_data = session_response.get('Item', {})
        user_id = session_data.get('userId')
        
        if not user_id:
            raise Exception(f"No user ID found for session {session_id}")
        
        # Find active connections for user
        response = connections_table.query(
            IndexName='userId-index',
            KeyConditionExpression='userId = :userId',
            ExpressionAttributeValues={':userId': user_id}
        )
        
        connections = response.get('Items', [])
        if not connections:
            raise Exception(f"No active connections for user {user_id}")
        
        # Store task token for later callback
        sessions_table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression='SET #ctx.pendingTaskToken = :token, #ctx.pendingPrompt = :prompt, updatedAt = :timestamp',
            ExpressionAttributeNames={'#ctx': 'context'},
            ExpressionAttributeValues={
                ':token': task_token,
                ':prompt': prompt,
                ':timestamp': int(datetime.now().timestamp() * 1000)
            }
        )
        
        # Send prompt to all active connections
        message = {
            'action': 'prompt',
            'sessionId': session_id,
            'prompt': prompt,
            'timestamp': datetime.now().isoformat()
        }
        
        for connection in connections:
            connection_id = connection['connectionId']
            try:
                # In production, this would use API Gateway Management API
                # For local dev, we'll store this in DynamoDB for the WebSocket server to pick up
                print(f"Would send to connection {connection_id}: {json.dumps(message)}")
                
                # Store pending message (local dev workaround)
                dynamodb.Table('causal-analysis-dev-pending-messages').put_item(
                    Item={
                        'connectionId': connection_id,
                        'message': message,
                        'timestamp': int(datetime.now().timestamp() * 1000)
                    }
                )
            except Exception as e:
                print(f"Failed to send to connection {connection_id}: {e}")
        
        # This Lambda returns immediately
        # The actual response will come via callback when user responds
        return {
            'status': 'prompt_sent',
            'sessionId': session_id,
            'connections': len(connections)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        # Send error callback to Step Functions
        step_functions = boto3.client('stepfunctions', 
                                      endpoint_url=os.environ.get('STEP_FUNCTIONS_ENDPOINT'))
        
        if 'taskToken' in event:
            try:
                step_functions.send_task_failure(
                    taskToken=event['taskToken'],
                    error='PromptError',
                    cause=str(e)
                )
            except:
                pass
        
        return {
            'error': str(e),
            'sessionId': event.get('sessionId')
        }