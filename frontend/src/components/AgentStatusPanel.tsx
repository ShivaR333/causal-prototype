'use client'

interface AgentStatusPanelProps {
  sessionId: string | null
  agentState: string
  requiresConfirmation: boolean
  onReset: () => void
  isConnected: boolean | null
}

export function AgentStatusPanel({ 
  sessionId, 
  agentState, 
  requiresConfirmation, 
  onReset, 
  isConnected 
}: AgentStatusPanelProps) {
  const getStateDescription = (state: string) => {
    switch (state) {
      case 'initial':
        return {
          label: 'Ready',
          description: 'Waiting for your causal analysis question',
          color: 'bg-blue-100 text-blue-800'
        }
      case 'dag_proposed':
        return {
          label: 'DAG Proposed',
          description: 'Agent has proposed a DAG and dataset configuration',
          color: 'bg-yellow-100 text-yellow-800'
        }
      case 'eda_completed':
        return {
          label: 'EDA Complete',
          description: 'Exploratory data analysis completed, reviewing results',
          color: 'bg-purple-100 text-purple-800'
        }
      case 'analysis_plan_proposed':
        return {
          label: 'Analysis Plan',
          description: 'Agent has proposed a causal analysis plan',
          color: 'bg-orange-100 text-orange-800'
        }
      case 'causal_analysis_completed':
        return {
          label: 'Analysis Complete',
          description: 'Causal analysis completed, results available',
          color: 'bg-green-100 text-green-800'
        }
      case 'completed':
        return {
          label: 'Complete',
          description: 'Analysis fully completed',
          color: 'bg-green-100 text-green-800'
        }
      default:
        return {
          label: 'Unknown',
          description: 'Unknown state',
          color: 'bg-gray-100 text-gray-800'
        }
    }
  }

  const stateInfo = getStateDescription(agentState)

  return (
    <div className="w-80 bg-white border-l border-gray-200 p-4 overflow-y-auto">
      <div className="space-y-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            Agent Status
          </h2>
          
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Connection
              </label>
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  isConnected === null ? 'bg-yellow-400' :
                  isConnected ? 'bg-green-400' : 'bg-red-400'
                }`} />
                <span className="text-sm text-gray-600">
                  {isConnected === null ? 'Checking...' :
                   isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>

            {sessionId && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Session ID
                </label>
                <div className="text-xs text-gray-500 font-mono bg-gray-50 p-2 rounded">
                  {sessionId.slice(-12)}...
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Current State
              </label>
              <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${stateInfo.color}`}>
                {stateInfo.label}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {stateInfo.description}
              </p>
            </div>

            {requiresConfirmation && (
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-4 h-4 bg-yellow-400 rounded-full flex items-center justify-center">
                      <span className="text-white text-xs">!</span>
                    </div>
                  </div>
                  <div className="ml-2">
                    <p className="text-sm text-yellow-800 font-medium">
                      Confirmation Required
                    </p>
                    <p className="text-xs text-yellow-700">
                      Please respond to the agent's proposal
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-3">
            Workflow Steps
          </h3>
          <div className="space-y-2">
            {[
              { state: 'initial', label: '1. Ask Question' },
              { state: 'dag_proposed', label: '2. Review DAG Proposal' },
              { state: 'eda_completed', label: '3. Review EDA' },
              { state: 'analysis_plan_proposed', label: '4. Confirm Analysis Plan' },
              { state: 'causal_analysis_completed', label: '5. Review Results' },
              { state: 'completed', label: '6. Complete' }
            ].map((step, index) => {
              const isActive = agentState === step.state
              const isCompleted = ['dag_proposed', 'eda_completed', 'analysis_plan_proposed', 'causal_analysis_completed', 'completed'].indexOf(agentState) > ['dag_proposed', 'eda_completed', 'analysis_plan_proposed', 'causal_analysis_completed', 'completed'].indexOf(step.state)
              
              return (
                <div key={step.state} className="flex items-center space-x-2">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${
                    isActive ? 'bg-blue-500 text-white' :
                    isCompleted ? 'bg-green-500 text-white' :
                    'bg-gray-200 text-gray-600'
                  }`}>
                    {isCompleted ? '✓' : index + 1}
                  </div>
                  <span className={`text-sm ${
                    isActive ? 'text-blue-600 font-medium' :
                    isCompleted ? 'text-green-600' :
                    'text-gray-500'
                  }`}>
                    {step.label}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-3">
            Actions
          </h3>
          <button
            onClick={onReset}
            disabled={!sessionId}
            className="w-full bg-red-500 text-white py-2 px-4 rounded-md hover:bg-red-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm"
          >
            Reset Session
          </button>
        </div>

        <div className="text-xs text-gray-500 space-y-2">
          <h3 className="font-medium">How it works:</h3>
          <ul className="space-y-1 list-disc list-inside">
            <li>Ask your causal analysis question in natural language</li>
            <li>Agent will propose a DAG and dataset</li>
            <li>Review and confirm the setup</li>
            <li>Agent runs EDA and proposes analysis plan</li>
            <li>Confirm to run the causal analysis</li>
            <li>Get interpreted results and insights</li>
          </ul>
        </div>
      </div>
    </div>
  )
}