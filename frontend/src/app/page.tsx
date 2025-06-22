'use client'

import { useState, useEffect } from 'react'
import { ChatMessage } from '@/components/ChatMessage'
import { MessageInput } from '@/components/MessageInput'
import { CausalForm } from '@/components/CausalForm'
import { causalAPI, formatCausalResponse, createNaturalLanguageQuery, CausalQueryRequest } from '@/lib/api'

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
      content: 'Welcome to the Causal Analysis Agent! I can help you analyze causal relationships in your data. You can either ask me questions directly or use the form below to run specific analyses.',
      timestamp: new Date()
    }
  ])
  const [isLoading, setIsLoading] = useState(false)
  const [isConnected, setIsConnected] = useState<boolean | null>(null)

  // Check API connection on component mount
  useEffect(() => {
    const checkConnection = async () => {
      const connected = await causalAPI.checkConnection()
      setIsConnected(connected)
      if (connected) {
        addMessage({
          type: 'system',
          content: '✅ Connected to Causal Analysis API at localhost:8000'
        })
      } else {
        addMessage({
          type: 'system',
          content: '❌ Cannot connect to API. Please ensure Docker container is running on port 8000.'
        })
      }
    }
    checkConnection()
  }, [])

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
      // Try to parse as natural language query
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
        // General response for non-causal queries
        addMessage({
          type: 'assistant',
          content: `I understand you're asking: "${content}"\n\nI'm specifically designed for causal analysis. Try asking something like:\n• "What's the effect of discount on sales?"\n• "Analyze the impact of education on income"\n• Or use the form on the right to run a detailed analysis.`
        })
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

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 p-4">
          <h1 className="text-xl font-semibold text-gray-800">
            Causal Analysis Agent
          </h1>
          <p className="text-sm text-gray-600">
            {isConnected === null ? 'Checking connection...' : 
             isConnected ? '🟢 Connected to API at localhost:8000' : 
             '🔴 Disconnected from API at localhost:8000'}
          </p>
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
        <MessageInput onSendMessage={handleSendMessage} disabled={isLoading} />
      </div>

      {/* Sidebar with Causal Analysis Form */}
      <div className="w-96 bg-white border-l border-gray-200 p-4 overflow-y-auto">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          Causal Analysis
        </h2>
        <CausalForm onSubmit={handleCausalQuery} disabled={isLoading} />
      </div>
    </div>
  )
}