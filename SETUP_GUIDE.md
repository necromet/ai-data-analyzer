# Connecting Frontend to Your LangGraph App

## Overview
Your frontend is now configured to connect to your custom LangGraph application that analyzes data from the Olist database.

## Configuration Summary

### Backend (LangGraph App)
- **Location**: `langgraph_app/`
- **Graph ID**: `agent` (defined in `langgraph.json`)
- **Graph Path**: `./src/agent/graph.py:app`

### Frontend (Agent Frontend)
- **Location**: `agent_frontend/`
- **API URL**: `http://localhost:2024`
- **Assistant ID**: `agent`

## Setup Steps

### 1. Start the LangGraph Server (Backend)

Open a terminal and navigate to your LangGraph app directory:

```bash
cd "/media/edward/SSD-Data/My Folder/ai-data-analyzer/langgraph_app"
```

Start the LangGraph development server:

```bash
langgraph dev
```

This will:
- Start the server on `http://localhost:2024`
- Hot-reload when you make changes to your graph
- Provide the LangGraph Studio interface

**Note**: Make sure you have the LangGraph CLI installed:
```bash
pip install -U langgraph-cli
```

### 2. Start the Frontend

Open a **new terminal** and navigate to the frontend directory:

```bash
cd "/media/edward/SSD-Data/My Folder/ai-data-analyzer/agent_frontend"
```

Install dependencies (if not already done):

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend will start on `http://localhost:5173` (or another port if 5173 is busy).

### 3. Access the Application

1. Open your browser to the URL shown in the terminal (typically `http://localhost:5173`)
2. The frontend should automatically connect to your LangGraph server
3. You can now chat with your data analysis agent!

## Troubleshooting

### Frontend can't connect to backend
- Verify the LangGraph server is running on `http://localhost:2024`
- Check the browser console for connection errors
- Ensure your `.env` file in `agent_frontend/apps/web/.env` has the correct values

### LangGraph server won't start
- Verify Python dependencies are installed: `pip install -e langgraph_app/`
- Check that your database connection in `database_tools.py` is working
- Review the terminal output for specific errors

### Port conflicts
If port 2024 is already in use, you can change it by:
1. Updating the LangGraph server port in the startup command
2. Updating `VITE_API_URL` in `agent_frontend/apps/web/.env`

## Environment Variables

### Backend (.env in langgraph_app/)
```env
LANGSMITH_API_KEY=your_key_here  # Optional: for tracing
OPENAI_API_KEY=your_key_here     # Required: for OpenAI models
```

### Frontend (.env in agent_frontend/apps/web/)
```env
VITE_API_URL=http://localhost:2024
VITE_ASSISTANT_ID=agent
# VITE_LANGSMITH_API_KEY=  # Optional: if you want client-side tracing
```

## Testing the Connection

Once both servers are running:

1. Open the frontend in your browser
2. Try asking a question like:
   - "What tables are in the database?"
   - "Show me the top 10 customers by order count"
   - "Create a chart of sales by month"

Your graph should process these queries through the various agents (Intention Agent → Planner → SQL Agent → Data Visualizer → Response Synthesizer) and return results with visualizations!

## Development Tips

- **LangGraph Studio**: Access at `http://localhost:2024` for visual debugging
- **Hot Reload**: Both servers support hot reload during development
- **Debugging**: Check token usage logs in `langgraph_app/src/agent/token_usage/`
- **Query Results**: Saved in `langgraph_app/src/agent/query_results/`
