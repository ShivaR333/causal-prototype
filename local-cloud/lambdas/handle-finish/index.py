import json
import boto3
import os
from datetime import datetime

# Initialize AWS services
dynamodb = boto3.resource('dynamodb', endpoint_url=os.environ.get('DYNAMODB_ENDPOINT'))
s3 = boto3.client('s3', endpoint_url=os.environ.get('S3_ENDPOINT'))
sessions_table = dynamodb.Table('causal-analysis-dev-sessions')
connections_table = dynamodb.Table('causal-analysis-dev-connections')

def handler(event, context):
    """
    Handle the final response and send it back to the user.
    
    Input:
        - sessionId: Session identifier
        - llmResponse: Final response from LLM
        
    Output:
        - Final formatted response sent to user
    """
    print(f"Event: {json.dumps(event)}")
    
    try:
        session_id = event['sessionId']
        llm_response = event.get('llmResponse', {})
        
        # Get session data
        session_response = sessions_table.get_item(Key={'sessionId': session_id})
        session_data = session_response.get('Item', {})
        user_id = session_data.get('userId')
        conversation_context = session_data.get('context', {})
        
        # Format final response
        final_response = {
            'action': 'response',
            'sessionId': session_id,
            'messageId': f"msg-{int(datetime.now().timestamp())}",
            'payload': {
                'type': 'final_answer',
                'content': llm_response.get('content', 'Analysis completed'),
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'executionTime': conversation_context.get('executionTime'),
                    'toolsUsed': [h['tool'] for h in conversation_context.get('history', []) if h.get('role') == 'tool']
                }
            }
        }
        
        # Add any artifacts or results
        if 'artifacts' in conversation_context:
            final_response['payload']['artifacts'] = conversation_context['artifacts']
        
        # Update session with completion
        sessions_table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression='SET #ctx.completed = :true, #ctx.completedAt = :timestamp, updatedAt = :timestamp',
            ExpressionAttributeNames={'#ctx': 'context'},
            ExpressionAttributeValues={
                ':true': True,
                ':timestamp': int(datetime.now().timestamp() * 1000)
            }
        )
        
        # Find user connections
        response = connections_table.query(
            IndexName='userId-index',
            KeyConditionExpression='userId = :userId',
            ExpressionAttributeValues={':userId': user_id}
        )
        
        connections = response.get('Items', [])
        
        # Send final response to all connections
        for connection in connections:
            connection_id = connection['connectionId']
            try:
                # In local dev, store for WebSocket server to pick up
                dynamodb.Table('causal-analysis-dev-pending-messages').put_item(
                    Item={
                        'connectionId': connection_id,
                        'message': final_response,
                        'timestamp': int(datetime.now().timestamp() * 1000)
                    }
                )
            except Exception as e:
                print(f"Failed to send to connection {connection_id}: {e}")
        
        # Generate summary for logging
        summary = {
            'sessionId': session_id,
            'status': 'completed',
            'toolsUsed': final_response['payload']['metadata']['toolsUsed'],
            'responseLength': len(final_response['payload']['content']),
            'connectionsSent': len(connections)
        }
        
        print(f"Execution completed: {json.dumps(summary)}")
        
        return summary
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'error': str(e),
            'sessionId': event.get('sessionId'),
            'status': 'failed'
        }