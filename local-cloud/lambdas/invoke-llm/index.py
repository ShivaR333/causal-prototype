import json
import boto3
import os
import openai
from datetime import datetime

# Initialize AWS services
secrets_client = boto3.client('secretsmanager', endpoint_url=os.environ.get('SECRETS_ENDPOINT'))
dynamodb = boto3.resource('dynamodb', endpoint_url=os.environ.get('DYNAMODB_ENDPOINT'))
sessions_table = dynamodb.Table('causal-analysis-dev-sessions')

def get_openai_config():
    """Retrieve OpenAI configuration from Secrets Manager."""
    try:
        # Try to get from new secrets structure first
        secret_name = os.environ.get('OPENAI_SECRET_NAME', 'causal-analysis-dev-openai-api-key')
        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response['SecretString'])
        return {
            'api_key': secret.get('api_key'),
            'model': secret.get('model', 'gpt-3.5-turbo')
        }
    except Exception as e:
        print(f"Error getting OpenAI config from Secrets Manager: {e}")
        # Fallback to environment variables for local development
        return {
            'api_key': os.environ.get('OPENAI_API_KEY', 'test-key'),
            'model': os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
        }

def handler(event, context):
    """
    Invoke LLM to process the query and determine next action.
    
    Input:
        - sessionId: Session identifier
        - prompt: Prepared prompt for LLM
        - context: Current conversation context
        
    Output:
        - type: "tool_call", "need_input", or "final_answer"
        - content: Response or tool parameters
    """
    print(f"Event: {json.dumps(event)}")
    
    try:
        session_id = event['sessionId']
        prompt = event.get('prompt', '')
        conversation_context = event.get('context', {})
        
        # Get OpenAI configuration
        openai_config = get_openai_config()
        api_key = openai_config['api_key']
        model = openai_config['model']
        
        # For local testing, mock LLM response
        if api_key == 'test-key' or os.environ.get('MOCK_LLM', 'false').lower() == 'true':
            # Mock response based on query content
            if 'effect' in prompt.lower() or 'causal' in prompt.lower():
                response = {
                    'type': 'tool_call',
                    'tool': 'causal_analysis',
                    'parameters': {
                        'treatment': 'discount',
                        'outcome': 'sales',
                        'confounders': ['customer_segment', 'season'],
                        'method': 'linear_regression'
                    }
                }
            elif 'eda' in prompt.lower() or 'explore' in prompt.lower():
                response = {
                    'type': 'tool_call',
                    'tool': 'eda_analysis',
                    'parameters': {
                        'data_file': 'sample_data/eCommerce_sales.csv',
                        'analysis_type': 'comprehensive'
                    }
                }
            else:
                response = {
                    'type': 'final_answer',
                    'content': 'I can help you with causal analysis and exploratory data analysis. What would you like to analyze?'
                }
        else:
            # Real LLM call
            openai.api_key = api_key
            
            messages = [
                {
                    "role": "system",
                    "content": "You are a causal analysis agent. Analyze queries and respond with structured JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # Add conversation history if available
            if 'history' in conversation_context:
                messages = conversation_context['history'] + messages
            
            completion = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            response = json.loads(completion.choices[0].message.content)
        
        # Update session context
        sessions_table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression='SET #ctx.lastLLMResponse = :response, updatedAt = :timestamp',
            ExpressionAttributeNames={'#ctx': 'context'},
            ExpressionAttributeValues={
                ':response': response,
                ':timestamp': int(datetime.now().timestamp() * 1000)
            }
        )
        
        # Add session ID to response
        response['sessionId'] = session_id
        
        return response
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'type': 'error',
            'error': str(e),
            'sessionId': event.get('sessionId')
        }