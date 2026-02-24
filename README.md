# Comet

An AI-powered chat application that lets you ask plain-English questions about your data and get back answers, insights, and interactive charts — no SQL knowledge required.

---

## What Does It Do?

Most business data sits inside databases that require technical knowledge to query. This project bridges that gap: you type a question like *"What were my top 5 selling products last month?"* and the AI figures out what data to retrieve, runs the query, crunches the numbers, picks the best chart to visualize it, and then explains the findings in plain language.

It is built on the [Olist Brazilian E-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), a real-world dataset covering customers, orders, products, sellers, payments, and reviews.

---

## How It Works (Non-Technical)

Think of the system as a team of specialized assistants working together behind the scenes every time you ask a question:

1. **Receptionist (Intention Agent)** — Reads your question and decides whether you are asking for data analysis or just asking a general question (e.g., about what tables exist, or saying hello).

2. **Analyst (Planner Agent)** — If you need data, the analyst breaks down your question into a precise data retrieval task.

3. **Database Engineer (Text-to-SQL Agent)** — Translates the analyst's task into a SQL query that can be run against the database.

4. **Review Step** — Before anything is executed, you get to see the generated SQL query. You can approve it or abort.

5. **Data Retrieval (SQL Executor)** — Runs the approved query and collects the results.

6. **Statistician (Statistical Analysis)** — Performs any necessary calculations on the raw results (e.g., totals, averages, rankings).

7. **Graphic Designer (Data Visualization Agent)** — Chooses the most appropriate chart type (bar, line, pie, scatter, heatmap, etc.) and configures it.

8. **Narrator (Response Synthesizer)** — Wraps everything up with a clear, plain-English explanation of what the data shows.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                  React Frontend                 │
│   (Chat UI + Interactive ECharts Visualizations)│
└────────────────────┬────────────────────────────┘
                     │ LangGraph API
┌────────────────────▼────────────────────────────┐
│              LangGraph Agent Pipeline           │
│                                                 │
│  Intention → Schema Info                        │
│           ↘                                     │
│             Planner → Text-to-SQL → Human Review│
│                          ↕ (retry on error)     │
│                       SQL Executor              │
│                          ↓                      │
│                  Statistical Analysis           │
│                          ↓                      │
│                  Data Visualization             │
│                          ↓                      │
│                  Response Synthesizer           │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│           FastAPI DB API Server                 │
│        (PostgreSQL / SQLite connection)         │
└─────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) |
| Language Models | OpenAI GPT (via LangChain) |
| Backend API | Python + FastAPI |
| Database | PostgreSQL (or SQLite for local dev) |
| Frontend | React + TypeScript + Vite |
| Charts | Apache ECharts |
| Monorepo | Turborepo |

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** and npm
- **PostgreSQL** (or SQLite for a quick local setup)
- An **OpenAI API key**
- A **LangSmith API key** (optional, for tracing)

---

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd ai-data-analyzer
```

### 2. Set up the Python environment

```bash
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r db_api_requirements.txt
pip install -e "langgraph_app/.[dev]" "langgraph-cli[inmem]"
```

### 3. Configure environment variables

Create a `.env` file inside `langgraph_app/`:

```ini
# langgraph_app/.env

OPENAI_API_KEY=sk-...

# Optional: LangSmith tracing
LANGSMITH_API_KEY=lsv2_...

# Database connection
DB_HOST=localhost
DB_PORT=5432
DB_NAME=olist
DB_USER=postgres
DB_PASSWORD=yourpassword
```

### 4. Set up the database

**Option A — PostgreSQL**

Make sure PostgreSQL is running, then import the CSV data:

```bash
python import_data_to_db/import_csv_to_postgresql.py
```

**Option B — SQLite (quick local setup)**

```bash
python create_olist_db.py
```

### 5. Install frontend dependencies

```bash
cd agent_frontend
npm install
cd ../
```

---

## Running the Application

All three services can be managed with the provided script:

**Windows (PowerShell):**
```powershell
.\start_server.ps1 start
```

**macOS / Linux:**
```bash
./start_server.sh start
```

This starts:
| Service | URL |
|---|---|
| React frontend | http://localhost:5173 |
| LangGraph agent server | http://localhost:2024 |
| Database API server | http://localhost:8000 |

To stop all services:
```powershell
.\start_server.ps1 stop      # Windows
./start_server.sh stop       # macOS / Linux
```

To check service status:
```powershell
.\start_server.ps1 status
```

---

## Running Services Individually

```bash
# LangGraph agent
cd langgraph_app
langgraph dev

# Database API server
python db_api_server.py

# Frontend
cd agent_frontend
npm run dev:web
```

---

## Example Questions You Can Ask

- *"What is the total revenue per product category?"*
- *"Show me the monthly order trend for 2017."*
- *"Which sellers have the highest average review score?"*
- *"What percentage of orders were delivered late?"*
- *"Compare average order value across Brazilian states."*
- *"What tables do I have access to?"*

---

## Dataset: Olist E-commerce

The application comes pre-configured for the [Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). It contains ~100k orders from 2016–2018 across the following tables:

| Table | Description |
|---|---|
| `customers` | Customer identifiers and locations |
| `orders` | Order status and timestamps |
| `order_items` | Products in each order and prices |
| `order_payments` | Payment method and installments |
| `order_reviews` | Customer review scores and comments |
| `products` | Product details and dimensions |
| `sellers` | Seller identifiers and locations |
| `geolocation` | ZIP code coordinates |

---

## Project Structure

```
ai-data-analyzer/
├── agent_frontend/          # React/TypeScript frontend (Turborepo monorepo)
│   └── apps/web/            # Main chat UI
├── langgraph_app/           # Python AI agent pipeline
│   └── src/agent/
│       ├── graph.py         # LangGraph state machine definition
│       ├── agents.py        # All agent node implementations
│       ├── *_system_prompt.py  # Prompts for each agent
│       └── artifacts/       # ECharts chart builders
├── db_api_server.py         # FastAPI server for DB connections
├── create_olist_db.py       # SQLite database setup script
├── import_data_to_db/       # PostgreSQL import scripts
├── olist_data/              # Raw CSV datasets
├── db_doc/                  # Human-readable schema documentation
├── start_server.ps1         # Windows service manager
└── start_server.sh          # Unix service manager
```

---

## Logs

Service logs are written to the `logs/` directory:

- `logs/frontend.log` — Frontend dev server output
- `logs/langgraph.log` — LangGraph agent server output
- `logs/db.log` — Database API server output
