'use client'

import { useState, useEffect } from 'react'
import { ChatMessage } from '@/components/ChatMessage'
import { MessageInput } from '@/components/MessageInput'
import { CausalForm } from '@/components/CausalForm'
import AuthForm from '@/components/AuthForm'
import { causalAPI, formatCausalResponse, createNaturalLanguageQuery, CausalQueryRequest } from '@/lib/api'
import { wsClient } from '@/lib/websocket'
import { authService } from '@/lib/auth'

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
      content: 'Welcome to the Causal Analysis Agent! Please sign in to start analyzing causal relationships in your data.',
      timestamp: new Date()
    }
  ])
  const [isLoading, setIsLoading] = useState(false)
  const [isConnected, setIsConnected] = useState<boolean | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [pendingPrompt, setPendingPrompt] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)

  // Initialize authentication and WebSocket
  useEffect(() => {
    // Check if user is already authenticated
    if (authService.isAuthenticated()) {
      handleAuthSuccess()
    }
  }, [])

  const handleAuthSuccess = async () => {
    setIsAuthenticated(true)
    
    try {
      // Connect to WebSocket
      await wsClient.connect()
      
      // Set up WebSocket callbacks
      wsClient.setCallbacks({
        onConnect: () => {
          setIsConnected(true)
          addMessage({
            type: 'system',
            content: '🔌 Connected to WebSocket Gateway'
          })
        },
        onDisconnect: () => {
          setIsConnected(false)
          addMessage({
            type: 'system',
            content: '🔌 Disconnected from WebSocket Gateway'
          })
        },
        onAuthSuccess: (data) => {
          setSessionId(data.sessionId)
          addMessage({
            type: 'system',
            content: `✅ Authenticated! Session: ${data.sessionId}`
          })
          addMessage({
            type: 'system',
            content: 'I can help you analyze causal relationships in your data. Ask me questions like "What\'s the effect of discount on sales?" or use the form on the right.'
          })
        },
        onPrompt: (data) => {
          setPendingPrompt(data.prompt)
          addMessage({
            type: 'assistant',
            content: `🤔 I need clarification: ${data.prompt}`
          })
        },
        onResponse: (data) => {
          setPendingPrompt(null)
          addMessage({
            type: 'assistant',
            content: data.payload.content,
            data: data.payload
          })
        },
        onError: (error) => {
          addMessage({
            type: 'system',
            content: `❌ Error: ${error}`
          })
        }
      })
      
      // Authenticate with WebSocket
      const user = authService.getCurrentUser()
      if (user) {
        wsClient.authenticate(user.accessToken)
      }
      
    } catch (error) {
      console.error('WebSocket connection failed:', error)
      addMessage({
        type: 'system',
        content: '❌ Failed to connect to WebSocket Gateway. Falling back to REST API.'
      })
      
      // Fallback to REST API
      const connected = await causalAPI.checkConnection()
      setIsConnected(connected)
    }
  }

  const handleLogout = async () => {
    await authService.logout()
    wsClient.disconnect()
    setIsAuthenticated(false)
    setIsConnected(null)
    setSessionId(null)
    setPendingPrompt(null)
    setMessages([{
      id: '1',
      type: 'system',
      content: 'You have been logged out. Please sign in to continue.',
      timestamp: new Date()
    }])
  }

  const addMessage = (message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage: Message = {
      ...message,
      id: Date.now().toString(),
      timestamp: new Date()
    }
    setMessages(prev => [...prev, newMessage])
  }

  const handleSendMessage = async (content: string) => {
    addMessage({ type: 'user', content })
    setIsLoading(true)

    try {
      if (wsClient.isConnected() && wsClient.isAuthenticated()) {
        // Use WebSocket for real-time communication
        const query = {
          type: 'natural_language',
          content: content
        }
        wsClient.sendQuery(query)
      } else {
        // Fallback to REST API
        const naturalQuery = createNaturalLanguageQuery(content)
        
        if (naturalQuery) {
          addMessage({
            type: 'system',
            content: `🔍 Detected causal query: analyzing effect of ${naturalQuery.query.treatment_variable} on ${naturalQuery.query.outcome_variable}`
          })
          
          const result = await causalAPI.executeQuery(naturalQuery)
          const formattedResponse = formatCausalResponse(result)
          
          addMessage({
            type: 'assistant',
            content: formattedResponse,
            data: result
          })
        } else {
          addMessage({
            type: 'assistant',
            content: `I understand you're asking: "${content}"\n\nI'm specifically designed for causal analysis. Try asking something like:\n• "What's the effect of discount on sales?"\n• "Analyze the impact of education on income"\n• Or use the form on the right to run a detailed analysis.`
          })
        }
      }
    } catch (error) {
      addMessage({
        type: 'system',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSendResponse = async (response: string) => {
    if (sessionId && pendingPrompt) {
      addMessage({ type: 'user', content: response })
      wsClient.sendResponse(response, sessionId)
      setPendingPrompt(null)
    }
  }

  const handleCausalQuery = async (queryData: CausalQueryRequest) => {
    addMessage({
      type: 'user',
      content: `Running causal analysis: ${queryData.query.treatment_variable} → ${queryData.query.outcome_variable}`
    })
    setIsLoading(true)

    try {
      const result = await causalAPI.executeQuery(queryData)
      const formattedResponse = formatCausalResponse(result)
      
      addMessage({
        type: 'assistant',
        content: formattedResponse,
        data: result
      })
    } catch (error) {
      addMessage({
        type: 'system',
        content: `Error running causal analysis: ${error instanceof Error ? error.message : 'Unknown error'}`
      })
    } finally {
      setIsLoading(false)
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-2xl w-full">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Causal Analysis Agent
            </h1>
            <p className="text-gray-600">
              Sign in to start analyzing causal relationships in your data
            </p>
          </div>
          <AuthForm onAuthSuccess={handleAuthSuccess} />
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-xl font-semibold text-gray-800">
                Causal Analysis Agent
              </h1>
              <p className="text-sm text-gray-600">
                {isConnected === null ? 'Checking connection...' : 
                 isConnected ? '🟢 Connected via WebSocket' : 
                 '🔴 Disconnected - using fallback API'}
                {sessionId && ` • Session: ${sessionId.slice(-8)}`}
              </p>
            </div>
            <button
              onClick={handleLogout}
              className="text-sm text-gray-600 hover:text-gray-800 bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded"
            >
              Sign Out
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
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
        </div>

        {/* Message Input */}
        <MessageInput 
          onSendMessage={handleSendMessage} 
          onSendResponse={handleSendResponse}
          disabled={isLoading || !isConnected}
          isPromptMode={!!pendingPrompt}
          promptText={pendingPrompt || undefined}
        />
      </div>

      {/* Sidebar with Causal Analysis Form */}
      <div className="w-96 bg-white border-l border-gray-200 p-4 overflow-y-auto">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          Causal Analysis
        </h2>
        <CausalForm onSubmit={handleCausalQuery} disabled={isLoading || !isConnected} />
      </div>
    </div>
  )
}