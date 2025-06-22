# Causal Analysis Agent

An OpenAI-powered agent that guides users through comprehensive causal analysis workflows, from data exploration to final interpretation.

## Features

The agent supports a structured 4-step workflow:

1. **DAG & Data Identification**: Analyzes user questions and proposes the most appropriate DAG structure and dataset
2. **Exploratory Data Analysis (EDA)**: Automatically runs comprehensive causal EDA and interprets results
3. **Analysis Plan Proposal**: Suggests optimal causal inference methodology based on EDA findings
4. **Causal Analysis & Interpretation**: Executes causal analysis and provides actionable insights

## Workflow States

- `INITIAL`: Ready to accept user questions
- `DAG_PROPOSED`: Waiting for user approval of proposed DAG/data configuration
- `EDA_COMPLETED`: EDA analysis finished, presenting results and analysis plan
- `ANALYSIS_PLAN_PROPOSED`: Waiting for user approval of proposed analysis methodology
- `CAUSAL_ANALYSIS_COMPLETED`: Final results ready, accepting follow-up questions

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Interactive Mode

Run the agent interactively:

```bash
python causal_agent.py
```

Example conversation:
```
You: I want to analyze the effect of an educational intervention on student performance

🤖 Agent: Based on your question, I propose the following analysis setup:

**DAG**: examples/simple_education_dag.json
**Dataset**: examples/education_data.csv
**Treatment Variable**: intervention
**Outcome Variable**: performance
**Query Type**: effect_estimation
**Confidence**: 85.0%

**Reasoning**: Your question involves analyzing the causal effect of an educational intervention on student performance, which matches the education DAG structure...

Does this setup look correct for your analysis?

You: yes, proceed

🤖 Agent: [Runs EDA analysis and presents results...]
```

### Programmatic Usage

```python
from causal_agent import CausalAnalysisAgent

# Initialize agent
agent = CausalAnalysisAgent()

# Process user question
response = agent.process_user_question("I want to analyze healthcare treatment effects")

# Continue conversation
response = agent.process_user_question("yes, proceed with this setup")

# Get current state
state = agent.get_state_info()
print(f"Current state: {state['state']}")
```

## Supported Query Types

1. **Effect Estimation**: Estimate the causal effect of treatment on outcome
2. **Anomaly Attribution**: Identify causes of anomalous outcomes
3. **Distribution Shift Attribution**: Analyze what drives changes in outcome distributions
4. **Intervention**: Simulate the effects of interventions
5. **Counterfactual**: Answer "what if" questions about alternative scenarios

## File Structure

The agent automatically discovers available resources:

- **DAG Library**: JSON files in `examples/` directory defining causal structures
- **Data Library**: CSV files in `sample_data/`, `examples/`, or current directory
- **EDA Output**: Generated in timestamped `agent_analysis_YYYYMMDD_HHMMSS/` directories

## DAG File Format

DAG files should follow this JSON structure:

```json
{
  "name": "example_dag",
  "description": "Description of the causal structure",
  "variables": {
    "treatment": {
      "name": "treatment",
      "type": "binary",
      "description": "Treatment variable"
    },
    "outcome": {
      "name": "outcome", 
      "type": "continuous",
      "description": "Outcome variable"
    }
  },
  "edges": [
    {"from": "treatment", "to": "outcome"}
  ],
  "treatment_variable": "treatment",
  "outcome_variable": "outcome",
  "confounders": ["age", "income"],
  "mediators": ["adherence"]
}
```

## Output Files

Each analysis generates:

- `causal_eda_report.txt`: Comprehensive EDA report
- `variable_inventory.csv`: Variable metadata and statistics
- `correlation_matrix.png`: Correlation heatmap
- `univariate_distributions.png`: Distribution plots
- `treatment_outcome_relationship.png`: Treatment-outcome relationship
- `propensity_score_overlap.png`: Propensity score analysis
- Additional plots based on data characteristics

## Advanced Features

### Custom Configuration

```python
# Use different OpenAI model
agent = CausalAnalysisAgent(model="gpt-3.5-turbo")

# Reset to start new analysis
agent.reset()

# Check current workflow state
state_info = agent.get_state_info()
```

### Error Handling

The agent includes robust error handling:
- Missing files are detected and reported
- OpenAI API errors are caught and displayed
- Invalid JSON responses are handled gracefully
- Analysis failures provide debugging information

## Commands

When running interactively:

- `quit` or `exit`: Exit the agent
- `reset`: Start a new analysis (clears current state)
- `status`: Show current workflow state and progress

## Examples

See `example_agent_usage.py` for a complete programmatic example.

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**
   ```
   Error: OpenAI API key not found
   Solution: Set OPENAI_API_KEY environment variable
   ```

2. **File Not Found**
   ```
   Error: DAG file not found at examples/my_dag.json
   Solution: Ensure DAG and data files exist in expected directories
   ```

3. **EDA Analysis Fails**
   ```
   Error: EDA execution failed
   Solution: Check data file format and ensure all required columns exist
   ```

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

agent = CausalAnalysisAgent()
```

## Architecture

The agent uses a state machine pattern with the following components:

- **CausalAnalysisAgent**: Main agent class managing workflow state
- **WorkflowState**: Enum defining possible states
- **DAGProposal**: Data structure for DAG/data proposals
- **AnalysisPlan**: Data structure for analysis methodology
- **CausalEDA**: EDA analysis engine (from existing codebase)
- **dispatch_query**: Causal analysis engine (from existing codebase)

## Contributing

To extend the agent:

1. Add new query types in `dispatch_query` function
2. Extend `WorkflowState` enum for new workflow steps
3. Add new DAG files to `examples/` directory
4. Add new datasets to `sample_data/` directory

## License

[Add your license information here]