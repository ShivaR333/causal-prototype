interface CognitoConfig {
  userPoolId: string;
  clientId: string;
  region: string;
  endpoint?: string;
}

interface AuthUser {
  userId: string;
  email: string;
  accessToken: string;
  idToken: string;
  refreshToken: string;
}

interface LoginCredentials {
  email: string;
  password: string;
}

interface SignupData {
  email: string;
  password: string;
  name?: string;
}

export class AuthService {
  private config: CognitoConfig;
  private currentUser: AuthUser | null = null;

  constructor(config: CognitoConfig) {
    this.config = config;
    this.loadUserFromStorage();
  }

  private async makeRequest(endpoint: string, body: any) {
    const baseUrl = this.config.endpoint || `https://cognito-idp.${this.config.region}.amazonaws.com`;
    
    const response = await fetch(`${baseUrl}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-amz-json-1.1',
        'X-Amz-Target': `AWSCognitoIdentityProviderService.${endpoint}`,
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Authentication request failed');
    }

    return response.json();
  }

  async login(credentials: LoginCredentials): Promise<AuthUser> {
    try {
      // For local development, use simplified auth
      if (this.config.endpoint?.includes('localhost') || process.env.NODE_ENV === 'development') {
        return this.mockLogin(credentials);
      }

      // Real Cognito authentication
      const response = await this.makeRequest('InitiateAuth', {
        AuthFlow: 'USER_PASSWORD_AUTH',
        ClientId: this.config.clientId,
        AuthParameters: {
          USERNAME: credentials.email,
          PASSWORD: credentials.password,
        },
      });

      const user: AuthUser = {
        userId: response.AuthenticationResult.AccessToken.split('.')[1], // Simplified user ID
        email: credentials.email,
        accessToken: response.AuthenticationResult.AccessToken,
        idToken: response.AuthenticationResult.IdToken,
        refreshToken: response.AuthenticationResult.RefreshToken,
      };

      this.currentUser = user;
      this.saveUserToStorage(user);
      
      return user;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  }

  async signup(data: SignupData): Promise<void> {
    try {
      // For local development, just simulate success
      if (this.config.endpoint?.includes('localhost') || process.env.NODE_ENV === 'development') {
        console.log('Mock signup for:', data.email);
        return;
      }

      await this.makeRequest('SignUp', {
        ClientId: this.config.clientId,
        Username: data.email,
        Password: data.password,
        UserAttributes: [
          {
            Name: 'email',
            Value: data.email,
          },
          ...(data.name ? [{
            Name: 'name',
            Value: data.name,
          }] : []),
        ],
      });
    } catch (error) {
      console.error('Signup failed:', error);
      throw error;
    }
  }

  async logout(): Promise<void> {
    try {
      if (this.currentUser && !this.config.endpoint?.includes('localhost')) {
        await this.makeRequest('GlobalSignOut', {
          AccessToken: this.currentUser.accessToken,
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      this.currentUser = null;
      this.clearUserFromStorage();
    }
  }

  async refreshTokens(): Promise<AuthUser> {
    if (!this.currentUser?.refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      // For local development, return current user
      if (this.config.endpoint?.includes('localhost') || process.env.NODE_ENV === 'development') {
        return this.currentUser;
      }

      const response = await this.makeRequest('InitiateAuth', {
        AuthFlow: 'REFRESH_TOKEN_AUTH',
        ClientId: this.config.clientId,
        AuthParameters: {
          REFRESH_TOKEN: this.currentUser.refreshToken,
        },
      });

      const updatedUser: AuthUser = {
        ...this.currentUser,
        accessToken: response.AuthenticationResult.AccessToken,
        idToken: response.AuthenticationResult.IdToken,
      };

      this.currentUser = updatedUser;
      this.saveUserToStorage(updatedUser);
      
      return updatedUser;
    } catch (error) {
      console.error('Token refresh failed:', error);
      this.logout();
      throw error;
    }
  }

  private mockLogin(credentials: LoginCredentials): AuthUser {
    // Mock authentication for local development
    const mockUser: AuthUser = {
      userId: `local-${credentials.email}`,
      email: credentials.email,
      accessToken: `mock-access-token-${Date.now()}`,
      idToken: `mock-id-token-${Date.now()}`,
      refreshToken: `mock-refresh-token-${Date.now()}`,
    };

    this.currentUser = mockUser;
    this.saveUserToStorage(mockUser);
    
    return mockUser;
  }

  getCurrentUser(): AuthUser | null {
    return this.currentUser;
  }

  isAuthenticated(): boolean {
    return this.currentUser !== null;
  }

  getAccessToken(): string | null {
    return this.currentUser?.accessToken || null;
  }

  private saveUserToStorage(user: AuthUser): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_user', JSON.stringify(user));
    }
  }

  private loadUserFromStorage(): void {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('auth_user');
      if (stored) {
        try {
          this.currentUser = JSON.parse(stored);
        } catch (error) {
          console.error('Failed to parse stored user:', error);
          this.clearUserFromStorage();
        }
      }
    }
  }

  private clearUserFromStorage(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_user');
    }
  }
}

// Initialize auth service
const authConfig: CognitoConfig = {
  userPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID || 'local-pool',
  clientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID || 'local-client',
  region: process.env.NEXT_PUBLIC_AWS_REGION || 'us-east-1',
  endpoint: process.env.NEXT_PUBLIC_COGNITO_ENDPOINT || 'http://localhost:4566',
};

export const authService = new AuthService(authConfig);

// JWT token generation for local development WebSocket authentication
function base64UrlEncode(str: string): string {
  return btoa(str)
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

export function generateLocalDevToken(): string {
  const header = {
    typ: 'JWT',
    alg: 'HS256'
  };
  
  const payload = {
    userId: 'local-user',
    email: 'user@localhost',
    iat: Math.floor(Date.now() / 1000),
    exp: Math.floor(Date.now() / 1000) + (24 * 60 * 60) // 24 hours
  };
  
  const encodedHeader = base64UrlEncode(JSON.stringify(header));
  const encodedPayload = base64UrlEncode(JSON.stringify(payload));
  
  // For local development, create a simple token that the WebSocket gateway can verify
  // This should match the secret in LocalStack: 'local-dev-secret-key-12345'
  const signature = base64UrlEncode(`signature-${encodedHeader}-${encodedPayload}`);
  
  return `${encodedHeader}.${encodedPayload}.${signature}`;
}

export function isLocalDevelopment(): boolean {
  return process.env.NODE_ENV === 'development' || 
         process.env.NEXT_PUBLIC_API_URL?.includes('localhost');
}