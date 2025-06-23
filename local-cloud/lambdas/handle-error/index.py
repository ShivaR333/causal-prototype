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
    Handle errors in the workflow and notify the user.
    
    Input:
        - sessionId: Session identifier
        - error: Error details
        - errorType: Type of error
        
    Output:
        - Error response sent to user
    """
    print(f"Error Event: {json.dumps(event)}")
    
    try:
        session_id = event.get('sessionId')
        error_message = event.get('error', 'An unexpected error occurred')
        error_type = event.get('errorType', 'UnknownError')
        
        # Get session data
        if session_id:
            session_response = sessions_table.get_item(Key={'sessionId': session_id})
            session_data = session_response.get('Item', {})
            user_id = session_data.get('userId')
        else:
            user_id = None
        
        # Format error response
        error_response = {
            'action': 'error',
            'sessionId': session_id,
            'messageId': f"err-{int(datetime.now().timestamp())}",
            'error': {
                'type': error_type,
                'message': error_message,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Add context if available
        if 'State' in event:
            error_response['error']['state'] = event['State']
        if 'Cause' in event:
            error_response['error']['cause'] = event['Cause']
        
        # Update session with error
        if session_id:
            sessions_table.update_item(
                Key={'sessionId': session_id},
                UpdateExpression='SET #ctx.error = :error, #ctx.errorAt = :timestamp, updatedAt = :timestamp',
                ExpressionAttributeNames={'#ctx': 'context'},
                ExpressionAttributeValues={
                    ':error': error_response['error'],
                    ':timestamp': int(datetime.now().timestamp() * 1000)
                }
            )
        
        # Send error to user connections
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
                            'message': error_response,
                            'timestamp': int(datetime.now().timestamp() * 1000)
                        }
                    )
                except Exception as e:
                    print(f"Failed to send error to connection {connection_id}: {e}")
        
        return {
            'sessionId': session_id,
            'status': 'error_handled',
            'errorType': error_type
        }
        
    except Exception as e:
        print(f"Error handler failed: {str(e)}")
        return {
            'error': 'Error handler failed',
            'details': str(e)
        }