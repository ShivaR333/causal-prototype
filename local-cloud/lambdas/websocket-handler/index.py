import json
import boto3
import os
from datetime import datetime
from uuid import uuid4

# Initialize AWS services
dynamodb = boto3.resource('dynamodb')
stepfunctions = boto3.client('stepfunctions')
apigatewaymanagementapi = None  # Will be initialized per request

# Environment variables
CONNECTIONS_TABLE_NAME = os.environ.get('CONNECTIONS_TABLE_NAME', 'causal-analysis-dev-connections')
SESSIONS_TABLE_NAME = os.environ.get('SESSIONS_TABLE_NAME', 'causal-analysis-dev-sessions')
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN')

def lambda_handler(event, context):
    """
    AWS API Gateway WebSocket Lambda handler.
    Handles $connect, $disconnect, and message routing.
    """
    try:
        print(f"WebSocket Event: {json.dumps(event, default=str)}")
        
        route_key = event.get('requestContext', {}).get('routeKey')
        connection_id = event.get('requestContext', {}).get('connectionId')
        domain_name = event.get('requestContext', {}).get('domainName')
        stage = event.get('requestContext', {}).get('stage')
        
        # Initialize API Gateway Management API client
        global apigatewaymanagementapi
        apigatewaymanagementapi = boto3.client(
            'apigatewaymanagementapi',
            endpoint_url=f"https://{domain_name}/{stage}"
        )
        
        if route_key == '$connect':
            return handle_connect(event, context)
        elif route_key == '$disconnect':
            return handle_disconnect(event, context)
        elif route_key == '$default' or route_key == 'sendMessage':
            return handle_message(event, context)
        else:
            print(f"Unknown route: {route_key}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unknown route: {route_key}'})
            }
            
    except Exception as e:
        print(f"Lambda handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

def handle_connect(event, context):
    """
    Handle new WebSocket connections.
    
    Note: Authentication is already handled by the Lambda authorizer
    for the $connect route. User info is available in event context.
    """
    connection_id = event['requestContext']['connectionId']
    
    # Get user info from authorizer context
    authorizer_context = event.get('requestContext', {}).get('authorizer', {})
    user_id = authorizer_context.get('userId', 'unknown')
    email = authorizer_context.get('email')
    session_id = authorizer_context.get('sessionId') or str(uuid4())
    
    print(f"New connection: {connection_id}, User: {user_id}")
    
    try:
        # Store connection in DynamoDB
        connections_table = dynamodb.Table(CONNECTIONS_TABLE_NAME)
        ttl = int(datetime.now().timestamp()) + (24 * 60 * 60)  # 24 hours
        
        connections_table.put_item(
            Item={
                'connectionId': connection_id,
                'userId': user_id,
                'email': email,
                'sessionId': session_id,
                'connectedAt': int(datetime.now().timestamp() * 1000),
                'ttl': ttl,
                'status': 'connected',
                'authenticated': True
            }
        )
        
        # Send welcome message
        send_to_connection(connection_id, {
            'action': 'connection',
            'connectionId': connection_id,
            'sessionId': session_id,
            'userId': user_id,
            'message': 'Connected successfully'
        })
        
        print(f"Connection {connection_id} stored successfully")
        
        return {'statusCode': 200}
        
    except Exception as e:
        print(f"Error handling connection: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to establish connection'})
        }

def handle_disconnect(event, context):
    """Handle WebSocket disconnections."""
    connection_id = event['requestContext']['connectionId']
    
    print(f"Disconnection: {connection_id}")
    
    try:
        # Remove connection from DynamoDB
        connections_table = dynamodb.Table(CONNECTIONS_TABLE_NAME)
        connections_table.delete_item(
            Key={'connectionId': connection_id}
        )
        
        print(f"Connection {connection_id} removed successfully")
        
        return {'statusCode': 200}
        
    except Exception as e:
        print(f"Error handling disconnection: {str(e)}")
        return {'statusCode': 200}  # Return success even if cleanup fails

def handle_message(event, context):
    """Handle incoming WebSocket messages."""
    connection_id = event['requestContext']['connectionId']
    
    try:
        # Parse message body
        body = json.loads(event.get('body', '{}'))
        action = body.get('action')
        
        print(f"Message from {connection_id}: {action}")
        
        # Get connection info
        connections_table = dynamodb.Table(CONNECTIONS_TABLE_NAME)
        connection_response = connections_table.get_item(
            Key={'connectionId': connection_id}
        )
        
        if 'Item' not in connection_response:
            send_to_connection(connection_id, {
                'action': 'error',
                'error': 'Connection not found'
            })
            return {'statusCode': 404}
        
        connection_info = connection_response['Item']
        
        # Route message based on action
        if action == 'query':
            return handle_query(connection_id, connection_info, body)
        elif action == 'response':
            return handle_user_response(connection_id, connection_info, body)
        elif action == 'ping':
            send_to_connection(connection_id, {
                'action': 'pong',
                'timestamp': int(datetime.now().timestamp() * 1000)
            })
            return {'statusCode': 200}
        else:
            send_to_connection(connection_id, {
                'action': 'error',
                'error': f'Unknown action: {action}'
            })
            return {'statusCode': 400}
            
    except json.JSONDecodeError:
        send_to_connection(connection_id, {
            'action': 'error',
            'error': 'Invalid JSON format'
        })
        return {'statusCode': 400}
    except Exception as e:
        print(f"Error handling message: {str(e)}")
        send_to_connection(connection_id, {
            'action': 'error',
            'error': 'Internal server error'
        })
        return {'statusCode': 500}

def handle_query(connection_id, connection_info, body):
    """Handle causal analysis queries."""
    try:
        user_id = connection_info['userId']
        session_id = connection_info.get('sessionId', str(uuid4()))
        
        query_payload = body.get('payload')
        message_id = body.get('messageId', str(uuid4()))
        
        print(f"Processing query for user {user_id}, session {session_id}")
        
        # Acknowledge query receipt
        send_to_connection(connection_id, {
            'action': 'query_received',
            'messageId': message_id,
            'sessionId': session_id,
            'status': 'processing'
        })
        
        # Start Step Functions execution
        execution_name = f"exec-{session_id}-{int(datetime.now().timestamp())}"
        
        step_input = {
            'sessionId': session_id,
            'userId': user_id,
            'connectionId': connection_id,
            'query': query_payload,
            'messageId': message_id,
            'networkConfig': {
                'subnets': ['subnet-local'],  # Will be replaced with actual VPC subnets
                'securityGroups': ['sg-local']  # Will be replaced with actual security groups
            }
        }
        
        if not STATE_MACHINE_ARN:
            raise ValueError("STATE_MACHINE_ARN environment variable not set")
        
        response = stepfunctions.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=execution_name,
            input=json.dumps(step_input)
        )
        
        print(f"Started execution: {response['executionArn']}")
        
        # Store execution info in session
        sessions_table = dynamodb.Table(SESSIONS_TABLE_NAME)
        sessions_table.put_item(
            Item={
                'sessionId': session_id,
                'userId': user_id,
                'connectionId': connection_id,
                'executionArn': response['executionArn'],
                'messageId': message_id,
                'createdAt': int(datetime.now().timestamp() * 1000),
                'status': 'processing'
            }
        )
        
        return {'statusCode': 200}
        
    except Exception as e:
        print(f"Error handling query: {str(e)}")
        send_to_connection(connection_id, {
            'action': 'error',
            'messageId': body.get('messageId'),
            'error': f'Failed to process query: {str(e)}'
        })
        return {'statusCode': 500}

def handle_user_response(connection_id, connection_info, body):
    """Handle user responses to prompts."""
    try:
        session_id = body.get('sessionId')
        response_text = body.get('response')
        
        if not session_id:
            send_to_connection(connection_id, {
                'action': 'error',
                'error': 'Session ID required'
            })
            return {'statusCode': 400}
        
        # Get session info
        sessions_table = dynamodb.Table(SESSIONS_TABLE_NAME)
        session_response = sessions_table.get_item(
            Key={'sessionId': session_id}
        )
        
        if 'Item' not in session_response:
            send_to_connection(connection_id, {
                'action': 'error',
                'error': 'Session not found'
            })
            return {'statusCode': 404}
        
        session_info = session_response['Item']
        task_token = session_info.get('pendingTaskToken')
        
        if not task_token:
            send_to_connection(connection_id, {
                'action': 'error',
                'error': 'No pending prompt'
            })
            return {'statusCode': 400}
        
        # Send task success to Step Functions
        stepfunctions.send_task_success(
            taskToken=task_token,
            output=json.dumps({
                'userResponse': response_text,
                'sessionId': session_id,
                'connectionId': connection_id
            })
        )
        
        # Clear pending token from session
        sessions_table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression='REMOVE pendingTaskToken, pendingPrompt',
            ReturnValues='UPDATED_NEW'
        )
        
        send_to_connection(connection_id, {
            'action': 'response_received',
            'sessionId': session_id
        })
        
        return {'statusCode': 200}
        
    except Exception as e:
        print(f"Error handling user response: {str(e)}")
        send_to_connection(connection_id, {
            'action': 'error',
            'error': f'Failed to process response: {str(e)}'
        })
        return {'statusCode': 500}

def send_to_connection(connection_id, message):
    """Send message to WebSocket connection via API Gateway Management API."""
    try:
        apigatewaymanagementapi.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps(message).encode('utf-8')
        )
        print(f"Message sent to {connection_id}: {message.get('action')}")
    except apigatewaymanagementapi.exceptions.GoneException:
        print(f"Connection {connection_id} is gone")
        # Connection is stale, remove from database
        try:
            connections_table = dynamodb.Table(CONNECTIONS_TABLE_NAME)
            connections_table.delete_item(Key={'connectionId': connection_id})
        except Exception as e:
            print(f"Error removing stale connection: {str(e)}")
    except Exception as e:
        print(f"Error sending message to {connection_id}: {str(e)}")
        raise