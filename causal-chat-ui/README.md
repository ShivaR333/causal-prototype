# Causal Analysis Chat Interface

A modern web chat interface for the Causal Analysis Agent built with Next.js, React, and TypeScript.

## Features

- 💬 **Interactive Chat Interface**: Ask questions in natural language
- 📊 **Structured Analysis Form**: Run detailed causal analyses with forms
- 🔄 **Real-time API Integration**: Connects to the Docker API on port 8000
- 🎨 **Modern UI**: Clean, responsive design with Tailwind CSS
- 🔍 **Smart Query Parsing**: Automatically detects causal questions
- 📱 **Responsive Design**: Works on desktop and mobile

## Quick Start

### Prerequisites

1. **Docker Container Running**: Make sure your causal analysis API is running:
   ```bash
   # From the main project directory
   docker compose up -d
   ```

2. **Node.js**: Install Node.js 18+ if not already installed

### Installation & Setup

1. **Install Dependencies**:
   ```bash
   cd causal-chat-ui
   npm install
   ```

2. **Start Development Server**:
   ```bash
   npm run dev
   ```

3. **Open in Browser**:
   Navigate to [http://localhost:3000](http://localhost:3000)

## Usage

### Chat Interface

Ask questions in natural language:
- "What's the effect of discount on sales?"
- "Analyze the impact of education on income"
- "Show me the causal relationship between price and demand"

### Analysis Form

Use the sidebar form for detailed analysis:
1. Select query type (Effect Estimation, Discovery, Refutation)
2. Enter treatment variable (e.g., "discount")
3. Enter outcome variable (e.g., "sales")
4. Add confounders (comma-separated)
5. Choose data file
6. Click "Run Analysis"

### Connection Status

- 🟢 **Green**: Connected to API at localhost:8000
- 🔴 **Red**: Disconnected - check if Docker container is running

## Architecture

```
Frontend (Port 3000)  ←→  Backend API (Port 8000)
    Next.js/React     ←→     FastAPI/Docker
```

### Key Components

- **`src/app/page.tsx`**: Main chat interface
- **`src/components/ChatMessage.tsx`**: Individual message component  
- **`src/components/MessageInput.tsx`**: Text input for messages
- **`src/components/CausalForm.tsx`**: Structured analysis form
- **`src/lib/api.ts`**: API integration layer

### API Integration

The chat interface communicates with the causal analysis API via:
- **Health Check**: `GET /` - Check API status
- **Query Endpoint**: `POST /query` - Run causal analyses
- **Legacy Endpoint**: `POST /analyze` - Backward compatibility

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Environment Variables

Create `.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Customization

- **Styling**: Modify Tailwind classes in components
- **API Endpoints**: Update `src/lib/api.ts`
- **Natural Language**: Enhance patterns in `createNaturalLanguageQuery()`

## Troubleshooting

### Common Issues

1. **"Cannot connect to API"**
   - Ensure Docker container is running: `docker compose up -d`
   - Check API is accessible: `curl http://localhost:8000`

2. **CORS Errors**
   - API should allow localhost:3000 (already configured)
   - Check browser console for specific errors

3. **Build Errors**
   - Clear Next.js cache: `rm -rf .next`
   - Reinstall dependencies: `rm -rf node_modules && npm install`

### Logs

- **Frontend**: Check browser console (F12)
- **Backend**: Check Docker logs: `docker logs causal-prototype-causal-analysis-1`

## Example Queries

### Natural Language
- "What is the effect of discount on sales?"
- "Does education affect income?"
- "Analyze price impact on demand controlling for season"

### Form-based
- Treatment: `discount`, Outcome: `sales`, Confounders: `customer_segment, season`
- Treatment: `education`, Outcome: `income`, Confounders: `age, experience`

## Next Steps

- Add file upload functionality
- Implement chat history persistence
- Add visualization of results
- Support for custom DAG uploads
- Real-time analysis progress indicators