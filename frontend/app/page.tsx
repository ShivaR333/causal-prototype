'use client'

import { useState, useEffect, useRef } from 'react'
import { ChatMessage } from '../src/components/ChatMessage'
import { MessageInput } from '../src/components/MessageInput'
import { AgentStatusPanel } from '../src/components/AgentStatusPanel'
import { wsClient } from '../src/lib/websocket'
import { createNaturalLanguageQuery } from '../src/lib/api'
import { useWebSocketAuth } from '../src/hooks/useWebSocketAuth'
import { AuthState } from '../src/types/websocket'

export interface Message {
  id: string
  type: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  data?: any
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'system',
      content: 'Welcome to the Causal Analysis Agent! 🤖\n\nConnecting to WebSocket Gateway...',
      timestamp: new Date()
    }
  ])
  const [isLoading, setIsLoading] = useState(false)
  const [agentState, setAgentState] = useState<string>('initial')
  const [requiresConfirmation, setRequiresConfirmation] = useState(false)
  
  // Use auth hook for WebSocket management
  const {
    authStatus,
    isConnected,
    isAuthenticated,
    isConnecting,
    isAuthenticating,
    connect,
    authenticate,
    reset,
    canSendMessages,
    connectionStatus
  } = useWebSocketAuth()

  // Track message counter
  const messageCounterRef = useRef(0)

  const addMessage = (message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage: Message = {
      ...message,
      id: `${Date.now()}-${++messageCounterRef.current}`,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, newMessage])
  }

  // Initialize WebSocket connection and authentication
  useEffect(() => {
    let mounted = true;

    const initializeWebSocket = async () => {
      try {
        // Set up WebSocket callbacks for UI updates
        wsClient.setCallbacks({
          onConnect: () => {
            if (mounted) {
              addMessage({
                type: 'system',
                content: '✅ Connected to WebSocket Gateway at localhost:8080\n\nAuthenticating...'
              })
            }
          },
          onDisconnect: () => {
            if (mounted) {
              addMessage({
                type: 'system',
                content: '❌ Disconnected from WebSocket Gateway'
              })
            }
          },
          onAuthSuccess: (data) => {
            if (mounted) {
              addMessage({
                type: 'system',
                content: '🔐 Authentication successful! Ready for causal analysis.\n\nI can help you analyze causal relationships in your data. Try asking questions like:\n• "What\'s the effect of discount on sales?"\n• "How does education impact income?"\n• "Analyze the impact of advertising on customer behavior"'
              })
            }
          },
          onAuthError: (error) => {
            if (mounted) {
              addMessage({
                type: 'system',
                content: `❌ Authentication failed: ${error}`
              })
            }
          },
          onResponse: (data) => {
            if (mounted) {
              setAgentState((data as any).state || 'ready')
              setRequiresConfirmation((data as any).requires_confirmation || false)
              addMessage({
                type: 'assistant',
                content: data.payload?.response || 'Analysis complete',
                data: data.payload
              })
              setIsLoading(false)
            }
          },
          onError: (error) => {
            if (mounted) {
              addMessage({
                type: 'system',
                content: `❌ WebSocket error: ${error}`
              })
              setIsLoading(false)
            }
          }
        })

        // Connect and authenticate
        await connect()
        await authenticate()
      } catch (error) {
        if (mounted) {
          addMessage({
            type: 'system',
            content: `❌ Failed to initialize: ${error instanceof Error ? error.message : 'Unknown error'}`
          })
        }
      }
    }

    initializeWebSocket()

    // Cleanup
    return () => {
      mounted = false;
    }
  }, [connect, authenticate])

  const handleSendMessage = async (content: string) => {
    // Don't allow sending if not authenticated
    if (!canSendMessages) {
      addMessage({
        type: 'system',
        content: '⚠️ Please wait for authentication to complete before sending messages.'
      })
      return
    }

    addMessage({ type: 'user', content })
    setIsLoading(true)

    try {
      // Try to create a structured query from natural language
      const structuredQuery = createNaturalLanguageQuery(content)
      
      if (structuredQuery) {
        // Send structured causal analysis query
        await wsClient.sendQuery(structuredQuery, `msg-${Date.now()}`)
      } else {
        // Send as general agent message
        await wsClient.sendQuery({
          message: content,
          session_id: authStatus.sessionId
        }, `msg-${Date.now()}`)
      }
    } catch (error) {
      addMessage({
        type: 'system',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`
      })
      setIsLoading(false)
    }
  }

  const handleReset = async () => {
    try {
      setMessages([
        {
          id: '1',
          type: 'system',
          content: 'Session reset! Reconnecting to WebSocket Gateway...',
          timestamp: new Date()
        }
      ])
      setAgentState('initial')
      setRequiresConfirmation(false)
      
      // Reset connection and auth
      await reset()
    } catch (error) {
      addMessage({
        type: 'system',
        content: `Error resetting session: ${error instanceof Error ? error.message : 'Unknown error'}`
      })
    }
  }

  // Determine UI state
  const isInitializing = isConnecting || isAuthenticating
  const showLoadingOverlay = isInitializing && messages.length === 1
  
  // Generate status message
  const statusMessage = (() => {
    if (isConnecting) return '🟡 Connecting to WebSocket Gateway...'
    if (isAuthenticating) return '🟡 Authenticating...'
    if (isAuthenticated) return `🟢 Connected (Session: ${authStatus.sessionId?.slice(-8) || 'Unknown'})`
    if (authStatus.state === AuthState.ERROR) return `🔴 ${authStatus.error || 'Connection failed'}`
    return '🔴 Disconnected'
  })()

  return (
    <main className="flex min-h-screen flex-col bg-gray-50">
      <div className="flex-1 container mx-auto max-w-4xl p-4 flex flex-col">
        <div className="bg-white rounded-lg shadow-lg flex-1 flex flex-col">
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 rounded-t-lg">
            <h1 className="text-2xl font-bold mb-2">Causal Analysis Agent</h1>
            <p className="text-sm opacity-90">
              {statusMessage}
            </p>
            {authStatus.sessionId && isAuthenticated && (
              <p className="text-xs text-gray-200 mt-1">
                State: {agentState}
              </p>
            )}
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4 relative">
            {showLoadingOverlay && (
              <div className="absolute inset-0 bg-white bg-opacity-90 flex items-center justify-center">
                <div className="text-center">
                  <div className="flex justify-center mb-4">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                  </div>
                  <p className="text-gray-600">{connectionStatus}</p>
                </div>
              </div>
            )}
            
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-200 rounded-lg p-3 max-w-sm">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                    <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                  </div>
                </div>
              </div>
            )}
            <div className="h-4" />
          </div>

          <MessageInput 
            onSendMessage={handleSendMessage} 
            disabled={!canSendMessages || isLoading}
            placeholder={
              canSendMessages 
                ? "Type your causal analysis question..." 
                : isInitializing 
                  ? "Connecting..." 
                  : "Connection failed - please refresh"
            }
          />
        </div>

        <div className="mt-4 text-center">
          <button
            onClick={handleReset}
            className="text-sm text-gray-600 hover:text-gray-800 transition-colors"
            disabled={isInitializing}
          >
            Reset Session
          </button>
        </div>

        {agentState !== 'initial' && (
          <AgentStatusPanel
            isConnected={isConnected}
            sessionId={authStatus.sessionId}
            agentState={agentState}
            requiresConfirmation={requiresConfirmation}
            onReset={handleReset}
          />
        )}
      </div>
    </main>
  )
}