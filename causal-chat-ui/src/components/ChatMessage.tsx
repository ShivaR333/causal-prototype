import { Message } from '@/app/page'

interface ChatMessageProps {
  message: Message
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.type === 'user'
  const isSystem = message.type === 'system'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-sm lg:max-w-md xl:max-w-lg rounded-lg p-3 ${
          isUser
            ? 'bg-blue-500 text-white'
            : isSystem
            ? 'bg-yellow-100 text-yellow-800 border border-yellow-200'
            : 'bg-gray-200 text-gray-800'
        }`}
      >
        <div className="text-sm">{message.content}</div>
        {message.data && (
          <div className="mt-2 p-2 bg-black bg-opacity-10 rounded text-xs">
            <pre className="whitespace-pre-wrap">
              {JSON.stringify(message.data, null, 2)}
            </pre>
          </div>
        )}
        <div className={`text-xs mt-1 ${isUser ? 'text-blue-100' : 'text-gray-500'}`}>
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}