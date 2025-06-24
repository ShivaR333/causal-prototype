import { 
  AuthState, 
  AuthStatus, 
  WebSocketMessage, 
  WebSocketCallbacks, 
  QueuedMessage 
} from '../types/websocket';
import { authService } from './auth';

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private callbacks: WebSocketCallbacks = {};
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 1000;
  
  // Authentication state
  private authState: AuthState = AuthState.IDLE;
  private authPromise: Promise<AuthStatus> | null = null;
  private authResolver: ((value: AuthStatus) => void) | null = null;
  private authRejecter: ((reason: any) => void) | null = null;
  
  // Session data
  private sessionId: string | null = null;
  private userId: string | null = null;
  
  // Message queue for pending auth
  private messageQueue: QueuedMessage[] = [];
  private isProcessingQueue = false;

  constructor(url: string) {
    this.url = url;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.authState = AuthState.CONNECTING;
        
        // Get authentication token for WebSocket connection
        const token = authService.getIdToken();
        if (!token) {
          reject(new Error('Authentication required. Please sign in first.'));
          return;
        }
        
        // Add token to WebSocket URL as query parameter for AWS API Gateway
        const urlWithAuth = `${this.url}?token=${encodeURIComponent(token)}`;
        this.ws = new WebSocket(urlWithAuth);

        this.ws.onopen = () => {
          console.log('WebSocket connected to AWS API Gateway');
          this.reconnectAttempts = 0;
          this.authState = AuthState.AUTHENTICATED; // Auth handled by API Gateway authorizer
          this.callbacks.onConnect?.();
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.handleDisconnect();
          
          if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.callbacks.onError?.(error);
          reject(error);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  authenticate(token?: string): Promise<AuthStatus> {
    // For AWS API Gateway WebSocket, authentication is handled during connection
    // The Lambda authorizer validates the token before allowing the connection
    
    if (this.authState === AuthState.AUTHENTICATED && this.ws?.readyState === WebSocket.OPEN) {
      return Promise.resolve(this.getAuthStatus());
    }
    
    // If not connected or not authenticated, need to reconnect with fresh token
    return this.connect().then(() => this.getAuthStatus());
  }

  private handleMessage(message: WebSocketMessage) {
    console.log('Received WebSocket message:', message);

    switch (message.action) {
      case 'connection':
        // Connection acknowledgment from AWS API Gateway
        this.handleConnectionAck(message);
        break;
      
      case 'prompt':
        this.callbacks.onPrompt?.(message.payload);
        break;
      
      case 'response':
        this.callbacks.onResponse?.(message.payload);
        break;
      
      case 'query_received':
        console.log('Query received by server:', message);
        break;
      
      case 'error':
        console.error('Server error:', message.error);
        this.callbacks.onError?.(new Event('server-error'));
        break;
      
      case 'pong':
        // Health check response
        break;
      
      default:
        console.warn('Unknown message action:', message.action);
    }

    // Call general message callback
    this.callbacks.onMessage?.(message);
  }

  private handleConnectionAck(message: WebSocketMessage) {
    // Extract session info from connection acknowledgment
    this.sessionId = message.sessionId || message.payload?.sessionId || null;
    this.userId = (message as any).userId || message.payload?.userId || null;
    
    const authStatus = this.getAuthStatus();
    
    // Resolve auth promise if exists
    if (this.authResolver) {
      this.authResolver(authStatus);
      this.authResolver = null;
      this.authRejecter = null;
    }
    
    // Call success callback
    this.callbacks.onAuthSuccess?.(message.payload);
    
    // Process queued messages
    this.processMessageQueue();
  }

  private handleAuthError(error: string) {
    this.authState = AuthState.ERROR;
    
    // Reject auth promise
    if (this.authRejecter) {
      this.authRejecter(new Error(error));
      this.authResolver = null;
      this.authRejecter = null;
    }
    
    // Clear auth data
    this.sessionId = null;
    this.userId = null;
    
    // Call error callback
    this.callbacks.onAuthError?.(error);
    
    // Clear message queue
    this.clearMessageQueue(new Error(error));
  }

  private handleDisconnect() {
    this.authState = AuthState.DISCONNECTED;
    this.sessionId = null;
    this.userId = null;
    
    // Reject pending auth
    if (this.authRejecter) {
      this.authRejecter(new Error('Disconnected during authentication'));
      this.authResolver = null;
      this.authRejecter = null;
    }
    
    // Clear message queue
    this.clearMessageQueue(new Error('WebSocket disconnected'));
    
    this.callbacks.onDisconnect?.();
  }

  private async processMessageQueue() {
    if (this.isProcessingQueue || this.messageQueue.length === 0) {
      return;
    }

    this.isProcessingQueue = true;
    
    while (this.messageQueue.length > 0 && this.authState === AuthState.AUTHENTICATED) {
      const queued = this.messageQueue.shift();
      if (queued) {
        try {
          this.send(queued.message);
          queued.resolve?.();
        } catch (error) {
          queued.reject?.(error);
        }
      }
    }
    
    this.isProcessingQueue = false;
  }

  private clearMessageQueue(error: Error) {
    while (this.messageQueue.length > 0) {
      const queued = this.messageQueue.shift();
      queued?.reject?.(error);
    }
  }

  sendQuery(query: any, messageId?: string): Promise<void> {
    const message: WebSocketMessage = {
      action: 'query',
      sessionId: this.sessionId || undefined,
      messageId: messageId || `msg-${Date.now()}`,
      payload: query
    };

    // If authenticated, send immediately
    if (this.authState === AuthState.AUTHENTICATED) {
      return this.sendWithRetry(message);
    }

    // If authenticating, queue the message
    if (this.authState === AuthState.AUTHENTICATING) {
      return new Promise((resolve, reject) => {
        this.messageQueue.push({
          message,
          timestamp: Date.now(),
          resolve,
          reject
        });
      });
    }

    // Otherwise, reject
    return Promise.reject(new Error(`Cannot send query in state: ${this.authState}`));
  }

  private sendWithRetry(message: WebSocketMessage): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.send(message);
        resolve();
      } catch (error) {
        reject(error);
      }
    });
  }

  sendResponse(response: string, sessionId: string): Promise<void> {
    const message: WebSocketMessage = {
      action: 'response',
      sessionId,
      payload: { response }
    };

    if (this.authState !== AuthState.AUTHENTICATED) {
      return Promise.reject(new Error('Not authenticated'));
    }

    return this.sendWithRetry(message);
  }

  ping(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.send({ action: 'ping' });
    }
  }

  private send(message: WebSocketMessage): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }

    this.ws.send(JSON.stringify(message));
  }

  private reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    setTimeout(() => {
      this.connect().catch((error) => {
        console.error('Reconnection failed:', error);
      });
    }, this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1));
  }

  setCallbacks(callbacks: Partial<WebSocketCallbacks>): void {
    this.callbacks = { ...this.callbacks, ...callbacks };
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this.handleDisconnect();
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  isAuthenticated(): boolean {
    return this.authState === AuthState.AUTHENTICATED;
  }

  getAuthState(): AuthState {
    return this.authState;
  }

  getAuthStatus(): AuthStatus {
    return {
      state: this.authState,
      sessionId: this.sessionId,
      userId: this.userId,
      error: this.authState === AuthState.ERROR ? 'Authentication failed' : null
    };
  }

  getSessionId(): string | null {
    return this.sessionId;
  }

  getUserId(): string | null {
    return this.userId;
  }
}

// Create singleton instance - will use AWS API Gateway WebSocket endpoint
const WEBSOCKET_URL = process.env.NEXT_PUBLIC_WEBSOCKET_URL || '';
if (!WEBSOCKET_URL) {
  console.error('NEXT_PUBLIC_WEBSOCKET_URL environment variable is required. This should be your AWS API Gateway WebSocket URL (wss://...)');
}
export const wsClient = new WebSocketClient(WEBSOCKET_URL);