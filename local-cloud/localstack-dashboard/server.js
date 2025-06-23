const express = require('express');
const cors = require('cors');
const axios = require('axios');
const AWS = require('aws-sdk');
const winston = require('winston');
const WebSocket = require('ws');
const http = require('http');
const { Server } = require('socket.io');

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

// Configuration
const PORT = process.env.PORT || 4567;
const LOCALSTACK_URL = process.env.LOCALSTACK_URL || 'http://localstack:4566';
const WEBSOCKET_GATEWAY_URL = process.env.WEBSOCKET_GATEWAY_URL || 'ws://websocket-gateway:8080';

// Configure AWS SDK for LocalStack
AWS.config.update({
  region: 'eu-central-1',
  endpoint: LOCALSTACK_URL,
  accessKeyId: 'test',
  secretAccessKey: 'test',
  s3ForcePathStyle: true
});

// Initialize AWS services
const s3 = new AWS.S3();
const dynamodb = new AWS.DynamoDB();
const dynamodbDoc = new AWS.DynamoDB.DocumentClient();
const lambda = new AWS.Lambda();
const secretsManager = new AWS.SecretsManager();
const stepfunctions = new AWS.StepFunctions();
const cognito = new AWS.CognitoIdentityServiceProvider();

const app = express();
app.use(cors());
app.use(express.json());

// Dashboard statistics
const dashboardStats = {
  startTime: Date.now(),
  totalRequests: 0,
  serviceChecks: 0,
  errors: 0
};

// WebSocket message monitoring
const wsMessages = [];
const MAX_MESSAGES = 500;
let wsGatewayConnection = null;
let dashboardIO = null;

// WebSocket message storage
function addWSMessage(direction, message, connectionId = null) {
  const wsMessage = {
    id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    timestamp: Date.now(),
    direction, // 'incoming' or 'outgoing'
    message: typeof message === 'string' ? message : JSON.stringify(message),
    connectionId,
    parsed: null
  };

  // Try to parse the message if it's JSON
  try {
    wsMessage.parsed = typeof message === 'string' ? JSON.parse(message) : message;
  } catch (e) {
    // Not JSON, keep as string
  }

  wsMessages.push(wsMessage);
  
  // Keep only recent messages
  if (wsMessages.length > MAX_MESSAGES) {
    wsMessages.shift();
  }

  // Broadcast to dashboard clients
  if (dashboardIO) {
    dashboardIO.emit('wsMessage', wsMessage);
  }

  logger.info(`WebSocket ${direction}:`, { connectionId, message: wsMessage.message.substring(0, 200) });
}

// Service health cache
let serviceHealth = {};
let lastHealthCheck = 0;
const HEALTH_CACHE_DURATION = 30000; // 30 seconds

// LocalStack service endpoints to monitor
const SERVICES = [
  'dynamodb',
  's3',
  'lambda',
  'secretsmanager',
  'stepfunctions',
  'cognito-idp',
  'sts',
  'iam',
  'logs',
  'apigateway'
];

// Check individual service health
async function checkServiceHealth(service) {
  try {
    const response = await axios.get(`${LOCALSTACK_URL}/_localstack/health`, {
      timeout: 5000
    });
    
    const serviceStatus = response.data.services?.[service];
    return {
      service,
      status: serviceStatus || 'unknown',
      available: serviceStatus === 'available' || serviceStatus === 'running',
      lastChecked: Date.now()
    };
  } catch (error) {
    return {
      service,
      status: 'error',
      available: false,
      error: error.message,
      lastChecked: Date.now()
    };
  }
}

// Get resource counts for services
async function getResourceCounts() {
  const resources = {
    s3: { buckets: 0, objects: 0 },
    dynamodb: { tables: 0, items: 0 },
    lambda: { functions: 0 },
    secrets: { secrets: 0 },
    cognito: { userPools: 0 }
  };

  try {
    // S3 buckets
    const buckets = await s3.listBuckets().promise();
    resources.s3.buckets = buckets.Buckets?.length || 0;
    
    // Try to count objects (simplified)
    let totalObjects = 0;
    for (const bucket of buckets.Buckets || []) {
      try {
        const objects = await s3.listObjectsV2({ Bucket: bucket.Name }).promise();
        totalObjects += objects.Contents?.length || 0;
      } catch (e) {
        // Skip buckets we can't access
      }
    }
    resources.s3.objects = totalObjects;

    // DynamoDB tables
    const tables = await dynamodb.listTables().promise();
    resources.dynamodb.tables = tables.TableNames?.length || 0;

    // Lambda functions
    const functions = await lambda.listFunctions().promise();
    resources.lambda.functions = functions.Functions?.length || 0;

    // Secrets
    const secrets = await secretsManager.listSecrets().promise();
    resources.secrets.secrets = secrets.SecretList?.length || 0;

    // Cognito User Pools
    const userPools = await cognito.listUserPools({ MaxResults: 60 }).promise();
    resources.cognito.userPools = userPools.UserPools?.length || 0;

  } catch (error) {
    logger.error('Error getting resource counts:', error.message);
  }

  return resources;
}

// Refresh service health
async function refreshServiceHealth() {
  const now = Date.now();
  if (now - lastHealthCheck < HEALTH_CACHE_DURATION) {
    return serviceHealth;
  }

  logger.info('Refreshing service health...');
  const healthPromises = SERVICES.map(service => checkServiceHealth(service));
  const healthResults = await Promise.all(healthPromises);
  
  serviceHealth = {};
  healthResults.forEach(result => {
    serviceHealth[result.service] = result;
  });
  
  lastHealthCheck = now;
  dashboardStats.serviceChecks++;
  
  return serviceHealth;
}

// Dashboard HTML
app.get('/dashboard', (req, res) => {
  const html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LocalStack Dashboard</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
            margin: 0; padding: 20px; background: #f5f5f5; 
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { 
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); 
            color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; 
        }
        .stats-grid { 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 15px; margin-bottom: 20px; 
        }
        .stat-card { 
            background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
            text-align: center;
        }
        .stat-value { font-size: 1.8em; font-weight: bold; color: #ff6b6b; }
        .stat-label { color: #666; margin-top: 5px; font-size: 0.9em; }
        .services-grid { 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 20px; margin-bottom: 20px; 
        }
        .service-card { 
            background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        }
        .service-header { 
            display: flex; justify-content: between; align-items: center; margin-bottom: 15px; 
        }
        .service-name { font-size: 1.2em; font-weight: 600; }
        .status-available { color: #28a745; }
        .status-unavailable { color: #dc3545; }
        .status-unknown { color: #ffc107; }
        .resource-list { margin-top: 10px; }
        .resource-item { 
            display: flex; justify-content: space-between; padding: 5px 0; 
            border-bottom: 1px solid #eee; 
        }
        .resource-item:last-child { border-bottom: none; }
        .refresh-btn { 
            background: #ff6b6b; color: white; border: none; padding: 10px 20px; 
            border-radius: 4px; cursor: pointer; margin-bottom: 20px; 
        }
        .refresh-btn:hover { background: #ff5252; }
        .auto-refresh { margin-left: 10px; }
        .logs-section { 
            background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
            margin-top: 20px; 
        }
        .websocket-section { 
            background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
            margin-top: 20px; 
        }
        .ws-messages-container { 
            max-height: 400px; overflow-y: auto; border: 1px solid #eee; border-radius: 4px; 
        }
        .ws-message { 
            padding: 10px; border-bottom: 1px solid #f0f0f0; font-family: monospace; font-size: 0.85em; 
        }
        .ws-message:last-child { border-bottom: none; }
        .ws-message-header { 
            display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; 
        }
        .ws-direction-incoming { background: #e8f5e8; border-left: 4px solid #28a745; }
        .ws-direction-outgoing { background: #e8f4fd; border-left: 4px solid #007bff; }
        .ws-direction-system { background: #fff3cd; border-left: 4px solid #ffc107; }
        .ws-timestamp { color: #666; font-size: 0.8em; }
        .ws-direction { 
            font-weight: bold; font-size: 0.8em; 
            padding: 2px 6px; border-radius: 3px; color: white; 
        }
        .ws-direction.incoming { background: #28a745; }
        .ws-direction.outgoing { background: #007bff; }
        .ws-direction.system { background: #ffc107; color: #333; }
        .ws-content { 
            margin-top: 5px; word-break: break-all; 
            max-height: 100px; overflow-y: auto; 
        }
        .endpoint-section { 
            background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
            margin-top: 20px; 
        }
        .endpoint-list { font-family: monospace; }
        .endpoint-item { 
            padding: 8px; margin: 5px 0; background: #f8f9fa; border-radius: 4px; 
            border-left: 4px solid #ff6b6b; 
        }
        .error-card { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📦 LocalStack Dashboard</h1>
            <p>AWS service emulation monitoring</p>
        </div>

        <button class="refresh-btn" onclick="refreshData()">🔄 Refresh</button>
        <label class="auto-refresh">
            <input type="checkbox" id="autoRefresh" onchange="toggleAutoRefresh()"> Auto-refresh (30s)
        </label>

        <div class="stats-grid" id="statsGrid">
            <!-- Stats will be populated by JavaScript -->
        </div>

        <div class="services-grid" id="servicesGrid">
            <!-- Services will be populated by JavaScript -->
        </div>

        <div class="endpoint-section">
            <h3>🔗 LocalStack Endpoints</h3>
            <div class="endpoint-list">
                <div class="endpoint-item">Health Check: <strong>${LOCALSTACK_URL}/_localstack/health</strong></div>
                <div class="endpoint-item">Dashboard: <strong>${LOCALSTACK_URL}/_localstack/dashboard</strong></div>
                <div class="endpoint-item">DynamoDB: <strong>${LOCALSTACK_URL}</strong> (service: dynamodb)</div>
                <div class="endpoint-item">S3: <strong>${LOCALSTACK_URL}</strong> (service: s3)</div>
                <div class="endpoint-item">Lambda: <strong>${LOCALSTACK_URL}</strong> (service: lambda)</div>
            </div>
        </div>

        <div class="websocket-section">
            <h3>🔌 WebSocket Messages (Live)</h3>
            <div class="ws-messages-container" id="wsMessagesContainer">
                <div style="padding: 20px; text-align: center; color: #666;">
                    Connecting to WebSocket Gateway...
                </div>
            </div>
        </div>

        <div class="logs-section">
            <h3>📊 System Information</h3>
            <div id="systemInfo">
                <!-- System info will be populated by JavaScript -->
            </div>
        </div>
    </div>

    <script src="/socket.io/socket.io.js"></script>
    <script>
        let autoRefreshInterval = null;
        let socket = null;

        // Initialize Socket.IO connection
        function initializeWebSocket() {
            socket = io();
            
            socket.on('connect', () => {
                console.log('Connected to dashboard server');
                updateWSConnectionStatus('Connected to dashboard server');
            });
            
            socket.on('disconnect', () => {
                console.log('Disconnected from dashboard server');
                updateWSConnectionStatus('Disconnected from dashboard server');
            });
            
            socket.on('wsMessage', (message) => {
                addWSMessageToUI(message);
            });
            
            socket.on('wsMessageHistory', (messages) => {
                displayWSMessages(messages);
            });
        }

        function updateWSConnectionStatus(status) {
            const container = document.getElementById('wsMessagesContainer');
            if (container.children.length === 1 && container.children[0].style.textAlign === 'center') {
                container.innerHTML = \`<div style="padding: 20px; text-align: center; color: #666;">\${status}</div>\`;
            }
        }

        function formatTimestamp(timestamp) {
            return new Date(timestamp).toLocaleTimeString();
        }

        function addWSMessageToUI(message) {
            const container = document.getElementById('wsMessagesContainer');
            
            // Remove loading message if present
            if (container.children.length === 1 && container.children[0].style.textAlign === 'center') {
                container.innerHTML = '';
            }

            const messageDiv = document.createElement('div');
            messageDiv.className = \`ws-message ws-direction-\${message.direction}\`;
            messageDiv.innerHTML = \`
                <div class="ws-message-header">
                    <span class="ws-direction \${message.direction}">\${message.direction.toUpperCase()}</span>
                    <span class="ws-timestamp">\${formatTimestamp(message.timestamp)}</span>
                </div>
                <div class="ws-content">\${message.message}</div>
            \`;

            container.insertBefore(messageDiv, container.firstChild);

            // Keep only recent 50 messages
            while (container.children.length > 50) {
                container.removeChild(container.lastChild);
            }
        }

        function displayWSMessages(messages) {
            const container = document.getElementById('wsMessagesContainer');
            container.innerHTML = '';

            if (messages.length === 0) {
                container.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">No WebSocket messages yet</div>';
                return;
            }

            messages.forEach(message => {
                addWSMessageToUI(message);
            });
        }

        async function fetchWSMessages() {
            try {
                const response = await fetch('/api/websocket-messages?limit=20');
                const messages = await response.json();
                displayWSMessages(messages);
            } catch (error) {
                console.error('Failed to fetch WebSocket messages:', error);
            }
        }

        async function fetchStats() {
            try {
                const response = await fetch('/api/stats');
                return await response.json();
            } catch (error) {
                console.error('Failed to fetch stats:', error);
                return null;
            }
        }

        async function fetchServices() {
            try {
                const response = await fetch('/api/services');
                return await response.json();
            } catch (error) {
                console.error('Failed to fetch services:', error);
                return [];
            }
        }

        async function fetchResources() {
            try {
                const response = await fetch('/api/resources');
                return await response.json();
            } catch (error) {
                console.error('Failed to fetch resources:', error);
                return {};
            }
        }

        function formatUptime(startTime) {
            const uptime = Math.floor((Date.now() - startTime) / 1000);
            const hours = Math.floor(uptime / 3600);
            const minutes = Math.floor((uptime % 3600) / 60);
            const seconds = uptime % 60;
            return \`\${hours}h \${minutes}m \${seconds}s\`;
        }

        function updateStats(stats) {
            if (!stats) return;
            
            const statsGrid = document.getElementById('statsGrid');
            statsGrid.innerHTML = \`
                <div class="stat-card">
                    <div class="stat-value">\${stats.servicesAvailable}</div>
                    <div class="stat-label">Services Available</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">\${stats.totalServices}</div>
                    <div class="stat-label">Total Services</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">\${stats.totalRequests}</div>
                    <div class="stat-label">API Requests</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">\${formatUptime(stats.startTime)}</div>
                    <div class="stat-label">Dashboard Uptime</div>
                </div>
            \`;
        }

        function updateServices(services, resources) {
            const servicesGrid = document.getElementById('servicesGrid');
            
            const serviceCards = services.map(service => {
                const statusClass = service.available ? 'status-available' : 
                                  service.status === 'unknown' ? 'status-unknown' : 'status-unavailable';
                const statusIcon = service.available ? '✅' : service.status === 'unknown' ? '⚠️' : '❌';
                
                let resourceInfo = '';
                if (service.service === 's3' && resources.s3) {
                    resourceInfo = \`
                        <div class="resource-list">
                            <div class="resource-item">
                                <span>Buckets:</span><span>\${resources.s3.buckets}</span>
                            </div>
                            <div class="resource-item">
                                <span>Objects:</span><span>\${resources.s3.objects}</span>
                            </div>
                        </div>
                    \`;
                } else if (service.service === 'dynamodb' && resources.dynamodb) {
                    resourceInfo = \`
                        <div class="resource-list">
                            <div class="resource-item">
                                <span>Tables:</span><span>\${resources.dynamodb.tables}</span>
                            </div>
                        </div>
                    \`;
                } else if (service.service === 'lambda' && resources.lambda) {
                    resourceInfo = \`
                        <div class="resource-list">
                            <div class="resource-item">
                                <span>Functions:</span><span>\${resources.lambda.functions}</span>
                            </div>
                        </div>
                    \`;
                } else if (service.service === 'secretsmanager' && resources.secrets) {
                    resourceInfo = \`
                        <div class="resource-list">
                            <div class="resource-item">
                                <span>Secrets:</span><span>\${resources.secrets.secrets}</span>
                            </div>
                        </div>
                    \`;
                } else if (service.service === 'cognito-idp' && resources.cognito) {
                    resourceInfo = \`
                        <div class="resource-list">
                            <div class="resource-item">
                                <span>User Pools:</span><span>\${resources.cognito.userPools}</span>
                            </div>
                        </div>
                    \`;
                }

                return \`
                    <div class="service-card \${service.available ? '' : 'error-card'}">
                        <div class="service-header">
                            <div class="service-name">\${service.service}</div>
                            <span class="\${statusClass}">\${statusIcon} \${service.status}</span>
                        </div>
                        <div>Last checked: \${new Date(service.lastChecked).toLocaleTimeString()}</div>
                        \${service.error ? \`<div style="color: #721c24; margin-top: 5px;">Error: \${service.error}</div>\` : ''}
                        \${resourceInfo}
                    </div>
                \`;
            }).join('');
            
            servicesGrid.innerHTML = serviceCards;
        }

        function updateSystemInfo(stats) {
            const systemInfo = document.getElementById('systemInfo');
            systemInfo.innerHTML = \`
                <div>LocalStack URL: <strong>${LOCALSTACK_URL}</strong></div>
                <div>Dashboard started: <strong>\${new Date(stats.startTime).toLocaleString()}</strong></div>
                <div>Service checks performed: <strong>\${stats.serviceChecks}</strong></div>
                <div>Errors encountered: <strong>\${stats.errors}</strong></div>
            \`;
        }

        async function refreshData() {
            try {
                const [stats, services, resources] = await Promise.all([
                    fetchStats(),
                    fetchServices(),
                    fetchResources()
                ]);

                updateStats(stats);
                updateServices(services, resources);
                updateSystemInfo(stats);
            } catch (error) {
                console.error('Error refreshing data:', error);
            }
        }

        function toggleAutoRefresh() {
            const checkbox = document.getElementById('autoRefresh');
            if (checkbox.checked) {
                autoRefreshInterval = setInterval(refreshData, 30000);
            } else {
                if (autoRefreshInterval) {
                    clearInterval(autoRefreshInterval);
                    autoRefreshInterval = null;
                }
            }
        }

        // Initial load
        refreshData();
        initializeWebSocket();
        
        // Also refresh WebSocket messages periodically as fallback
        setTimeout(() => {
            fetchWSMessages();
        }, 3000);
    </script>
</body>
</html>
  `;
  res.send(html);
});

// API endpoints
app.get('/api/stats', async (req, res) => {
  dashboardStats.totalRequests++;
  
  try {
    const health = await refreshServiceHealth();
    const availableServices = Object.values(health).filter(s => s.available).length;
    
    res.json({
      servicesAvailable: availableServices,
      totalServices: SERVICES.length,
      totalRequests: dashboardStats.totalRequests,
      serviceChecks: dashboardStats.serviceChecks,
      errors: dashboardStats.errors,
      startTime: dashboardStats.startTime
    });
  } catch (error) {
    dashboardStats.errors++;
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/services', async (req, res) => {
  try {
    const health = await refreshServiceHealth();
    res.json(Object.values(health));
  } catch (error) {
    dashboardStats.errors++;
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/resources', async (req, res) => {
  try {
    const resources = await getResourceCounts();
    res.json(resources);
  } catch (error) {
    dashboardStats.errors++;
    res.status(500).json({ error: error.message });
  }
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'localstack-dashboard' });
});

// API endpoint for WebSocket messages
app.get('/api/websocket-messages', (req, res) => {
  const limit = parseInt(req.query.limit) || 50;
  const recentMessages = wsMessages.slice(-limit).reverse();
  res.json(recentMessages);
});

// WebSocket Gateway monitoring
function connectToWebSocketGateway() {
  try {
    logger.info(`Attempting to connect to WebSocket Gateway at: ${WEBSOCKET_GATEWAY_URL}`);
    
    wsGatewayConnection = new WebSocket(WEBSOCKET_GATEWAY_URL);

    wsGatewayConnection.on('open', () => {
      logger.info('Connected to WebSocket Gateway for monitoring');
      addWSMessage('system', 'Dashboard connected to WebSocket Gateway', 'dashboard');
      
      // Authenticate to receive messages
      const authMessage = {
        action: 'auth',
        token: 'dashboard-monitor-token'
      };
      wsGatewayConnection.send(JSON.stringify(authMessage));
      addWSMessage('outgoing', authMessage, 'dashboard');
    });

    wsGatewayConnection.on('message', (data) => {
      addWSMessage('incoming', data.toString(), 'gateway');
    });

    wsGatewayConnection.on('close', () => {
      logger.warn('WebSocket Gateway connection closed, attempting to reconnect in 10s...');
      addWSMessage('system', 'WebSocket Gateway connection closed', 'dashboard');
      wsGatewayConnection = null;
      setTimeout(connectToWebSocketGateway, 10000);
    });

    wsGatewayConnection.on('error', (error) => {
      logger.error('WebSocket Gateway connection error:', error.message);
      addWSMessage('system', `WebSocket Gateway error: ${error.message}`, 'dashboard');
    });

  } catch (error) {
    logger.error('Failed to connect to WebSocket Gateway:', error.message);
    setTimeout(connectToWebSocketGateway, 10000);
  }
}

// Proxy LocalStack requests (optional)
app.use('/_localstack/*', async (req, res) => {
  try {
    const targetUrl = `${LOCALSTACK_URL}${req.path}`;
    const response = await axios({
      method: req.method,
      url: targetUrl,
      data: req.body,
      headers: req.headers,
      timeout: 10000
    });
    
    res.status(response.status).json(response.data);
  } catch (error) {
    dashboardStats.errors++;
    res.status(500).json({ error: 'LocalStack request failed', details: error.message });
  }
});

// Create HTTP server and Socket.IO
const server = http.createServer(app);
dashboardIO = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// Socket.IO connection handling
dashboardIO.on('connection', (socket) => {
  logger.info('Dashboard client connected:', socket.id);
  
  // Send recent messages to new client
  const recentMessages = wsMessages.slice(-20);
  socket.emit('wsMessageHistory', recentMessages);
  
  socket.on('disconnect', () => {
    logger.info('Dashboard client disconnected:', socket.id);
  });
});

server.listen(PORT, () => {
  logger.info(`LocalStack Dashboard listening on port ${PORT}`);
  logger.info(`Dashboard available at: http://localhost:${PORT}/dashboard`);
  logger.info(`Monitoring LocalStack at: ${LOCALSTACK_URL}`);
  logger.info(`WebSocket Gateway at: ${WEBSOCKET_GATEWAY_URL}`);
  
  // Start WebSocket Gateway monitoring
  setTimeout(connectToWebSocketGateway, 2000);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  server.close(() => {
    logger.info('Process terminated');
  });
});