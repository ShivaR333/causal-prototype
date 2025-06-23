import json
import jwt
import boto3
import os
import logging
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
cognito_client = boto3.client('cognito-idp')
secrets_client = boto3.client('secretsmanager')

# Configuration
USER_POOL_ID = os.environ.get('USER_POOL_ID')
USER_POOL_CLIENT_ID = os.environ.get('USER_POOL_CLIENT_ID')
JWT_SECRET_ARN = os.environ.get('JWT_SECRET_ARN')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    WebSocket Lambda Authorizer for $connect route
    
    This function validates JWT tokens and Cognito authentication
    for WebSocket connections to API Gateway.
    
    Returns an IAM policy allowing or denying the connection.
    """
    try:
        logger.info(f"Authorizer event: {json.dumps(event, default=str)}")
        
        # Extract the token from various possible locations
        token = extract_token(event)
        
        if not token:
            logger.warning("No authorization token found")
            return generate_policy('Deny', event.get('methodArn'), {
                'error': 'Missing authorization token'
            })
        
        # Validate the token
        user_info = validate_token(token)
        
        if not user_info:
            logger.warning("Token validation failed")
            return generate_policy('Deny', event.get('methodArn'), {
                'error': 'Invalid or expired token'
            })
        
        logger.info(f"Authorization successful for user: {user_info.get('user_id')}")
        
        # Return Allow policy with user context
        return generate_policy('Allow', event.get('methodArn'), {
            'userId': user_info.get('user_id'),
            'email': user_info.get('email'),
            'sessionId': user_info.get('session_id'),
            'tokenExpiration': user_info.get('exp')
        })
        
    except Exception as e:
        logger.error(f"Authorizer error: {str(e)}")
        return generate_policy('Deny', event.get('methodArn'), {
            'error': 'Authorization failed',
            'details': str(e)
        })

def extract_token(event: Dict[str, Any]) -> Optional[str]:
    """Extract JWT token from various possible locations in the event."""
    
    # Check query string parameters
    query_params = event.get('queryStringParameters') or {}
    if 'token' in query_params:
        return query_params['token']
    
    # Check headers
    headers = event.get('headers') or {}
    
    # Check Authorization header
    auth_header = headers.get('Authorization') or headers.get('authorization')
    if auth_header:
        if auth_header.startswith('Bearer '):
            return auth_header[7:]  # Remove 'Bearer ' prefix
        return auth_header
    
    # Check custom headers
    if 'x-auth-token' in headers:
        return headers['x-auth-token']
    
    # Check request context (for API Gateway)
    request_context = event.get('requestContext', {})
    authorizer = request_context.get('authorizer', {})
    if 'token' in authorizer:
        return authorizer['token']
    
    return None

def validate_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate JWT token using either Cognito or custom JWT secret.
    
    Returns user information if valid, None if invalid.
    """
    try:
        # First, try to validate as Cognito JWT token
        if USER_POOL_ID and USER_POOL_CLIENT_ID:
            user_info = validate_cognito_token(token)
            if user_info:
                return user_info
        
        # Fallback to custom JWT validation
        if JWT_SECRET_ARN:
            user_info = validate_custom_jwt(token)
            if user_info:
                return user_info
        
        logger.warning("No valid token validation method configured")
        return None
        
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return None

def validate_cognito_token(token: str) -> Optional[Dict[str, Any]]:
    """Validate Cognito JWT token."""
    try:
        # Get Cognito user info
        response = cognito_client.get_user(AccessToken=token)
        
        # Extract user attributes
        user_attributes = {attr['Name']: attr['Value'] for attr in response['UserAttributes']}
        
        return {
            'user_id': response['Username'],
            'email': user_attributes.get('email'),
            'email_verified': user_attributes.get('email_verified') == 'true',
            'session_id': None,  # Will be generated later
            'auth_method': 'cognito',
            'exp': None  # Cognito handles expiration
        }
        
    except cognito_client.exceptions.NotAuthorizedException:
        logger.warning("Cognito token is invalid or expired")
        return None
    except Exception as e:
        logger.error(f"Cognito validation error: {str(e)}")
        return None

def validate_custom_jwt(token: str) -> Optional[Dict[str, Any]]:
    """Validate custom JWT token using secret from AWS Secrets Manager."""
    try:
        # Get JWT secret from Secrets Manager
        secret_response = secrets_client.get_secret_value(SecretId=JWT_SECRET_ARN)
        secret_data = json.loads(secret_response['SecretString'])
        
        jwt_secret = secret_data.get('secret')
        algorithm = secret_data.get('algorithm', 'HS256')
        
        if not jwt_secret:
            logger.error("JWT secret not found in Secrets Manager")
            return None
        
        # Decode and validate JWT
        decoded_token = jwt.decode(
            token,
            jwt_secret,
            algorithms=[algorithm],
            options={'verify_exp': True}
        )
        
        return {
            'user_id': decoded_token.get('sub') or decoded_token.get('user_id'),
            'email': decoded_token.get('email'),
            'session_id': decoded_token.get('session_id'),
            'exp': decoded_token.get('exp'),
            'auth_method': 'custom_jwt'
        }
        
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Custom JWT validation error: {str(e)}")
        return None

def generate_policy(effect: str, resource: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate IAM policy response for API Gateway WebSocket authorizer.
    """
    policy = {
        'principalId': context.get('userId', 'unknown'),
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': resource or '*'
                }
            ]
        },
        'context': context
    }
    
    logger.info(f"Generated policy: {json.dumps(policy, default=str)}")
    return policy