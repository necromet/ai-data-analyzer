# PostgreSQL Database Integration - Quick Start Guide

This guide will help you set up and use the PostgreSQL database connection feature in the AI Data Analyzer.

## Prerequisites

- Python 3.8 or higher
- Node.js 18 or higher
- PostgreSQL database server running (or access to a remote PostgreSQL instance)

## Setup Instructions

### 1. Install Backend Dependencies

Install the required Python packages for the database API server:

```bash
pip install -r db_api_requirements.txt
```

### 2. Start the Database API Server

In one terminal, start the FastAPI backend server:

```bash
python db_api_server.py
```

The server will start on `http://localhost:8000`. You should see:
```
Starting Database API Server on http://localhost:8000
API Documentation available at http://localhost:8000/docs
```

### 3. Start the Frontend

In another terminal, navigate to the frontend directory and start the development server:

```bash
cd agent_frontend
npm run dev
```

The frontend will start on `http://localhost:5173`.

### 4. Connect to Your PostgreSQL Database

1. Open the application in your browser at `http://localhost:5173`
2. Click the sidebar toggle button (if not visible)
3. Click on the **"Connect"** tab in the sidebar
4. Fill in your PostgreSQL connection details:
   - **Host**: localhost (or your PostgreSQL server address)
   - **Port**: 5432 (default PostgreSQL port)
   - **Database Name**: Your database name
   - **Username**: Your PostgreSQL username
   - **Password**: Your PostgreSQL password
5. Click **"Connect"**

### 5. View Database Schema

After successfully connecting:
1. Click on the **"Schema"** tab in the sidebar
2. The database schema will load automatically
3. Click on any table to expand and view its columns, data types, and constraints

## Features

### Database Connector
- Connect to PostgreSQL databases
- Connection status indicator (green for connected, red for error)
- Secure credential handling
- Test connection functionality

### Database Viewer
- Browse all tables in your database
- View column names and data types
- See nullable constraints
- Expandable/collapsible table view
- Refresh schema button

## API Endpoints

The database API server provides these endpoints:

- **POST** `/api/database/connect` - Connect to a database
- **POST** `/api/database/disconnect` - Disconnect from a database
- **GET** `/api/database/schema` - Get database schema
- **GET** `/api/database/status` - Check connection status

For detailed API documentation, visit: http://localhost:8000/docs

## Troubleshooting

### Cannot Connect to Database

**Error**: "Connection failed: could not connect to server"

**Solution**:
1. Verify PostgreSQL is running: `sudo systemctl status postgresql` (Linux) or check services (Windows)
2. Check if PostgreSQL is listening on the correct port: `sudo netstat -plnt | grep 5432`
3. Verify your credentials are correct
4. Check PostgreSQL configuration (`pg_hba.conf`) allows connections from your IP

### CORS Errors in Browser

**Error**: "Access to fetch at ... has been blocked by CORS policy"

**Solution**:
1. Verify the database API server is running on port 8000
2. Check that your frontend URL matches the allowed origins in `db_api_server.py`
3. Restart the API server after making changes

### API Server Not Starting

**Error**: "Address already in use"

**Solution**:
- Port 8000 is already in use. Either:
  - Kill the process using port 8000: `sudo lsof -ti:8000 | xargs kill -9`
  - Or change the port in `db_api_server.py` and update `DB_API_URL` in the frontend components

### Database Schema Not Loading

**Error**: "No active database connection"

**Solution**:
1. Ensure you've connected to a database first (Connect tab)
2. Check browser console for errors
3. Verify the connection ID is stored: Check `localStorage.getItem('db_connection_id')` in browser console

## Architecture

```
┌─────────────────────┐
│   React Frontend    │
│  (localhost:5173)   │
└──────────┬──────────┘
           │
           │ HTTP/REST
           │
┌──────────▼──────────┐
│  FastAPI Backend    │
│  (localhost:8000)   │
└──────────┬──────────┘
           │
           │ psycopg2
           │
┌──────────▼──────────┐
│  PostgreSQL Server  │
│  (localhost:5432)   │
└─────────────────────┘
```

## Security Notes

⚠️ **Important**: This setup is for development only.

For production deployment:
- Use environment variables for sensitive data
- Implement proper authentication (JWT, OAuth)
- Use HTTPS for all connections
- Implement rate limiting
- Store database credentials securely (e.g., encrypted vault)
- Use connection pooling
- Add input validation and sanitization
- Implement proper error handling without exposing sensitive information

## Next Steps

- Integrate the database connection with the LangGraph agent for AI-powered queries
- Add support for other database types (MySQL, SQLite, etc.)
- Implement query execution from the frontend
- Add data visualization for query results
- Implement connection history and saved connections

## Support

For issues or questions:
1. Check the API documentation at http://localhost:8000/docs
2. Review the [DB_API_README.md](DB_API_README.md) for detailed API information
3. Check the browser console and API server logs for errors
