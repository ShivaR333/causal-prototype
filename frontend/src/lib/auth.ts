import { CognitoUserPool, CognitoUser, AuthenticationDetails, CognitoUserSession, CognitoUserAttribute } from 'amazon-cognito-identity-js';

// Cognito configuration
const poolData = {
  UserPoolId: process.env.NEXT_PUBLIC_USER_POOL_ID || '',
  ClientId: process.env.NEXT_PUBLIC_USER_POOL_CLIENT_ID || ''
};

// Check if we have valid Cognito configuration
const hasValidCognitoConfig = poolData.UserPoolId && poolData.ClientId && 
  poolData.UserPoolId !== '' && poolData.ClientId !== '';

if (!hasValidCognitoConfig) {
  console.warn('Cognito configuration missing. Please set NEXT_PUBLIC_USER_POOL_ID and NEXT_PUBLIC_USER_POOL_CLIENT_ID');
}

// Only create UserPool if we have valid configuration
const userPool = hasValidCognitoConfig ? 
  new CognitoUserPool(poolData) : null;

export interface AuthUser {
  username: string;
  email: string;
  accessToken: string;
  idToken: string;
  refreshToken: string;
  tokenExpiration: number;
}

export interface SignUpResult {
  success: boolean;
  message: string;
  needsConfirmation?: boolean;
}

export interface SignInResult {
  success: boolean;
  user?: AuthUser;
  message: string;
  needsNewPassword?: boolean;
}

class AuthService {
  private currentUser: AuthUser | null = null;
  private refreshTimer: NodeJS.Timeout | null = null;

  constructor() {
    // Check for existing session on initialization
    this.checkExistingSession();
  }

  private checkExistingSession(): void {
    if (!userPool) return;
    
    const cognitoUser = userPool.getCurrentUser();
    if (cognitoUser) {
      cognitoUser.getSession((err: any, session: CognitoUserSession) => {
        if (!err && session.isValid()) {
          this.setCurrentUser(cognitoUser, session);
        }
      });
    }
  }

  private setCurrentUser(cognitoUser: CognitoUser, session: CognitoUserSession): void {
    const accessToken = session.getAccessToken();
    const idToken = session.getIdToken();
    const refreshToken = session.getRefreshToken();

    this.currentUser = {
      username: cognitoUser.getUsername(),
      email: idToken.payload.email || '',
      accessToken: accessToken.getJwtToken(),
      idToken: idToken.getJwtToken(),
      refreshToken: refreshToken.getToken(),
      tokenExpiration: accessToken.payload.exp * 1000 // Convert to milliseconds
    };

    // Set up auto-refresh
    this.setupTokenRefresh();
  }

  private setupTokenRefresh(): void {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }

    if (this.currentUser) {
      const timeUntilRefresh = this.currentUser.tokenExpiration - Date.now() - (5 * 60 * 1000); // Refresh 5 mins before expiry
      
      if (timeUntilRefresh > 0) {
        this.refreshTimer = setTimeout(() => {
          this.refreshTokens();
        }, timeUntilRefresh);
      }
    }
  }

  private async refreshTokens(): Promise<void> {
    if (!userPool) return;
    
    const cognitoUser = userPool.getCurrentUser();
    if (!cognitoUser) return;

    return new Promise((resolve, reject) => {
      cognitoUser.getSession((err: any, session: CognitoUserSession) => {
        if (err) {
          console.error('Token refresh failed:', err);
          this.signOut();
          reject(err);
          return;
        }

        if (session.isValid()) {
          this.setCurrentUser(cognitoUser, session);
          resolve();
        } else {
          this.signOut();
          reject(new Error('Session is no longer valid'));
        }
      });
    });
  }

  async signUp(email: string, password: string, username?: string): Promise<SignUpResult> {
    if (!userPool) {
      return {
        success: false,
        message: 'Cognito not configured. Please check environment variables.'
      };
    }
    
    return new Promise((resolve) => {
      const attributeList = [
        new CognitoUserAttribute({
          Name: 'email',
          Value: email
        })
      ];

      userPool.signUp(
        username || email,
        password,
        attributeList,
        [],
        (err, result) => {
          if (err) {
            console.error('Sign up error:', err);
            resolve({
              success: false,
              message: err.message || 'Sign up failed'
            });
            return;
          }

          resolve({
            success: true,
            message: 'Sign up successful',
            needsConfirmation: result?.userConfirmed === false
          });
        }
      );
    });
  }

  async confirmSignUp(username: string, code: string): Promise<{ success: boolean; message: string }> {
    if (!userPool) {
      return {
        success: false,
        message: 'Cognito not configured. Please check environment variables.'
      };
    }
    
    return new Promise((resolve) => {
      const cognitoUser = new CognitoUser({
        Username: username,
        Pool: userPool
      });

      cognitoUser.confirmRegistration(code, true, (err) => {
        if (err) {
          console.error('Confirmation error:', err);
          resolve({
            success: false,
            message: err.message || 'Confirmation failed'
          });
          return;
        }

        resolve({
          success: true,
          message: 'Account confirmed successfully'
        });
      });
    });
  }

  async signIn(username: string, password: string): Promise<SignInResult> {
    if (!userPool) {
      return {
        success: false,
        message: 'Cognito not configured. Please check environment variables.'
      };
    }
    
    return new Promise((resolve) => {
      const authenticationDetails = new AuthenticationDetails({
        Username: username,
        Password: password
      });

      const cognitoUser = new CognitoUser({
        Username: username,
        Pool: userPool
      });

      cognitoUser.authenticateUser(authenticationDetails, {
        onSuccess: (session: CognitoUserSession) => {
          this.setCurrentUser(cognitoUser, session);
          
          resolve({
            success: true,
            user: this.currentUser!,
            message: 'Sign in successful'
          });
        },
        
        onFailure: (err) => {
          console.error('Sign in error:', err);
          resolve({
            success: false,
            message: err.message || 'Sign in failed'
          });
        },

        newPasswordRequired: (userAttributes, requiredAttributes) => {
          resolve({
            success: false,
            message: 'New password required',
            needsNewPassword: true
          });
        }
      });
    });
  }

  async signOut(): Promise<void> {
    if (!userPool) return;
    
    const cognitoUser = userPool.getCurrentUser();
    if (cognitoUser) {
      cognitoUser.signOut();
    }
    
    this.currentUser = null;
    
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
  }

  async forgotPassword(username: string): Promise<{ success: boolean; message: string }> {
    if (!userPool) {
      return {
        success: false,
        message: 'Cognito not configured. Please check environment variables.'
      };
    }
    
    return new Promise((resolve) => {
      const cognitoUser = new CognitoUser({
        Username: username,
        Pool: userPool
      });

      cognitoUser.forgotPassword({
        onSuccess: () => {
          resolve({
            success: true,
            message: 'Password reset code sent to your email'
          });
        },
        onFailure: (err) => {
          console.error('Forgot password error:', err);
          resolve({
            success: false,
            message: err.message || 'Failed to send reset code'
          });
        }
      });
    });
  }

  async resetPassword(username: string, code: string, newPassword: string): Promise<{ success: boolean; message: string }> {
    if (!userPool) {
      return {
        success: false,
        message: 'Cognito not configured. Please check environment variables.'
      };
    }
    
    return new Promise((resolve) => {
      const cognitoUser = new CognitoUser({
        Username: username,
        Pool: userPool
      });

      cognitoUser.confirmPassword(code, newPassword, {
        onSuccess: () => {
          resolve({
            success: true,
            message: 'Password reset successful'
          });
        },
        onFailure: (err) => {
          console.error('Reset password error:', err);
          resolve({
            success: false,
            message: err.message || 'Password reset failed'
          });
        }
      });
    });
  }

  getCurrentUser(): AuthUser | null {
    return this.currentUser;
  }

  isAuthenticated(): boolean {
    return this.currentUser !== null && this.currentUser.tokenExpiration > Date.now();
  }

  getAccessToken(): string | null {
    if (this.isAuthenticated()) {
      return this.currentUser!.accessToken;
    }
    return null;
  }

  getIdToken(): string | null {
    if (this.isAuthenticated()) {
      return this.currentUser!.idToken;
    }
    return null;
  }
}

// Export singleton instance
export const authService = new AuthService();