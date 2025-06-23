import json
import boto3
import os
from datetime import datetime

# Initialize AWS services
dynamodb = boto3.resource('dynamodb', endpoint_url=os.environ.get('DYNAMODB_ENDPOINT'))
sessions_table = dynamodb.Table('causal-analysis-dev-sessions')
connections_table = dynamodb.Table('causal-analysis-dev-connections')

def handler(event, context):
    """
    Handle timeout scenarios (e.g., user didn't respond to prompt).
    
    Input:
        - sessionId: Session identifier
        - timeoutType: Type of timeout
        
    Output:
        - Timeout notification sent to user
    """
    print(f"Timeout Event: {json.dumps(event)}")
    
    try:
        session_id = event.get('sessionId')
        timeout_type = event.get('timeoutType', 'user_response')
        
        # Get session data
        session_response = sessions_table.get_item(Key={'sessionId': session_id})
        session_data = session_response.get('Item', {})
        user_id = session_data.get('userId')
        conversation_context = session_data.get('context', {})
        
        # Format timeout response
        timeout_response = {
            'action': 'timeout',
            'sessionId': session_id,
            'messageId': f"timeout-{int(datetime.now().timestamp())}",
            'timeout': {
                'type': timeout_type,
                'message': 'The operation timed out. Please try again.',
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Add context-specific timeout messages
        if timeout_type == 'user_response' and 'pendingPrompt' in conversation_context:
            timeout_response['timeout']['message'] = f"Timed out waiting for response to: {conversation_context['pendingPrompt']}"
        
        # Clear pending task token
        sessions_table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression='REMOVE #ctx.pendingTaskToken, #ctx.pendingPrompt SET #ctx.timedOut = :true, updatedAt = :timestamp',
            ExpressionAttributeNames={'#ctx': 'context'},
            ExpressionAttributeValues={
                ':true': True,
                ':timestamp': int(datetime.now().timestamp() * 1000)
            }
        )
        
        # Send timeout notification
        if user_id:
            response = connections_table.query(
                IndexName='userId-index',
                KeyConditionExpression='userId = :userId',
                ExpressionAttributeValues={':userId': user_id}
            )
            
            connections = response.get('Items', [])
            
            for connection in connections:
                connection_id = connection['connectionId']
                try:
                    # Store for WebSocket server
                    dynamodb.Table('causal-analysis-dev-pending-messages').put_item(
                        Item={
                            'connectionId': connection_id,
                            'message': timeout_response,
                            'timestamp': int(datetime.now().timestamp() * 1000)
                        }
                    )
                except Exception as e:
                    print(f"Failed to send timeout to connection {connection_id}: {e}")
        
        return {
            'sessionId': session_id,
            'status': 'timeout_handled',
            'timeoutType': timeout_type
        }
        
    except Exception as e:
        print(f"Timeout handler failed: {str(e)}")
        return {
            'error': 'Timeout handler failed',
            'details': str(e)
        }