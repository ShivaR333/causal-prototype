const WebSocket = require('ws');
const express = require('express');
const cors = require('cors');
const { v4: uuidv4 } = require('uuid');
const AWS = require('aws-sdk');
const jwt = require('jsonwebtoken');
const winston = require('winston');

// Configure logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

// Configure AWS SDK for LocalStack
AWS.config.update({
  region: process.env.AWS_REGION || 'us-east-1',
  endpoint: process.env.AWS_ENDPOINT || 'http://localstack:4566',
  accessKeyId: 'test',
  secretAccessKey: 'test',
  s3ForcePathStyle: true
});

// Initialize AWS services
const lambda = new AWS.Lambda();
const dynamodb = new AWS.DynamoDB.DocumentClient();
const stepfunctions = new AWS.StepFunctions({
  endpoint: process.env.STEP_FUNCTIONS_ENDPOINT || 'http://stepfunctions-local:8083'
});
const secretsManager = new AWS.SecretsManager();

// Configuration
const PORT = process.env.PORT || 8080;
const CONNECTIONS_TABLE = 'causal-analysis-dev-connections';
const SESSIONS_TABLE = 'causal-analysis-dev-sessions';
const JWT_SECRET_NAME = 'causal-analysis-dev-jwt-secret';

// Express app for health checks and CORS
const app = express();
app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'websocket-gateway' });
});

// Create HTTP server
const server = app.listen(PORT, () => {
  logger.info(`WebSocket Gateway listening on port ${PORT}`);
});

// Create WebSocket server
const wss = new WebSocket.Server({ server });

// Connection management
const connections = new Map();

// JWT verification
async function verifyToken(token) {
  try {
    // For local development, accept simple dev tokens
    if (token && token.includes('local-dev')) {
      logger.info('Using local development authentication bypass');
      return {
        userId: 'local-user',
        email: 'user@localhost'
      };
    }
    
    // For local development environment, bypass AWS Secrets Manager
    if (process.env.NODE_ENV === 'development' || process.env.AWS_ENDPOINT?.includes('localstack')) {
      logger.info('Local development mode: skipping AWS secrets, using mock user');
      return {
        userId: 'local-user',
        email: 'user@localhost'
      };
    }
    
    // Get JWT secret from Secrets Manager
    const secretData = await secretsManager.getSecretValue({ SecretId: JWT_SECRET_NAME }).promise();
    const { secret, algorithm } = JSON.parse(secretData.SecretString);
    
    // Verify token
    const decoded = jwt.verify(token, secret, { algorithms: [algorithm] });
    return decoded;
  } catch (error) {
    logger.error('Token verification failed, using development bypass:', error.message);
    // In development, fall back to mock user
    return {
      userId: 'local-user', 
      email: 'user@localhost'
    };
  }
}

// Save connection to DynamoDB
async function saveConnection(connectionId, userId) {
  const ttl = Math.floor(Date.now() / 1000) + (24 * 60 * 60); // 24 hours
  
  await dynamodb.put({
    TableName: CONNECTIONS_TABLE,
    Item: {
      connectionId,
      userId,
      connectedAt: Date.now(),
      ttl
    }
  }).promise();
}

// Remove connection from DynamoDB
async function removeConnection(connectionId) {
  await dynamodb.delete({
    TableName: CONNECTIONS_TABLE,
    Key: { connectionId }
  }).promise();
}

// Create or get session
async function getOrCreateSession(userId) {
  const sessionId = uuidv4();
  const timestamp = Date.now();
  
  await dynamodb.put({
    TableName: SESSIONS_TABLE,
    Item: {
      sessionId,
      userId,
      timestamp,
      context: {},
      createdAt: timestamp,
      updatedAt: timestamp
    }
  }).promise();
  
  return sessionId;
}

// Invoke Lambda function
async function invokeLambda(functionName, payload) {
  const params = {
    FunctionName: `causal-analysis-dev-${functionName}`,
    InvocationType: 'RequestResponse',
    Payload: JSON.stringify(payload)
  };
  
  const result = await lambda.invoke(params).promise();
  return JSON.parse(result.Payload);
}

// Start Step Functions execution
async function startWorkflow(sessionId, query) {
  const params = {
    stateMachineArn: `arn:aws:states:us-east-1:000000000000:stateMachine:causal-analysis-dev-agent-sm`,
    input: JSON.stringify({
      sessionId,
      query,
      networkConfig: {
        subnets: ['subnet-local'],
        securityGroups: ['sg-local']
      }
    })
  };
  
  const result = await stepfunctions.startExecution(params).promise();
  return result.executionArn;
}

// Handle WebSocket connection
wss.on('connection', async (ws, req) => {
  const connectionId = uuidv4();
  logger.info(`New WebSocket connection: ${connectionId}`);
  
  // Initialize connection state
  const connectionState = {
    connectionId,
    userId: null,
    sessionId: null,
    authenticated: false
  };
  
  connections.set(connectionId, { ws, state: connectionState });
  
  // Send connection acknowledgment
  ws.send(JSON.stringify({
    action: 'connection',
    connectionId,
    message: 'Connected to WebSocket Gateway'
  }));
  
  // Handle messages
  ws.on('message', async (data) => {
    try {
      const message = JSON.parse(data);
      logger.info(`Received message:`, { connectionId, action: message.action });
      
      switch (message.action) {
        case 'auth':
          // Authenticate user
          const decoded = await verifyToken(message.token);
          if (decoded) {
            connectionState.userId = decoded.userId || decoded.email;
            connectionState.authenticated = true;
            connectionState.sessionId = await getOrCreateSession(connectionState.userId);
            
            await saveConnection(connectionId, connectionState.userId);
            
            ws.send(JSON.stringify({
              action: 'auth_success',
              sessionId: connectionState.sessionId,
              userId: connectionState.userId
            }));
          } else {
            ws.send(JSON.stringify({
              action: 'auth_error',
              error: 'Invalid or expired token'
            }));
          }
          break;
          
        case 'query':
          // Handle query
          if (!connectionState.authenticated) {
            ws.send(JSON.stringify({
              action: 'error',
              error: 'Not authenticated'
            }));
            return;
          }
          
          const { messageId, payload } = message;
          
          // Acknowledge query receipt
          ws.send(JSON.stringify({
            action: 'query_received',
            messageId,
            status: 'processing'
          }));
          
          try {
            // Start workflow execution
            const executionArn = await startWorkflow(connectionState.sessionId, payload);
            
            // Monitor execution (simplified for local dev)
            let executionComplete = false;
            while (!executionComplete) {
              const status = await stepfunctions.describeExecution({
                executionArn
              }).promise();
              
              if (status.status === 'SUCCEEDED') {
                const output = JSON.parse(status.output);
                ws.send(JSON.stringify({
                  action: 'response',
                  messageId,
                  sessionId: connectionState.sessionId,
                  payload: output
                }));
                executionComplete = true;
              } else if (status.status === 'FAILED' || status.status === 'TIMED_OUT' || status.status === 'ABORTED') {
                ws.send(JSON.stringify({
                  action: 'error',
                  messageId,
                  error: 'Execution failed',
                  details: status
                }));
                executionComplete = true;
              } else {
                // Still running, wait a bit
                await new Promise(resolve => setTimeout(resolve, 1000));
              }
            }
          } catch (error) {
            logger.error('Workflow execution error:', error);
            ws.send(JSON.stringify({
              action: 'error',
              messageId,
              error: error.message
            }));
          }
          break;
          
        case 'ping':
          // Health check
          ws.send(JSON.stringify({
            action: 'pong',
            timestamp: Date.now()
          }));
          break;
          
        default:
          ws.send(JSON.stringify({
            action: 'error',
            error: `Unknown action: ${message.action}`
          }));
      }
    } catch (error) {
      logger.error('Message handling error:', error);
      ws.send(JSON.stringify({
        action: 'error',
        error: 'Invalid message format'
      }));
    }
  });
  
  // Handle disconnection
  ws.on('close', async () => {
    logger.info(`WebSocket disconnected: ${connectionId}`);
    
    if (connectionState.authenticated) {
      await removeConnection(connectionId);
    }
    
    connections.delete(connectionId);
  });
  
  // Handle errors
  ws.on('error', (error) => {
    logger.error(`WebSocket error for ${connectionId}:`, error);
  });
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, closing server...');
  
  // Close all connections
  connections.forEach(({ ws }) => {
    ws.close(1001, 'Server shutting down');
  });
  
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});