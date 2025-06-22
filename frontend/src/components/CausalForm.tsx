'use client'

import { useState } from 'react'

interface CausalFormProps {
  onSubmit: (data: any) => void
  disabled?: boolean
}

export function CausalForm({ onSubmit, disabled }: CausalFormProps) {
  const [formData, setFormData] = useState({
    query_type: 'effect_estimation',
    treatment_variable: '',
    outcome_variable: '',
    confounders: '',
    data_file: 'sample_data/eCommerce_sales.csv',
    dag_file: 'causal_analysis/config/sample_dag.json'
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    const queryData = {
      query: {
        query_type: formData.query_type,
        treatment_variable: formData.treatment_variable,
        outcome_variable: formData.outcome_variable,
        confounders: formData.confounders.split(',').map(s => s.trim()).filter(s => s)
      },
      data_file: formData.data_file,
      dag_file: formData.dag_file
    }
    
    onSubmit(queryData)
  }

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Query Type
        </label>
        <select
          value={formData.query_type}
          onChange={(e) => handleChange('query_type', e.target.value)}
          className="w-full border border-gray-300 rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={disabled}
        >
          <option value="effect_estimation">Effect Estimation</option>
          <option value="discovery">Discovery</option>
          <option value="refutation">Refutation</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Treatment Variable
        </label>
        <input
          type="text"
          value={formData.treatment_variable}
          onChange={(e) => handleChange('treatment_variable', e.target.value)}
          placeholder="e.g., discount"
          className="w-full border border-gray-300 rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={disabled}
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Outcome Variable
        </label>
        <input
          type="text"
          value={formData.outcome_variable}
          onChange={(e) => handleChange('outcome_variable', e.target.value)}
          placeholder="e.g., sales"
          className="w-full border border-gray-300 rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={disabled}
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Confounders (comma-separated)
        </label>
        <input
          type="text"
          value={formData.confounders}
          onChange={(e) => handleChange('confounders', e.target.value)}
          placeholder="e.g., customer_segment, season"
          className="w-full border border-gray-300 rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={disabled}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Data File
        </label>
        <select
          value={formData.data_file}
          onChange={(e) => handleChange('data_file', e.target.value)}
          className="w-full border border-gray-300 rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={disabled}
        >
          <option value="sample_data/eCommerce_sales.csv">eCommerce Sales</option>
          <option value="sample_data/small_effect.csv">Small Effect</option>
          <option value="sample_data/medium_effect.csv">Medium Effect</option>
          <option value="sample_data/large_effect.csv">Large Effect</option>
        </select>
      </div>

      <button
        type="submit"
        disabled={disabled || !formData.treatment_variable || !formData.outcome_variable}
        className="w-full bg-green-500 text-white py-2 px-4 rounded-md hover:bg-green-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
      >
        Run Analysis
      </button>

      <div className="text-xs text-gray-500 mt-2">
        <p><strong>Examples:</strong></p>
        <p>• Treatment: discount, Outcome: sales</p>
        <p>• Treatment: education, Outcome: income</p>
        <p>• Confounders: age, gender, location</p>
      </div>
    </form>
  )
}