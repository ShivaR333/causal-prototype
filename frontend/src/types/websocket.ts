export enum AuthState {
  IDLE = 'idle',
  CONNECTING = 'connecting',
  AUTHENTICATING = 'authenticating',
  AUTHENTICATED = 'authenticated',
  ERROR = 'error',
  DISCONNECTED = 'disconnected'
}

export interface AuthStatus {
  state: AuthState;
  sessionId: string | null;
  userId: string | null;
  error: string | null;
}

export interface WebSocketMessage {
  action: string;
  sessionId?: string;
  messageId?: string;
  payload?: any;
  error?: any;
  token?: string;
}

export interface WebSocketCallbacks {
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onAuthSuccess?: (data: { sessionId: string; userId: string }) => void;
  onAuthError?: (error: string) => void;
  onPrompt?: (data: { prompt: string; sessionId: string }) => void;
  onResponse?: (data: { payload: any; sessionId: string }) => void;
}

export interface QueuedMessage {
  message: WebSocketMessage;
  timestamp: number;
  resolve?: (value: void) => void;
  reject?: (reason: any) => void;
}