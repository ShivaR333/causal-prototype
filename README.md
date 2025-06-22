# Causal Analysis Agent

A comprehensive causal analysis platform with both web interface and API, powered by DoWhy, econometric methods, and LLM integration.

## 🚀 Quick Start

### 1. Start the Backend API
```bash
docker compose up -d
```

### 2. Start the Frontend (Optional)
```bash
cd frontend
npm install
npm run dev
```

### 3. Access the Applications
- **Web Chat Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **CLI Agent**: `docker exec -it causal-prototype-causal-analysis-1 python causal_agent.py`

## 📁 Project Structure

```
causal-prototype/
├── backend/                    # Python API and analysis engine
│   ├── causal_analysis/        # Core causal inference modules
│   ├── causal_agent.py         # Interactive LLM agent
│   ├── causal_eda.py          # EDA engine
│   ├── Dockerfile             # Backend container
│   └── requirements.txt       # Python dependencies
│
├── frontend/                   # React/Next.js web interface
│   ├── src/
│   │   ├── app/               # Next.js app router
│   │   ├── components/        # React components
│   │   └── lib/               # API integration
│   └── package.json           # Node dependencies
│
├── data/                       # Sample data and examples
│   ├── sample_data/           # CSV datasets
│   └── examples/              # DAG configurations
│
├── scripts/                    # Utility scripts
│   ├── run_tests.py           # Test runner
│   ├── test_bench.py          # Comprehensive testing
│   └── generate_sample_data.py # Data generation
│
├── docs/                       # Documentation
│   ├── TESTING.md
│   ├── AGENT_README.md
│   └── TestPlan.md
│
└── output/                     # Generated outputs (git ignored)
    ├── test_results/
    └── archived_runs/
```

## 💬 Web Chat Interface Features

- **Natural Language Queries**: Ask questions like "What's the effect of discount on sales?"
- **Structured Analysis Form**: Detailed causal analysis with dropdowns and validation
- **Real-time API Integration**: Live connection between frontend (port 3000) and backend (port 8000)
- **Visual Feedback**: Connection status, loading states, and error handling
- **Responsive Design**: Works on desktop and mobile

## 🔧 API Endpoints

### Main Analysis
- `POST /query` - Execute causal analysis
- `POST /analyze` - Legacy endpoint for backward compatibility
- `GET /` - Health check and API info
- `GET /docs` - Interactive API documentation

### Example API Usage
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "query_type": "effect_estimation",
      "treatment_variable": "discount",
      "outcome_variable": "sales",
      "confounders": ["customer_segment", "season"]
    },
    "data_file": "sample_data/eCommerce_sales.csv",
    "dag_file": "causal_analysis/config/sample_dag.json"
  }'
```

## 📊 Supported Analysis Types

1. **Effect Estimation** - Quantify causal relationships
2. **Causal Discovery** - Identify causal structures  
3. **Refutation Testing** - Validate causal assumptions
4. **Sensitivity Analysis** - Test robustness

## 🛠️ Development Setup

### Backend Development
```bash
cd backend
pip install -r requirements.txt
python causal_agent.py
```

### Frontend Development  
```bash
cd frontend
npm install
npm run dev
```

### Testing
```bash
cd scripts
python run_tests.py        # Full test suite
python test_bench.py       # Individual testing
```

## 🎯 Example Queries

### Natural Language (Web Interface)
- "Analyze the effect of education on income"
- "What's the impact of price on demand?"
- "Show me the causal relationship between discount and sales"

### Structured (API/Form)
- Treatment: `discount`, Outcome: `sales`, Confounders: `customer_segment, season`
- Treatment: `education`, Outcome: `income`, Confounders: `age, experience`

## 📈 Sample Datasets

Located in `data/sample_data/`:
- `eCommerce_sales.csv` - E-commerce transaction data
- `education_data.csv` - Education and income relationships
- `small_effect.csv`, `medium_effect.csv`, `large_effect.csv` - Synthetic datasets

## 🔐 Environment Configuration

Create `.env` file:
```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
```

## 🐳 Docker Commands

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs

# Stop services
docker compose down

# Rebuild after changes
docker compose up --build
```

## 🤝 Contributing

1. Follow the organized directory structure
2. Add tests for new features
3. Update documentation
4. Ensure Docker builds work

## 📚 Documentation

- **Backend API**: `/backend/causal_analysis/api/main.py`
- **Frontend Components**: `/frontend/src/components/`
- **Testing Guide**: `/docs/TESTING.md`
- **Agent Usage**: `/docs/AGENT_README.md`