"""
FastAPI server for database connection management.
Handles PostgreSQL and other database connections for the frontend.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2 import sql
import traceback
import os


def is_running_in_docker() -> bool:
    """Detect if the code is running inside a Docker container."""
    # Check for .dockerenv file in the root filesystem
    if os.path.exists('/.dockerenv'):
        return True
    
    # Check cgroup file for docker-related entries
    try:
        with open('/proc/1/cgroup', 'r') as f:
            cgroup_content = f.read()
            if 'docker' in cgroup_content or 'containerd' in cgroup_content:
                return True
    except (FileNotFoundError, PermissionError):
        pass
    
    return False


# Flag to track if we're running in Docker
RUNNING_IN_DOCKER = is_running_in_docker()

app = FastAPI(title="Database API Server", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active connections (in production, use Redis or similar)
active_connections: Dict[str, Any] = {}


class DatabaseConnectionInfo(BaseModel):
    host: str
    port: int
    database: str
    username: str
    password: str


class ConnectionResponse(BaseModel):
    success: bool
    message: str
    connection_id: Optional[str] = None


class TableColumn(BaseModel):
    name: str
    type: str
    nullable: bool


class TableInfo(BaseModel):
    name: str
    columns: List[TableColumn]


class SchemaResponse(BaseModel):
    success: bool
    tables: List[TableInfo]
    message: Optional[str] = None


class SchemasListResponse(BaseModel):
    success: bool
    schemas: List[str]
    message: Optional[str] = None


class QueryRequest(BaseModel):
    sql: str
    connection_id: Optional[str] = None
    schema: Optional[str] = None


class QueryResponse(BaseModel):
    success: bool
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    message: Optional[str] = None


@app.get("/")
async def root():
    return {"message": "Database API Server", "version": "1.0.0"}


@app.post("/api/database/connect", response_model=ConnectionResponse)
async def connect_database(connection_info: DatabaseConnectionInfo):
    """Test and establish a database connection."""

    host = connection_info.host
    # Only translate localhost to 'db' when running in Docker
    if RUNNING_IN_DOCKER and host in ("localhost", "127.0.0.1", "::1"):
        host = "db"

    try:
        # Create connection string. use the possibly-translated host value
        conn = psycopg2.connect(
            host=host,
            port=connection_info.port,
            database=connection_info.database,
            user=connection_info.username,
            password=connection_info.password,
            connect_timeout=10
        )
        # store the normalized host back into info so that status endpoints
        # reflect what was actually used for the connection
        connection_info.host = host
        
        # Enable autocommit to prevent transaction aborted errors
        conn.autocommit = True
        
        # Test the connection
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        cursor.close()
        
        # Generate a simple connection ID (in production, use UUID)
        connection_id = f"{connection_info.host}:{connection_info.port}/{connection_info.database}"
        
        # Store the connection (in production, implement proper connection pooling)
        active_connections[connection_id] = {
            "connection": conn,
            "info": connection_info.model_dump()
        }
        
        return ConnectionResponse(
            success=True,
            message=f"Successfully connected to PostgreSQL database: {connection_info.database}",
            connection_id=connection_id
        )
        
    except psycopg2.OperationalError as e:
        error_msg = str(e).split('\n')[0]  # Get first line of error
        raise HTTPException(
            status_code=400,
            detail=f"Connection failed: {error_msg}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@app.post("/api/database/disconnect")
async def disconnect_database(connection_id: str):
    """Close a database connection."""
    try:
        if connection_id in active_connections:
            conn = active_connections[connection_id]["connection"]
            conn.close()
            del active_connections[connection_id]
            return {"success": True, "message": "Database disconnected"}
        else:
            raise HTTPException(status_code=404, detail="Connection not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/database/schemas", response_model=SchemasListResponse)
async def list_schemas(connection_id: Optional[str] = None):
    """List all available schemas in the database."""
    try:
        if not connection_id:
            if not active_connections:
                raise HTTPException(
                    status_code=400,
                    detail="No active database connection. Please connect first."
                )
            connection_id = list(active_connections.keys())[0]
        
        if connection_id not in active_connections:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        conn = active_connections[connection_id]["connection"]
        cursor = conn.cursor()
        
        # Get all schemas except system schemas
        cursor.execute("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name;
        """)
        
        schemas = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        return SchemasListResponse(
            success=True,
            schemas=schemas,
            message=f"Found {len(schemas)} schema(s)"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing schemas: {str(e)}"
        )


@app.get("/api/database/schema", response_model=SchemaResponse)
async def get_database_schema(connection_id: Optional[str] = None, schema: str = "public"):
    """Retrieve the database schema (tables and columns) for a specific schema."""
    try:
        # For now, if no connection_id, try to use the first available connection
        if not connection_id:
            if not active_connections:
                raise HTTPException(
                    status_code=400,
                    detail="No active database connection. Please connect first."
                )
            connection_id = list(active_connections.keys())[0]
        
        if connection_id not in active_connections:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        conn = active_connections[connection_id]["connection"]
        cursor = conn.cursor()
        
        # Get all tables in the specified schema
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s 
            ORDER BY table_name;
        """, (schema,))
        
        table_names = [row[0] for row in cursor.fetchall()]
        tables = []
        
        # Get columns for each table
        for table_name in table_names:
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable
                FROM information_schema.columns
                WHERE table_schema = %s 
                AND table_name = %s
                ORDER BY ordinal_position;
            """, (schema, table_name))
            
            columns = [
                TableColumn(
                    name=row[0],
                    type=row[1],
                    nullable=(row[2] == 'YES')
                )
                for row in cursor.fetchall()
            ]
            
            tables.append(TableInfo(name=table_name, columns=columns))
        
        cursor.close()
        
        return SchemaResponse(
            success=True,
            tables=tables,
            message=f"Retrieved {len(tables)} table(s) from schema '{schema}'"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving schema: {str(e)}"
        )


@app.get("/api/database/status")
async def get_connection_status():
    """Get the status of active connections."""
    connections = []
    # iterate over a static list to avoid runtime errors if the dict is
    # modified concurrently by another request (eg. connect/disconnect)
    for conn_id, conn_data in list(active_connections.items()):
        info = conn_data["info"]
        connections.append({
            "connection_id": conn_id,
            "host": info["host"],
            "port": info["port"],
            "database": info["database"],
            "username": info["username"]
        })
    
    return {
        "active_connections": len(active_connections),
        "connections": connections
    }


@app.post("/api/database/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """Execute a SQL SELECT query against the active database connection."""
    try:
        connection_id = request.connection_id
        if not connection_id:
            if not active_connections:
                raise HTTPException(
                    status_code=400,
                    detail="No active database connection. Please connect first."
                )
            connection_id = list(active_connections.keys())[0]

        if connection_id not in active_connections:
            raise HTTPException(status_code=404, detail="Connection not found")

        conn = active_connections[connection_id]["connection"]

        # Check if connection is still alive; reconnect if needed
        try:
            conn.isolation_level  # probe
        except Exception:
            conn_info = active_connections[connection_id]["info"]
            conn = psycopg2.connect(
                host=conn_info["host"],
                port=conn_info["port"],
                database=conn_info["database"],
                user=conn_info["username"],
                password=conn_info["password"],
                connect_timeout=10
            )
            conn.autocommit = True
            active_connections[connection_id]["connection"] = conn

        cursor = conn.cursor()

        # Set schema search path if requested
        schema = request.schema
        if schema and schema != "public":
            cursor.execute(f"SET search_path TO {schema}, public;")

        cursor.execute(request.sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        raw_rows = cursor.fetchall()
        cursor.close()

        # Serialize rows: convert non-JSON-native types to strings
        rows: List[List[Any]] = []
        for row in raw_rows:
            serialized = []
            for val in row:
                if val is None or isinstance(val, (bool, int, float, str)):
                    serialized.append(val)
                else:
                    serialized.append(str(val))
            rows.append(serialized)

        return QueryResponse(
            success=True,
            columns=columns,
            rows=rows,
            row_count=len(rows),
            message=f"Query returned {len(rows)} row(s)"
        )

    except HTTPException:
        raise
    except psycopg2.Error as e:
        # Rollback any failed transaction to reset connection state
        try:
            conn.rollback()
        except:
            pass
        raise HTTPException(status_code=400, detail=f"SQL error: {e.pgerror or str(e)}")
    except Exception as e:
        # Rollback any failed transaction to reset connection state
        try:
            conn.rollback()
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}\n{traceback.format_exc()}")


if __name__ == "__main__":
    import uvicorn
    print("Starting Database API Server on http://localhost:8000")
    print("API Documentation available at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
