
```
 ██████╗ ██████╗ ███╗   ███╗███████╗████████╗
██╔════╝██╔═══██╗████╗ ████║██╔════╝╚══██╔══╝
██║     ██║   ██║██╔████╔██║█████╗     ██║   
██║     ██║   ██║██║╚██╔╝██║██╔══╝     ██║   
╚██████╗╚██████╔╝██║ ╚═╝ ██║███████╗   ██║   
 ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝   ╚═╝   
```

<p align="center">
  <strong>Ask questions about your data in plain English.<br/>
  Comet writes the SQL, runs the query, and returns insights with visualizations.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue?logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/node-18+-green?logo=node.js&logoColor=white" alt="Node 18+" />
  <img src="https://img.shields.io/badge/langgraph-1.0+-orange" alt="LangGraph 1.0+" />
  <img src="https://img.shields.io/badge/openai-GPT-black?logo=openai&logoColor=white" alt="OpenAI GPT" />
</p>

---

## What Is Comet?

Comet is an AI-powered data analyst. You ask a question like *"What are the top 10 product categories by revenue?"* and Comet:

1. Understands your intent
2. Writes a SQL query
3. Shows you the SQL for approval before running it
4. Executes the query
5. Picks the best chart type and builds an interactive visualization
6. Explains the findings in plain language

No SQL knowledge required. No BI tools to configure. Just ask.

---

## How It Works

Every question passes through a pipeline of specialized AI agents:

```
Your Question
     │
     ▼
┌─────────────────────┐
│  Intention Agent     │  "Is this a data question or a general question?"
└────────┬────────────┘
         │
    ┌────┴────┐
    ▼         ▼
 Schema    Planner          "Break the question into data retrieval steps"
 Info        │
 (END)       ▼
        Text-to-SQL          "Write the SQL query"
              │
              ▼
        ┌───────────┐
        │   Human   │        ◄── You see the SQL, click Continue or Cancel
        │   Review  │
        └─────┬─────┘
              │
              ▼
        SQL Executor          "Run the query"
              │
         ┌────┴────┐
         ▼         ▼
      Statistical  Data       "Choose the best chart"
      Analysis     Visuals
         │         │
         └────┬────┘
              ▼
        Response               "Explain the findings in plain English"
        Synthesizer
              │
              ▼
         Your Answer (text + chart + table)
```

**Key features of the pipeline:**

- **Human-in-the-loop** — You review every SQL query before it runs. Approve it or cancel.
- **Self-correction** — If a query fails, the agent fixes it automatically (up to 3 retries).
- **Smart chart selection** — Chooses from 15+ chart types based on the data shape.
- **Multi-step plans** — Complex questions are broken into multiple queries with separate visualizations.

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) |
| Language Models | OpenAI GPT (via LangChain) |
| Backend API | Python + FastAPI |
| Database | PostgreSQL (or SQLite for local dev) |
| Frontend | React + TypeScript + Vite |
| Charts | Apache ECharts (bar, line, pie, scatter, heatmap, boxplot, and more) |
| Styling | Tailwind CSS |
| Monorepo | Turborepo |

---

## Prerequisites

| Requirement | Notes |
|---|---|
| **Python 3.10+** | For the agent pipeline and DB API |
| **Node.js 18+** | For the React frontend |
| **PostgreSQL** | Or use SQLite for a quick local setup |
| **OpenAI API key** | Required for the LLM agents |
| **LangSmith API key** | Optional — enables tracing and debugging |

---

## Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
cd ai-data-analyzer
```

### 2. Set up the Python environment

```bash
python -m venv .venv

# Activate it
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r db_api_requirements.txt
pip install -e "langgraph_app/.[dev]" "langgraph-cli[inmem]"
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```ini
# Required
OPENAI_API_KEY=sk-...

# Optional: LangSmith tracing
LANGSMITH_API_KEY=lsv2_...
```

If using **PostgreSQL**, also add:

```ini
DB_HOST=localhost
DB_PORT=5432
DB_NAME=olist
DB_USER=postgres
DB_PASSWORD=yourpassword
```

If using **Docker**, use these instead:

```ini
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=olist
```

### 4. Set up the database

Choose **one** of the following options:

<details>
<summary><strong>Option A — PostgreSQL (recommended for production)</strong></summary>

Make sure PostgreSQL is running, then import the data:

```bash
python import_data_to_db/import_csv_to_postgresql.py
```

</details>

<details>
<summary><strong>Option B — SQLite (quick local setup)</strong></summary>

```bash
python create_olist_db.py
```

This creates an `olist.db` file locally. No PostgreSQL installation needed.

</details>

<details>
<summary><strong>Option C — Docker (everything wired together)</strong></summary>

```bash
docker compose up --build
```

The database is created automatically. The importer container loads the CSV data on first run and skips if data already exists. To use a custom schema:

```ini
# Add to .env
POSTGRES_SCHEMA=myschema
```

</details>

### 5. Install frontend dependencies

```bash
cd agent_frontend
npm install
cd ..
```

### 6. Start all services

**Windows (PowerShell):**
```powershell
.\start_server.ps1 start
```

**macOS / Linux:**
```bash
./start_server.sh start
```

This launches:

| Service | URL |
|---|---|
| React frontend | http://localhost:5173 |
| LangGraph agent server | http://localhost:2024 |
| Database API server | http://localhost:8000 |

Open **http://localhost:5173** in your browser. Connect to a database using the sidebar, then start asking questions.

**Other commands:**

```powershell
.\start_server.ps1 stop       # Stop all services
.\start_server.ps1 status     # Check what's running
.\start_server.ps1 logs       # Tail all logs
```

### Running services individually

```bash
# Terminal 1 — LangGraph agent
cd langgraph_app
langgraph dev

# Terminal 2 — Database API
python db_api_server.py

# Terminal 3 — Frontend
cd agent_frontend
npm run dev:web
```

---

## Dataset: Olist Brazilian E-Commerce

Comet comes pre-configured for the [Olist Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — a real-world dataset of ~100k orders from a Brazilian marketplace (2016–2018).

| Table | Description |
|---|---|
| `customers` | Customer IDs and location (city, state, ZIP) |
| `orders` | Order records with status and timestamps (purchased → shipped → delivered) |
| `order_items` | Products in each order with price and freight cost |
| `order_payments` | Payment method, installments, and value |
| `order_reviews` | Customer review scores and comments |
| `products` | Product catalog with dimensions, weight, and category |
| `sellers` | Seller IDs and location |
| `geolocation` | ZIP code to latitude/longitude mapping |
| `product_category` | Category name translations (Portuguese → English) |

---

## Example Questions

Try asking things like:

- *"What are the top 10 product categories by revenue?"*
- *"Show me the monthly order trend for 2017."*
- *"Which sellers have the highest average review score?"*
- *"What percentage of orders were delivered late?"*
- *"Compare average order value across Brazilian states."*
- *"What's the correlation between product weight and freight cost?"*
- *"What tables do I have access to?"*

---

## Project Structure

```
ai-data-analyzer/
├── agent_frontend/               # React/TypeScript frontend
│   └── apps/web/src/
│       ├── components/thread/    # Chat UI and message rendering
│       ├── components/database/  # DB connector and schema viewer
│       ├── providers/            # LangGraph stream + thread providers
│       └── lib/                  # Utilities and helpers
│
├── langgraph_app/                # Python AI agent pipeline
│   └── src/agent/
│       ├── graph.py              # LangGraph state machine definition
│       ├── graph_routes.py       # Routing functions (conditional edges)
│       ├── agents.py             # All agent node implementations
│       ├── artifacts/            # ECharts chart builders
│       │   ├── bar_chart.py      # Bar, stacked, grouped, horizontal
│       │   ├── line_chart.py     # Line, smooth, stacked, area
│       │   ├── pie_chart.py      # Pie charts
│       │   ├── scatter_chart.py  # Scatter / bubble (with downsampling)
│       │   ├── heatmap_chart.py  # Heatmap + correlation matrix
│       │   ├── box_plot.py       # Boxplot (pre-computed stats)
│       │   └── bar_line_chart.py # Dual-axis bar + line combos
│       └── *_system_prompt.py    # System prompts for each agent
│
├── db_api_server.py              # FastAPI server for DB connections
├── db_doc/                       # Human-readable schema documentation
├── create_olist_db.py            # SQLite database setup script
├── import_data_to_db/            # PostgreSQL import scripts
├── olist_data/                   # Raw CSV datasets
├── start_server.ps1              # Windows service manager
└── start_server.sh               # Unix service manager
```

---

## Logs

Service logs are written to the `logs/` directory:

| File | Content |
|---|---|
| `logs/frontend.log` | Frontend dev server output |
| `logs/langgraph.log` | LangGraph agent server output |
| `logs/db.log` | Database API server output |

---

## License

MIT
