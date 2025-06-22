interface WebSocketMessage {
  action: string;
  sessionId?: string;
  messageId?: string;
  payload?: any;
  error?: any;
  token?: string;
}

interface WebSocketCallbacks {
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onAuthSuccess?: (data: { sessionId: string; userId: string }) => void;
  onPrompt?: (data: { prompt: string; sessionId: string }) => void;
  onResponse?: (data: { payload: any; sessionId: string }) => void;
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private callbacks: WebSocketCallbacks = {};
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 1000;
  private authenticated = false;
  private sessionId: string | null = null;
  private userId: string | null = null;

  constructor(url: string) {
    this.url = url;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
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
          this.authenticated = false;
          this.callbacks.onDisconnect?.();
          
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

  private handleMessage(message: WebSocketMessage) {
    console.log('Received WebSocket message:', message);

    switch (message.action) {
      case 'connection':
        // Connection acknowledgment
        break;
      
      case 'auth_success':
        this.authenticated = true;
        this.sessionId = message.sessionId || null;
        this.userId = message.payload?.userId || null;
        this.callbacks.onAuthSuccess?.(message.payload);
        break;
      
      case 'auth_error':
        this.authenticated = false;
        console.error('Authentication failed:', message.error);
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

  authenticate(token?: string): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }

    // For local development, use a simple bypass token
    let authToken = token;
    if (!authToken) {
      authToken = 'local-dev-token-bypass';
    }

    const authMessage: WebSocketMessage = {
      action: 'auth',
      token: authToken
    };

    this.send(authMessage);
  }

  sendQuery(query: any, messageId?: string): void {
    if (!this.authenticated) {
      throw new Error('Not authenticated');
    }

    const message: WebSocketMessage = {
      action: 'query',
      sessionId: this.sessionId || undefined,
      messageId: messageId || `msg-${Date.now()}`,
      payload: query
    };

    this.send(message);
  }

  sendResponse(response: string, sessionId: string): void {
    if (!this.authenticated) {
      throw new Error('Not authenticated');
    }

    const message: WebSocketMessage = {
      action: 'response',
      sessionId,
      payload: { response }
    };

    this.send(message);
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

  setCallbacks(callbacks: Partial<WebSocketCallbacks>): void {
    this.callbacks = { ...this.callbacks, ...callbacks };
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this.authenticated = false;
    this.sessionId = null;
    this.userId = null;
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  isAuthenticated(): boolean {
    return this.authenticated;
  }

  getSessionId(): string | null {
    return this.sessionId;
  }

  getUserId(): string | null {
    return this.userId;
  }
}

// Create singleton instance
const WEBSOCKET_URL = process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8080';
export const wsClient = new WebSocketClient(WEBSOCKET_URL);