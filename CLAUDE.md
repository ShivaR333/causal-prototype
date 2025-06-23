# CLAUDE.md

This document provides context and instructions for Claude when working on the Causal Analysis Agent project.

## Project Overview

A comprehensive causal analysis platform with both web interface and API, powered by DoWhy, econometric methods, and LLM integration. The project enables users to perform causal inference through natural language queries or structured analysis forms. The project is run in sprints. 

## Architecture

- **Backend**: Python FastAPI service with causal analysis engine
- **Frontend**: React/Next.js web interface for chat and forms
- **Data**: Sample datasets and DAG configurations
- **Docker**: Containerized deployment with docker-compose

## Key Components

### Backend (`/backend/`)
- `causal_agent.py` - Interactive LLM agent for CLI usage
- `causal_analysis/` - Core causal inference modules
  - `api/main.py` - FastAPI endpoints
  - `dispatch.py` - Query routing and processing
  - `models.py` - Data models and schemas
- `causal_eda.py` - Exploratory data analysis engine

### Frontend (`/frontend/`)
- `src/app/page.tsx` - Main chat interface
- `src/components/` - React components
  - `CausalForm.tsx` - Structured analysis form
  - `MessageInput.tsx` - Chat input component
  - `AgentStatusPanel.tsx` - Status display
- `src/lib/api.ts` - API integration utilities

## Development Commands

### Backend
```bash
cd backend
pip install -r requirements.txt
python causal_agent.py  # CLI agent
uvicorn causal_analysis.api.main:app --reload  # API server
```

### Frontend
```bash
cd frontend
npm install
npm run dev
npm run build
npm run lint
```

### Testing
```bash
cd scripts
python run_tests.py        # Full test suite
python test_bench.py       # Individual testing
python run_eda_tests.py    # EDA testing
```

### Docker
```bash
docker compose up -d       # Start all services
docker compose logs        # View logs
docker compose down        # Stop services
docker compose up --build # Rebuild after changes
```

## Important Files

- `docker-compose.yml` - Service orchestration
- `backend/requirements.txt` - Python dependencies
- `frontend/package.json` - Node.js dependencies
- `data/sample_data/` - Test datasets
- `data/examples/` - DAG configurations
- `docs/` - Additional documentation

## API Endpoints

- `POST /query` - Main causal analysis endpoint
- `POST /analyze` - Legacy analysis endpoint
- `GET /` - Health check
- `GET /docs` - API documentation

## Environment Variables

Create `.env` file with:
```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
```

## Code Conventions

- **Python**: Follow PEP 8, use type hints, async/await for API endpoints
- **TypeScript/React**: Use functional components, TypeScript strict mode
- **API**: RESTful design with proper HTTP status codes
- **Testing**: Unit tests in respective test directories

## Common Tasks

### Adding New Analysis Types
1. Update `backend/causal_analysis/models.py` with new query types
2. Implement logic in `backend/causal_analysis/dispatch.py`
3. Add frontend components if needed
4. Update API documentation

### Frontend Components
- Follow existing component patterns in `src/components/`
- Use TypeScript interfaces for props
- Implement proper error handling and loading states

### Data Handling
- New datasets go in `data/sample_data/`
- DAG configurations in `data/examples/`
- Output files are git-ignored in `output/`

## Testing Strategy

- Backend: pytest with test files in `backend/causal_analysis/tests/`
- Frontend: Jest/React Testing Library (setup in package.json)
- Integration: Scripts in `scripts/` directory
- Test data: Use existing sample datasets or generate synthetic data

## Deployment Notes

- Services run on ports 3000 (frontend) and 8000 (backend)
- Docker containers handle all dependencies
- Environment variables required for OpenAI integration
- Persistent volumes for data and output directories

## Documentation

- Maintain a SprintDoc.md in the root folder
- Start a new section for each new sprint when specified by the user by saying "Start a new sprint"
- Ensure that the key features for the sprint are clear and status against them are updated after each step in the SprintDoc.md
- Update sprintcounter
- Ensure all git commits carry the corresponding sprint number in remarks