# Database API Server

A FastAPI-based backend server for managing PostgreSQL database connections from the frontend application.

## Features

- Connect to PostgreSQL databases with credentials
- Test database connections
- Retrieve database schema (tables and columns)
- Manage multiple database connections
- CORS-enabled for frontend communication

## Installation

1. Install the required dependencies:

```bash
pip install -r db_api_requirements.txt
```

## Running the Server

Start the database API server:

```bash
python db_api_server.py
```

The server will start on `http://localhost:8000`

## API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Connect to Database
**POST** `/api/database/connect`

Connect to a PostgreSQL database.

**Request Body:**
```json
{
  "host": "localhost",
  "port": 5432,
  "database": "your_database",
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully connected to PostgreSQL database: your_database",
  "connection_id": "localhost:5432/your_database"
}
```

### Disconnect from Database
**POST** `/api/database/disconnect?connection_id={connection_id}`

Close an active database connection.

### Get Database Schema
**GET** `/api/database/schema?connection_id={connection_id}`

Retrieve the schema of the connected database (all tables and columns).

**Response:**
```json
{
  "success": true,
  "tables": [
    {
      "name": "customers",
      "columns": [
        {
          "name": "customer_id",
          "type": "varchar",
          "nullable": false
        }
      ]
    }
  ],
  "message": "Retrieved schema for 5 tables"
}
```

### Get Connection Status
**GET** `/api/database/status`

Get information about all active database connections.

## Frontend Integration

The frontend components automatically connect to this API server:

1. **Database Connector** (`components/database/connector.tsx`): 
   - Manages database connection credentials
   - Tests and establishes connections

2. **Database Viewer** (`components/database/viewer.tsx`):
   - Displays database schema
   - Shows tables and columns with data types

## Security Notes

⚠️ **Important**: This is a development server. For production use:
- Implement proper authentication and authorization
- Use environment variables for sensitive configuration
- Implement connection pooling
- Add rate limiting
- Use HTTPS
- Store connection credentials securely (not in memory)
- Implement proper session management

## CORS Configuration

The server is configured to accept requests from:
- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (Alternative frontend port)

To add more origins, update the `allow_origins` list in `db_api_server.py`.

## Troubleshooting

### Connection Issues

If you can't connect to the database:
1. Verify PostgreSQL is running
2. Check the host, port, and credentials
3. Ensure PostgreSQL allows connections from your IP
4. Check `pg_hba.conf` for connection permissions

### CORS Errors

If you see CORS errors in the frontend:
1. Verify the frontend URL is in the `allow_origins` list
2. Restart the API server after making changes

## Development

The server uses:
- **FastAPI**: Modern web framework for building APIs
- **psycopg2**: PostgreSQL adapter for Python
- **Pydantic**: Data validation using Python type annotations
- **Uvicorn**: ASGI server for running the application
