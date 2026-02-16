import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Database, Table, ChevronDown, ChevronRight, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";

const DB_API_URL = "http://localhost:8000";

interface TableInfo {
  name: string;
  columns: ColumnInfo[];
  expanded?: boolean;
}

interface ColumnInfo {
  name: string;
  type: string;
  nullable: boolean;
}

export default function DatabaseViewer() {
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [connectionId, setConnectionId] = useState<string | null>(null);
  const [schemas, setSchemas] = useState<string[]>([]);
  const [selectedSchema, setSelectedSchema] = useState<string>("public");
  const [isLoadingSchemas, setIsLoadingSchemas] = useState(false);

  const loadSchemas = useCallback(async (connId?: string) => {
    const activeConnectionId = connId || connectionId || localStorage.getItem("db_connection_id");
    
    if (!activeConnectionId) return;
    
    setIsLoadingSchemas(true);
    try {
      const response = await fetch(
        `${DB_API_URL}/api/database/schemas?connection_id=${encodeURIComponent(activeConnectionId)}`
      );

      if (!response.ok) {
        throw new Error("Failed to load schemas");
      }

      const data = await response.json();
      setSchemas(data.schemas);
    } catch (error) {
      console.error("Failed to load schemas", error);
    } finally {
      setIsLoadingSchemas(false);
    }
  }, [connectionId]);

  const loadTables = useCallback(async (connId?: string, schema?: string) => {
    const activeConnectionId = connId || connectionId || localStorage.getItem("db_connection_id");
    const activeSchema = schema || selectedSchema || localStorage.getItem("db_schema") || "public";
    
    if (!activeConnectionId) {
      toast.error("No database connection", {
        description: "Please connect to a database first",
        richColors: true,
      });
      return;
    }
    
    setSelectedSchema(activeSchema);
    setIsLoading(true);
    try {
      const response = await fetch(
        `${DB_API_URL}/api/database/schema?connection_id=${encodeURIComponent(activeConnectionId)}&schema=${encodeURIComponent(activeSchema)}`
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to load schema");
      }

      const data = await response.json();
      setTables(data.tables);
      setConnectionId(activeConnectionId);
      
      toast.success("Database schema loaded", {
        description: data.message || `Loaded ${data.tables.length} tables from '${activeSchema}'`,
        richColors: true,
      });
    } catch (error) {
      toast.error("Failed to load database schema", {
        description: error instanceof Error ? error.message : "Unknown error",
        richColors: true,
      });
      setTables([]);
      setConnectionId(null);
    } finally {
      setIsLoading(false);
    }
  }, [connectionId, selectedSchema]);

  useEffect(() => {
    // Check for existing connection on mount
    const storedConnectionId = localStorage.getItem("db_connection_id");
    const storedSchema = localStorage.getItem("db_schema") || "public";
    if (storedConnectionId) {
      setConnectionId(storedConnectionId);
      setSelectedSchema(storedSchema);
      loadSchemas(storedConnectionId);
      loadTables(storedConnectionId, storedSchema);
    }
    
    // Listen for connection events
    const handleConnected = (event: Event) => {
      const customEvent = event as CustomEvent;
      const connId = customEvent.detail?.connectionId;
      const schema = customEvent.detail?.schema || "public";
      if (connId) {
        setConnectionId(connId);
        setSelectedSchema(schema);
        loadSchemas(connId);
        loadTables(connId, schema);
      }
    };
    
    const handleDisconnected = () => {
      setConnectionId(null);
      setSchemas([]);
      setSelectedSchema("public");
      setTables([]);
    };
    
    window.addEventListener("database-connected", handleConnected);
    window.addEventListener("database-disconnected", handleDisconnected);
    
    return () => {
      window.removeEventListener("database-connected", handleConnected);
      window.removeEventListener("database-disconnected", handleDisconnected);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggleTable = (index: number) => {
    setTables((prevTables) =>
      prevTables.map((table, i) =>
        i === index ? { ...table, expanded: !table.expanded } : table
      )
    );
  };

  if (isLoading) {
    return (
      <div className="h-full flex flex-col w-full gap-4 p-4 overflow-y-auto [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-gray-300 [&::-webkit-scrollbar-track]:bg-transparent">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database className="size-5" />
                <CardTitle>Database Schema</CardTitle>
              </div>
            </div>
            <CardDescription>Loading database schema...</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="w-full h-10" />
            ))}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!connectionId || tables.length === 0) {
    return (
      <div className="h-full flex flex-col w-full gap-4 p-4 overflow-y-auto [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-gray-300 [&::-webkit-scrollbar-track]:bg-transparent">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Database className="size-5" />
              <CardTitle>Database Schema</CardTitle>
            </div>
            <CardDescription>
              {!connectionId 
                ? "No database connected. Connect to a database first." 
                : "No tables found in this schema"}
            </CardDescription>
            {schemas.length > 0 && (
              <div className="mt-3">
                <label className="text-sm text-gray-600 block mb-2">Select Schema:</label>
                <select
                  value={selectedSchema}
                  onChange={(e) => loadTables(undefined, e.target.value)}
                  disabled={isLoading}
                  className="w-full px-2 py-2 text-sm border border-gray-300 rounded-md bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {schemas.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </CardHeader>
          {connectionId && (
            <CardContent>
              <Button onClick={() => loadTables()} className="w-full">
                <RefreshCw className="size-4 mr-2" />
                Load Schema
              </Button>
            </CardContent>
          )}
        </Card>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col w-full gap-4 p-4 overflow-y-auto [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-gray-300 [&::-webkit-scrollbar-track]:bg-transparent">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 flex-1">
              <Database className="size-5" />
              <div className="flex flex-col gap-2 flex-1">
                <CardTitle>Database Schema</CardTitle>
                {schemas.length > 0 && (
                  <div className="flex items-center gap-2">
                    <label className="text-sm text-gray-600 whitespace-nowrap">Schema:</label>
                    <select
                      value={selectedSchema}
                      onChange={(e) => loadTables(undefined, e.target.value)}
                      disabled={isLoading}
                      className="px-2 py-1 text-sm border border-gray-300 rounded-md bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {schemas.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
            </div>
            <Button size="sm" variant="ghost" onClick={() => loadTables()} disabled={isLoading}>
              <RefreshCw className="size-4" />
            </Button>
          </div>
          <CardDescription>{tables.length} tables found</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          {tables.map((table, index) => (
            <div key={table.name} className="border rounded-md">
              <Button
                variant="ghost"
                className="w-full justify-start font-normal px-3 py-2 h-auto"
                onClick={() => toggleTable(index)}
              >
                <div className="flex items-center gap-2 w-full">
                  {table.expanded ? (
                    <ChevronDown className="size-4 flex-shrink-0" />
                  ) : (
                    <ChevronRight className="size-4 flex-shrink-0" />
                  )}
                  <Table className="size-4 flex-shrink-0" />
                  <span className="font-medium break-words">{table.name}</span>
                </div>
              </Button>

              {table.expanded && (
                <div className="px-3 pb-3 space-y-1">
                  <Separator className="mb-2" />
                  {table.columns.map((column) => (
                    <div
                      key={column.name}
                      className="flex items-center justify-between gap-2 text-sm py-1 pl-3"
                    >
                      <span className="font-mono text-xs break-all">{column.name}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
