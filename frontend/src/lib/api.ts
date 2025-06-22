const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface CausalQueryRequest {
  query: {
    query_type: string
    treatment_variable: string
    outcome_variable: string
    confounders: string[]
    treatment_value?: number
  }
  dag_file: string
  data_file: string
}

export interface CausalQueryResponse {
  success: boolean
  estimate?: number
  confidence_interval?: [number, number]
  summary?: string
  error?: string
  query_type?: string
  results?: any
}

export class CausalAnalysisAPI {
  private baseURL: string

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL
  }

  async healthCheck(): Promise<{ message: string; version: string }> {
    const response = await fetch(`${this.baseURL}/`)
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`)
    }
    return response.json()
  }

  async executeQuery(request: CausalQueryRequest): Promise<CausalQueryResponse> {
    try {
      const response = await fetch(`${this.baseURL}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })

      if (!response.ok) {
        throw new Error(`API request failed: ${response.statusText}`)
      }

      const data = await response.json()
      return data
    } catch (error) {
      console.error('API Error:', error)
      throw error
    }
  }

  async executeLegacyQuery(query: {
    treatment_variable: string
    outcome_variable: string
    confounders: string[]
    treatment_value?: number
    dag_file?: string
    data_file: string
  }): Promise<CausalQueryResponse> {
    try {
      const response = await fetch(`${this.baseURL}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(query),
      })

      if (!response.ok) {
        throw new Error(`API request failed: ${response.statusText}`)
      }

      const data = await response.json()
      return data
    } catch (error) {
      console.error('API Error:', error)
      throw error
    }
  }

  async checkConnection(): Promise<boolean> {
    try {
      await this.healthCheck()
      return true
    } catch {
      return false
    }
  }
}

// Create a singleton instance
export const causalAPI = new CausalAnalysisAPI()

// Helper function to format API responses for chat
export function formatCausalResponse(response: CausalQueryResponse): string {
  if (!response.success) {
    return `❌ Analysis failed: ${response.error || 'Unknown error'}`
  }

  let message = `✅ **Causal Analysis Complete**\n\n`
  
  if (response.estimate !== undefined) {
    message += `**Estimated Effect:** ${response.estimate.toFixed(4)}\n`
  }
  
  if (response.confidence_interval) {
    message += `**95% Confidence Interval:** [${response.confidence_interval[0].toFixed(4)}, ${response.confidence_interval[1].toFixed(4)}]\n`
  }
  
  if (response.summary) {
    message += `\n**Summary:** ${response.summary}\n`
  }
  
  if (response.query_type) {
    message += `\n**Analysis Type:** ${response.query_type}\n`
  }

  return message
}

// Helper function to create natural language queries
export function createNaturalLanguageQuery(
  userMessage: string,
  defaultDataFile: string = 'sample_data/eCommerce_sales.csv'
): CausalQueryRequest | null {
  // Simple pattern matching for natural language queries
  const treatmentRegex = /effect of (\w+)/i
  const outcomeRegex = /on (\w+)/i
  const confoundersRegex = /controlling for (.+)/i

  const treatmentMatch = userMessage.match(treatmentRegex)
  const outcomeMatch = userMessage.match(outcomeRegex)
  const confoundersMatch = userMessage.match(confoundersRegex)

  if (treatmentMatch && outcomeMatch) {
    const confounders = confoundersMatch
      ? confoundersMatch[1].split(/,|\sand\s/).map(s => s.trim())
      : []

    return {
      query: {
        query_type: 'effect_estimation',
        treatment_variable: treatmentMatch[1],
        outcome_variable: outcomeMatch[1],
        confounders
      },
      dag_file: 'causal_analysis/config/sample_dag.json',
      data_file: defaultDataFile
    }
  }

  return null
}