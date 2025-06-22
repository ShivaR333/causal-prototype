# Causal Analysis Prototype

A comprehensive causal inference toolkit built on DoWhy that supports multiple types of causal queries through both API and CLI interfaces.

## Features

- **Multiple Query Types**: Effect estimation, anomaly attribution, distribution shift attribution, intervention analysis, and counterfactual reasoning
- **Flexible Architecture**: Supports both programmatic and interactive usage via FastAPI and CLI
- **DoWhy Integration**: Leverages DoWhy's causal inference capabilities with custom extensions
- **DAG-Based Modeling**: Uses JSON-based DAG configurations for causal model specification
- **Type-Safe**: Built with Pydantic models for robust data validation

## Installation

### Prerequisites

- Python 3.8+
- pip or conda

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install in development mode:

```bash
pip install -e .
```

### Dependencies

- `dowhy>=0.11.0` - Causal inference library
- `fastapi>=0.104.0` - Web API framework
- `pydantic>=2.0.0` - Data validation
- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.24.0` - Numerical computing
- `networkx>=3.0` - Graph operations
- `click>=8.1.0` - CLI framework

## Quick Start

### 1. Using the API

Start the FastAPI server:

```bash
uvicorn causal_analysis.api.main:app --reload
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

### 2. Using the CLI

After installation, use the CLI tool:

```bash
causal-analysis --help
```

### 3. Basic Example

```bash
# Run effect estimation
causal-analysis analyze \
  --treatment T \
  --outcome Y \
  --confounders X \
  --dag-file causal_analysis/config/sample_dag.json \
  --data-file sample_data/small_sample.csv
```

## Data Formats

### DAG Configuration (JSON)

Define your causal model structure:

```json
{
  "name": "treatment_outcome_dag",
  "description": "Sample DAG for treatment effect analysis",
  "variables": {
    "X": {
      "name": "confounder",
      "type": "continuous",
      "description": "Age or income confounder"
    },
    "T": {
      "name": "treatment",
      "type": "binary", 
      "description": "Treatment assignment (0/1)"
    },
    "Y": {
      "name": "outcome",
      "type": "continuous",
      "description": "Outcome variable"
    }
  },
  "edges": [
    {"from": "X", "to": "T"},
    {"from": "X", "to": "Y"},
    {"from": "T", "to": "Y"}
  ],
  "treatment_variable": "T",
  "outcome_variable": "Y",
  "confounders": ["X"]
}
```

### Data Files (CSV)

Your data should be in CSV format with columns matching the variable names in your DAG:

```csv
X,T,Y
25.5,1,12.3
30.2,0,8.7
...
```

## Query Types

### 1. Effect Estimation

Estimate causal effects using DoWhy's identification and estimation methods.

**API Example:**
```json
{
  "query": {
    "query_type": "effect_estimation",
    "treatment_variable": "T",
    "outcome_variable": "Y",
    "confounders": ["X"],
    "treatment_value": 1.0
  },
  "dag_file": "causal_analysis/config/sample_dag.json",
  "data_file": "sample_data/small_sample.csv"
}
```

**CLI Example:**
```bash
causal-analysis analyze \
  --treatment T \
  --outcome Y \
  --confounders X \
  --treatment-value 1.0 \
  --dag-file causal_analysis/config/sample_dag.json \
  --data-file sample_data/small_sample.csv
```

### 2. Anomaly Attribution

Identify potential causes of anomalies in outcome variables.

**API Example:**
```json
{
  "query": {
    "query_type": "anomaly_attribution",
    "outcome_variable": "Y",
    "anomaly_threshold": 15.0,
    "potential_causes": ["X", "T"],
    "time_window": "2023-01-01_2023-12-31"
  },
  "dag_file": "causal_analysis/config/sample_dag.json",
  "data_file": "sample_data/small_sample.csv"
}
```

**CLI Example:**
```bash
causal-analysis anomaly \
  --outcome Y \
  --threshold 15.0 \
  --causes X,T \
  --dag-file causal_analysis/config/sample_dag.json \
  --data-file sample_data/small_sample.csv
```

### 3. Distribution Shift Attribution

Analyze what drives changes in variable distributions between time periods.

**API Example:**
```json
{
  "query": {
    "query_type": "distribution_shift_attribution",
    "target_variable": "Y",
    "baseline_period": "2023-01-01_2023-06-30",
    "comparison_period": "2023-07-01_2023-12-31",
    "potential_drivers": ["X", "T"]
  },
  "dag_file": "causal_analysis/config/sample_dag.json",
  "data_file": "sample_data/small_sample.csv"
}
```

### 4. Intervention Analysis

Simulate the effects of interventions on multiple outcome variables.

**API Example:**
```json
{
  "query": {
    "query_type": "intervention",
    "intervention_variable": "T",
    "intervention_value": 1.0,
    "outcome_variables": ["Y"],
    "constraints": []
  },
  "dag_file": "causal_analysis/config/sample_dag.json",
  "data_file": "sample_data/small_sample.csv"
}
```

**CLI Example:**
```bash
causal-analysis intervention \
  --intervention-var T \
  --intervention-value 1.0 \
  --outcomes Y \
  --dag-file causal_analysis/config/sample_dag.json \
  --data-file sample_data/small_sample.csv
```

### 5. Counterfactual Analysis

Compare factual and counterfactual scenarios.

**API Example:**
```json
{
  "query": {
    "query_type": "counterfactual",
    "factual_scenario": {"T": 1, "X": 25.0},
    "counterfactual_scenario": {"T": 0, "X": 25.0},
    "outcome_variable": "Y",
    "evidence_variables": ["X"]
  },
  "dag_file": "causal_analysis/config/sample_dag.json",
  "data_file": "sample_data/small_sample.csv"
}
```

## API Reference

### Endpoints

#### `POST /query`

Execute any causal query using the dispatch system.

**Request Body:**
```json
{
  "query": {
    "query_type": "effect_estimation|anomaly_attribution|distribution_shift_attribution|intervention|counterfactual",
    // ... query-specific parameters
  },
  "dag_file": "path/to/dag.json",
  "data_file": "path/to/data.csv"
}
```

**Response:**
```json
{
  "success": true,
  "query_type": "effect_estimation",
  "estimate": 0.5,
  "confidence_interval": [0.3, 0.7],
  "summary": "Estimated causal effect...",
  // ... additional query-specific results
}
```

#### `POST /analyze` (Legacy)

Legacy endpoint for effect estimation queries.

**Request Body:**
```json
{
  "treatment_variable": "T",
  "outcome_variable": "Y",
  "confounders": ["X"],
  "treatment_value": 1.0,
  "dag_file": "causal_analysis/config/sample_dag.json",
  "data_file": "sample_data/small_sample.csv"
}
```

#### `GET /`

Health check endpoint.

## CLI Reference

### Commands

- `causal-analysis analyze` - Effect estimation
- `causal-analysis query` - Execute query from JSON file
- `causal-analysis anomaly` - Anomaly attribution
- `causal-analysis intervention` - Intervention analysis

### Global Options

- `--dag-file` - Path to DAG configuration file (default: `causal_analysis/config/sample_dag.json`)
- `--data-file` - Path to CSV data file (required)

### Using Query Files

Create a JSON file with your query:

```json
{
  "query_type": "effect_estimation",
  "treatment_variable": "treatment",
  "outcome_variable": "outcome",
  "confounders": ["age", "income"]
}
```

Then execute:

```bash
causal-analysis query \
  --query-file my_query.json \
  --dag-file examples/complex_dag.json \
  --data-file examples/complex_data.csv
```

## Architecture

### Core Components

1. **Models** (`causal_analysis/models.py`):
   - Pydantic models for each query type
   - Type-safe validation with Literal types
   - Union type for dispatch

2. **CausalModel** (`causal_analysis/causal_model.py`):
   - Wrapper around DoWhy's CausalModel
   - Loads DAG from JSON configuration
   - Provides convenient methods for causal inference

3. **Dispatch System** (`causal_analysis/dispatch.py`):
   - Central query routing based on query type
   - Handlers for each query type
   - Error handling and result formatting

4. **API** (`causal_analysis/api/main.py`):
   - FastAPI endpoints
   - Request/response models
   - Integration with dispatch system

5. **CLI** (`causal_analysis/cli/main.py`):
   - Click-based command-line interface
   - Multiple commands for different query types
   - JSON output formatting

### Data Flow

1. Query (JSON) → Dispatch System
2. Load DAG and Data → CausalModel
3. Route to appropriate handler based on query_type
4. Execute causal analysis using DoWhy or custom logic
5. Return JSON-serializable results

## Examples

### Sample DAGs

- `causal_analysis/config/sample_dag.json` - Simple treatment-outcome DAG
- `examples/complex_dag.json` - Healthcare intervention DAG
- `examples/eCommerce_sales_dag.json` - E-commerce sales DAG

### Sample Data

- `sample_data/small_sample.csv` - Small dataset for testing
- `sample_data/large_effect.csv` - Large effect size dataset
- `examples/complex_data.csv` - Complex healthcare data

### Generating Synthetic Data

```bash
python generate_sample_data.py
```

This generates synthetic data based on the DAG structure for testing.

## Development

### Running Tests

#### Unit Tests
```bash
pytest tests/
```

#### Comprehensive Test Bench

The project includes a comprehensive test bench that validates the entire causal analysis pipeline:

```bash
python run_tests.py
```

Or run the test bench directly:

```bash
python test_bench.py
```

The test bench:
1. **Generates Sample DAGs**: Creates various DAG structures (simple linear, complex healthcare, collider bias)
2. **Generates Synthetic Data**: Creates data with known ground truth causal effects
3. **Tests All Query Types**: Runs all 5 query types (effect estimation, anomaly attribution, distribution shift, intervention, counterfactual)
4. **Validates Results**: Compares estimated values against known ground truth
5. **Provides Detailed Reports**: Shows results in tabular format with pass/fail status

**Sample Output:**
```
🧪 CAUSAL ANALYSIS TEST BENCH REPORT
==================================================
Total Tests: 15
Passed: 12 (80.0%)
Failed: 2 (13.3%)
Errors: 1 (6.7%)

📋 DETAILED RESULTS
┌─────────────────────────────────────┬─────────────────────────────────┬────────┬───────────┬──────────┬───────────┬───────────┬──────────┐
│ Test ID                             │ Query Type                      │ Status │ Est Value │ GT Value │ Abs Error │ Rel Error │ Time (s) │
├─────────────────────────────────────┼─────────────────────────────────┼────────┼───────────┼──────────┼───────────┼───────────┼──────────┤
│ simple_linear_dag_effect_estimation │ effect_estimation               │ PASS   │ 1.4823    │ 1.5000   │ 0.0177    │ 1.18%     │ 0.234    │
│ simple_linear_dag_anomaly_attribution│ anomaly_attribution            │ PASS   │ 52        │ 50       │ 2.0000    │ 4.00%     │ 0.156    │
└─────────────────────────────────────┴─────────────────────────────────┴────────┴───────────┴──────────┴───────────┴───────────┴──────────┘
```

**Test Output Files:**
- `test_results/test_report.txt` - Human-readable test report
- `test_results/test_results.json` - Detailed results in JSON format

For detailed testing information, see [TESTING.md](TESTING.md).

### Starting Development Server

```bash
uvicorn causal_analysis.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Code Structure

```
causal_analysis/
├── __init__.py
├── models.py              # Pydantic models
├── causal_model.py        # DoWhy wrapper
├── dispatch.py           # Query routing system
├── api/
│   ├── __init__.py
│   └── main.py           # FastAPI application
├── cli/
│   ├── __init__.py
│   └── main.py           # Click CLI
├── config/
│   └── sample_dag.json   # Sample DAG
├── core/
│   └── __init__.py
└── data/
    ├── __init__.py
    ├── synthetic_generator.py
    └── utils.py
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`

2. **DAG Loading Errors**: Verify DAG JSON format matches the expected structure

3. **Data Format Errors**: Ensure CSV columns match variable names in DAG

4. **DoWhy Estimation Failures**: Some estimation methods may fail depending on data characteristics. The system tries multiple methods and reports which ones succeed.

### Debug Mode

For detailed error information, run with debug logging:

```bash
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# Your code here
"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.