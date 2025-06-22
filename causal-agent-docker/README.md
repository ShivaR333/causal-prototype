# Causal Analysis Agent - Docker

A containerized causal analysis agent that provides guided causal inference workflows using OpenAI's GPT models.

## Features

- Interactive causal analysis workflow
- Automated DAG and dataset selection
- Comprehensive Exploratory Data Analysis (EDA)
- Multiple causal inference methods
- AI-powered result interpretation
- Dockerized for easy deployment

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- OpenAI API key

### Setup

1. Clone or copy this directory
2. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

3. Add your OpenAI API key to `.env`:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### Running the Agent

#### Interactive Mode
```bash
docker-compose up causal-agent
```

This will start the agent in interactive mode where you can ask questions about causal analysis.

#### Jupyter Notebook Mode (Optional)
```bash
docker-compose --profile notebook up notebook
```

Access Jupyter at http://localhost:8888

### Usage

1. Start the container and you'll see the agent prompt
2. Ask a causal analysis question, for example:
   - "What is the effect of education on income?"
   - "How does marketing spend affect sales?"
   - "What factors influence customer churn?"

3. The agent will:
   - Propose a suitable DAG and dataset
   - Run exploratory data analysis
   - Suggest an analysis plan
   - Execute causal analysis
   - Interpret results

### Data and Configuration

- **Sample Data**: Located in `sample_data/` directory
- **Example DAGs**: Located in `examples/` directory
- **Analysis Output**: Saved to `output/` directory (mounted as volume)
- **Logs**: Saved to `logs/` directory (mounted as volume)

### Custom Data

To use your own data:

1. Place CSV files in `custom_data/` directory
2. The agent will automatically detect and use them

### API Mode

The container also exposes port 8000 for potential API access. You can extend the agent to include a FastAPI server for programmatic access.

### Supported Query Types

- `effect_estimation`: Estimate causal effects
- `anomaly_attribution`: Attribute anomalies to causes
- `distribution_shift_attribution`: Analyze distribution shifts
- `intervention`: Simulate interventions
- `counterfactual`: Generate counterfactual scenarios

### Architecture

```
causal-agent-docker/
├── causal_agent.py          # Main agent implementation
├── causal_eda.py           # EDA functionality
├── causal_analysis/        # Core causal analysis package
├── examples/               # Sample DAGs and data
├── sample_data/           # Sample datasets
├── Dockerfile             # Container definition
├── docker-compose.yml     # Service orchestration
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: Model to use (default: gpt-3.5-turbo)
- `LOG_LEVEL`: Logging level (default: INFO)

### Troubleshooting

1. **OpenAI API Issues**: Ensure your API key is correct and has sufficient credits
2. **Permission Issues**: Make sure the output and logs directories are writable
3. **Memory Issues**: Increase Docker memory allocation for large datasets

### Development

To modify the agent:

1. Edit the source files
2. Rebuild the container:
   ```bash
   docker-compose build
   ```

### License

This project is for educational and research purposes.