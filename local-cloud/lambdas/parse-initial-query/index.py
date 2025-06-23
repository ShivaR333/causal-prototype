import json
import boto3
import os
from datetime import datetime

# Initialize AWS services
dynamodb = boto3.resource('dynamodb', endpoint_url=os.environ.get('DYNAMODB_ENDPOINT'))
sessions_table = dynamodb.Table('causal-analysis-dev-sessions')

def handler(event, context):
    """
    Parse the initial user query and prepare it for LLM processing.
    
    Input:
        - sessionId: Session identifier
        - query: User's natural language or structured query
        
    Output:
        - Parsed query with context and metadata
    """
    print(f"Event: {json.dumps(event)}")
    
    try:
        session_id = event['sessionId']
        query = event['query']
        
        # Get session context
        session_response = sessions_table.get_item(Key={'sessionId': session_id})
        session_data = session_response.get('Item', {})
        context = session_data.get('context', {})
        
        # Parse query type
        query_type = query.get('type', 'natural_language')
        content = query.get('content', '')
        
        # Build prompt for LLM
        if query_type == 'natural_language':
            system_prompt = """You are a causal analysis agent. Analyze the user's query and determine:
1. Whether it requires causal analysis, EDA, or just information
2. What data files are needed
3. What specific analysis parameters are required

Previous context:
{context}

User query: {query}

Respond with a JSON object containing:
- intent: "causal_analysis", "eda", "information", or "clarification_needed"
- parameters: relevant parameters for the analysis
- data_requirements: what data is needed
- clarification: any questions if the query is unclear
"""
            
            prompt = system_prompt.format(
                context=json.dumps(context),
                query=content
            )
        else:
            # Structured query - validate and format
            prompt = json.dumps({
                "type": "structured_analysis",
                "parameters": query.get('parameters', {})
            })
        
        # Update session with query
        sessions_table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression='SET #ctx.lastQuery = :query, updatedAt = :timestamp',
            ExpressionAttributeNames={'#ctx': 'context'},
            ExpressionAttributeValues={
                ':query': content,
                ':timestamp': int(datetime.now().timestamp() * 1000)
            }
        )
        
        return {
            'sessionId': session_id,
            'prompt': prompt,
            'queryType': query_type,
            'originalQuery': content,
            'context': context
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'error': str(e),
            'statusCode': 500
        }