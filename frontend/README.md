# AI Data Analyzer - Frontend

A React + Vite frontend for the AI Data Analyzer LangGraph agent.

## 🚀 Getting Started

### Prerequisites

- Node.js (v18 or higher)
- LangGraph backend running on port 2024

### Installation

```bash
cd frontend
npm install
```

### Development

1. **Start the LangGraph backend** (in the `langgraph_app` folder):
   ```bash
   cd ../langgraph_app
   langgraph dev
   ```

2. **Start the frontend dev server** (in the `frontend` folder):
   ```bash
   npm run dev
   ```

3. Open [http://localhost:5173](http://localhost:5173) in your browser

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── Chat.jsx        # Main chat interface
│   │   └── Chat.css        # Chat styles
│   ├── services/           # API services
│   │   └── langgraph.js    # LangGraph API client
│   ├── App.jsx             # Main app component
│   ├── App.css             # App styles
│   ├── index.css           # Global styles
│   └── main.jsx            # Entry point
├── public/                  # Static assets
├── index.html              # HTML template
├── vite.config.js          # Vite configuration
└── package.json            # Dependencies
```

## 🔧 Configuration

### API Proxy

The Vite dev server is configured to proxy API requests to the LangGraph backend:

```javascript
// vite.config.js
server: {
  proxy: {
    '/runs': 'http://localhost:2024',
    '/threads': 'http://localhost:2024',
    '/assistants': 'http://localhost:2024'
  }
}
```

### LangGraph API Endpoints

The frontend uses these LangGraph API endpoints:

- `POST /threads` - Create a new conversation thread
- `POST /runs/stream` - Stream agent responses
- `POST /runs/wait` - Send message without streaming
- `GET /threads/{id}/state` - Get thread history

## 📦 Build for Production

```bash
npm run build
```

The built files will be in the `dist/` folder.

### Preview Production Build

```bash
npm run preview
```

## 🎨 Features

- **Real-time streaming** - Agent responses stream in real-time
- **Conversation threads** - Each session maintains conversation context
- **Clean UI** - Modern, responsive chat interface
- **Error handling** - Graceful error messages and connection status

## 🔍 Usage

1. The chat interface initializes a new thread automatically
2. Type your question about the e-commerce data
3. The agent will process your query and stream the response
4. Continue the conversation in the same thread

### Example Queries

- "What are the top selling products?"
- "Show me revenue trends over time"
- "Which cities have the most customers?"
- "Create a visualization of order distribution by category"

## 🛠️ Technology Stack

- **React 19** - UI framework
- **Vite 7** - Build tool and dev server
- **LangGraph API** - AI agent backend
- **Fetch API** - HTTP client for streaming

## 📝 Development Notes

- Hot Module Replacement (HMR) is enabled for instant updates
- The dev server runs on port 5173 by default
- Make sure the LangGraph backend is running before starting the frontend
- Check the browser console for detailed API interaction logs

## 🐛 Troubleshooting

**Error: Failed to initialize chat**
- Ensure the LangGraph dev server is running: `langgraph dev`
- Check that it's running on port 2024
- Verify the proxy configuration in `vite.config.js`

**Connection refused errors**
- Make sure both servers are running
- Check firewall settings
- Try restarting both servers

## 📄 License

Same license as the parent project.

