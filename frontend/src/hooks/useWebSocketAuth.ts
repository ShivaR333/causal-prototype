import { useState, useEffect, useCallback, useRef } from 'react';
import { wsClient } from '../lib/websocket';
import { AuthState, AuthStatus, WebSocketCallbacks } from '../types/websocket';

interface UseWebSocketAuthReturn {
  // Auth state
  authStatus: AuthStatus;
  isConnected: boolean;
  isAuthenticated: boolean;
  isConnecting: boolean;
  isAuthenticating: boolean;
  
  // Methods
  connect: () => Promise<void>;
  authenticate: (token?: string) => Promise<AuthStatus>;
  disconnect: () => void;
  reset: () => Promise<void>;
  
  // UI state helpers
  canSendMessages: boolean;
  connectionStatus: string;
}

export function useWebSocketAuth(): UseWebSocketAuthReturn {
  const [authStatus, setAuthStatus] = useState<AuthStatus>({
    state: AuthState.IDLE,
    sessionId: null,
    userId: null,
    error: null
  });
  const [isConnected, setIsConnected] = useState(false);
  
  // Track if we're currently connecting/authenticating
  const connectingRef = useRef(false);
  const authenticatingRef = useRef(false);

  // Update auth status when WebSocket state changes
  const updateAuthStatus = useCallback(() => {
    const status = wsClient.getAuthStatus();
    setAuthStatus(status);
    setIsConnected(wsClient.isConnected());
  }, []);

  // Set up WebSocket callbacks
  useEffect(() => {
    const callbacks: Partial<WebSocketCallbacks> = {
      onConnect: () => {
        connectingRef.current = false;
        updateAuthStatus();
      },
      onDisconnect: () => {
        connectingRef.current = false;
        authenticatingRef.current = false;
        updateAuthStatus();
      },
      onAuthSuccess: () => {
        authenticatingRef.current = false;
        updateAuthStatus();
      },
      onAuthError: () => {
        authenticatingRef.current = false;
        updateAuthStatus();
      }
    };

    // Merge with existing callbacks
    const existingCallbacks = { ...wsClient['callbacks'] };
    wsClient.setCallbacks({
      ...existingCallbacks,
      ...callbacks,
      // Preserve existing callbacks by calling both
      onConnect: () => {
        existingCallbacks.onConnect?.();
        callbacks.onConnect?.();
      },
      onDisconnect: () => {
        existingCallbacks.onDisconnect?.();
        callbacks.onDisconnect?.();
      },
      onAuthSuccess: (data) => {
        existingCallbacks.onAuthSuccess?.(data);
        callbacks.onAuthSuccess?.(data);
      },
      onAuthError: (error) => {
        existingCallbacks.onAuthError?.(error);
        callbacks.onAuthError?.(error);
      }
    });

    // Update initial status
    updateAuthStatus();

    // Cleanup
    return () => {
      // Restore original callbacks on unmount
      wsClient.setCallbacks(existingCallbacks);
    };
  }, [updateAuthStatus]);

  // Connect to WebSocket
  const connect = useCallback(async (): Promise<void> => {
    if (connectingRef.current || wsClient.isConnected()) {
      return;
    }

    connectingRef.current = true;
    try {
      await wsClient.connect();
    } finally {
      connectingRef.current = false;
      updateAuthStatus();
    }
  }, [updateAuthStatus]);

  // Authenticate
  const authenticate = useCallback(async (token?: string): Promise<AuthStatus> => {
    if (authenticatingRef.current) {
      // Wait for existing auth to complete
      return wsClient.authenticate(token);
    }

    authenticatingRef.current = true;
    try {
      const status = await wsClient.authenticate(token);
      updateAuthStatus();
      return status;
    } finally {
      authenticatingRef.current = false;
    }
  }, [updateAuthStatus]);

  // Disconnect
  const disconnect = useCallback(() => {
    wsClient.disconnect();
    updateAuthStatus();
  }, [updateAuthStatus]);

  // Reset connection and auth
  const reset = useCallback(async (): Promise<void> => {
    disconnect();
    
    // Wait a bit before reconnecting
    await new Promise(resolve => setTimeout(resolve, 100));
    
    await connect();
    await authenticate();
  }, [connect, authenticate, disconnect]);

  // Computed values
  const isAuthenticated = authStatus.state === AuthState.AUTHENTICATED;
  const isConnecting = authStatus.state === AuthState.CONNECTING || connectingRef.current;
  const isAuthenticating = authStatus.state === AuthState.AUTHENTICATING || authenticatingRef.current;
  const canSendMessages = isConnected && isAuthenticated;

  // Connection status string for UI
  const connectionStatus = (() => {
    switch (authStatus.state) {
      case AuthState.IDLE:
        return 'Not connected';
      case AuthState.CONNECTING:
        return 'Connecting...';
      case AuthState.AUTHENTICATING:
        return 'Authenticating...';
      case AuthState.AUTHENTICATED:
        return `Connected (Session: ${authStatus.sessionId?.slice(-8) || 'Unknown'})`;
      case AuthState.ERROR:
        return `Error: ${authStatus.error || 'Connection failed'}`;
      case AuthState.DISCONNECTED:
        return 'Disconnected';
      default:
        return 'Unknown';
    }
  })();

  return {
    // State
    authStatus,
    isConnected,
    isAuthenticated,
    isConnecting,
    isAuthenticating,
    
    // Methods
    connect,
    authenticate,
    disconnect,
    reset,
    
    // UI helpers
    canSendMessages,
    connectionStatus
  };
}