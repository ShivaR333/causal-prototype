'use client'

import { useState, KeyboardEvent } from 'react'

interface MessageInputProps {
  onSendMessage: (message: string) => void
  onSendResponse?: (response: string) => void
  disabled?: boolean
  placeholder?: string
  isPromptMode?: boolean
  promptText?: string
}

export function MessageInput({ 
  onSendMessage, 
  onSendResponse,
  disabled, 
  placeholder = "Ask me about causal analysis...", 
  isPromptMode = false,
  promptText
}: MessageInputProps) {
  const [message, setMessage] = useState('')

  const handleSend = () => {
    if (message.trim() && !disabled) {
      if (isPromptMode && onSendResponse) {
        onSendResponse(message.trim())
      } else {
        onSendMessage(message.trim())
      }
      setMessage('')
    }
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const displayPlaceholder = isPromptMode 
    ? `Respond to: ${promptText}` 
    : placeholder

  return (
    <div className="border-t border-gray-200 p-4 bg-white">
      {isPromptMode && promptText && (
        <div className="mb-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            <strong>Agent needs clarification:</strong> {promptText}
          </p>
        </div>
      )}
      
      <div className="flex space-x-2">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={displayPlaceholder}
          className="flex-1 border border-gray-300 rounded-lg p-2 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={isPromptMode ? 3 : 2}
          disabled={disabled}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !message.trim()}
          className={`px-4 py-2 rounded-lg disabled:bg-gray-300 disabled:cursor-not-allowed ${
            isPromptMode 
              ? 'bg-yellow-500 text-white hover:bg-yellow-600' 
              : 'bg-blue-500 text-white hover:bg-blue-600'
          }`}
        >
          {isPromptMode ? 'Respond' : 'Send'}
        </button>
      </div>
    </div>
  )
}