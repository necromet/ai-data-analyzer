import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Database, CheckCircle2, XCircle } from "lucide-react";
import { toast } from "sonner";

const DB_API_URL = "http://localhost:8000";

type ConnectionStatus = "disconnected" | "connecting" | "connected" | "error";

interface DatabaseConnectionInfo {
  host: string;
  port: string;
  database: string;
  username: string;
  password: string;
  schema: string;
}

export default function DatabaseConnector() {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("disconnected");
  const [connectionId, setConnectionId] = useState<string | null>(null);
  const [connectionInfo, setConnectionInfo] = useState<DatabaseConnectionInfo>({
    host: "localhost",
    port: "5432",
    database: "",
    username: "",
    password: "",
    schema: "public",
  });

  // Restore connection state from localStorage on mount
  useEffect(() => {
    const storedConnectionId = localStorage.getItem("db_connection_id");
    const storedSchema = localStorage.getItem("db_schema");
    
    if (storedConnectionId) {
      setConnectionId(storedConnectionId);
      setConnectionStatus("connected");
      
      if (storedSchema) {
        setConnectionInfo(prev => ({ ...prev, schema: storedSchema }));
      }
    }
  }, []);

  const handleConnect = async () => {
    if (!connectionInfo.database || !connectionInfo.username) {
      toast.error("Please fill in all required fields", {
        description: "Database name and username are required",
        richColors: true,
      });
      return;
    }

    setConnectionStatus("connecting");

    try {
      const response = await fetch(`${DB_API_URL}/api/database/connect`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          host: connectionInfo.host,
          port: parseInt(connectionInfo.port, 10),
          database: connectionInfo.database,
          username: connectionInfo.username,
          password: connectionInfo.password,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Connection failed");
      }

      const data = await response.json();
      setConnectionId(data.connection_id);
      setConnectionStatus("connected");
      
      // Store connection ID and schema in localStorage for other components
      localStorage.setItem("db_connection_id", data.connection_id);
      localStorage.setItem("db_schema", connectionInfo.schema);
      
      toast.success("Database connected successfully", {
        description: data.message,
        richColors: true,
      });
      
      // Dispatch custom event to notify other components (including viewer to auto-load schema)
      window.dispatchEvent(new CustomEvent("database-connected", { 
        detail: { 
          connectionId: data.connection_id,
          schema: connectionInfo.schema
        } 
      }));
    } catch (error) {
      setConnectionStatus("error");
      toast.error("Failed to connect to database", {
        description: error instanceof Error ? error.message : "Unknown error",
        richColors: true,
      });
    }
  };

  const handleDisconnect = async () => {
    if (!connectionId) return;
    
    try {
      await fetch(`${DB_API_URL}/api/database/disconnect?connection_id=${encodeURIComponent(connectionId)}`, {
        method: "POST",
      });
      
      setConnectionStatus("disconnected");
      setConnectionId(null);
      localStorage.removeItem("db_connection_id");
      localStorage.removeItem("db_schema");
      
      // Dispatch custom event to notify other components
      window.dispatchEvent(new Event("database-disconnected"));
      
      toast.info("Database disconnected", {
        richColors: true,
      });
    } catch (error) {
      toast.error("Failed to disconnect", {
        description: error instanceof Error ? error.message : "Unknown error",
        richColors: true,
      });
    }
  };

  const isConnected = connectionStatus === "connected";
  const isConnecting = connectionStatus === "connecting";

  return (
    <div className="h-full flex flex-col w-full gap-4 p-4 overflow-y-auto [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-gray-300 [&::-webkit-scrollbar-track]:bg-transparent">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Database className="size-5" />
              <CardTitle>Database Connection</CardTitle>
            </div>
            {isConnected && (
              <CheckCircle2 className="size-5 text-green-600" />
            )}
            {connectionStatus === "error" && (
              <XCircle className="size-5 text-red-600" />
            )}
          </div>
          <CardDescription>
            {isConnected
              ? "Connected to database"
              : "Configure and connect to your database"}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="host">Host</Label>
            <Input
              id="host"
              value={connectionInfo.host}
              onChange={(e) =>
                setConnectionInfo({ ...connectionInfo, host: e.target.value })
              }
              disabled={isConnected}
              placeholder="localhost"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="port">Port</Label>
            <Input
              id="port"
              value={connectionInfo.port}
              onChange={(e) =>
                setConnectionInfo({ ...connectionInfo, port: e.target.value })
              }
              disabled={isConnected}
              placeholder="5432"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="database">Database Name *</Label>
            <Input
              id="database"
              value={connectionInfo.database}
              onChange={(e) =>
                setConnectionInfo({ ...connectionInfo, database: e.target.value })
              }
              disabled={isConnected}
              placeholder="olist_db"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="username">Username *</Label>
            <Input
              id="username"
              value={connectionInfo.username}
              onChange={(e) =>
                setConnectionInfo({ ...connectionInfo, username: e.target.value })
              }
              disabled={isConnected}
              placeholder="postgres"
              required
            />
          </div>
        
            <div className="space-y-2">
                <Label htmlFor="password">Password *</Label>
                <Input
                id="password"
                type="password"
                value={connectionInfo.password}
                onChange={(e) =>
                    setConnectionInfo({ ...connectionInfo, password: e.target.value })
                }
                disabled={isConnected}
                placeholder="********"
                required
                />
            </div>

          <Separator />

          <div className="flex gap-2">
            {!isConnected ? (
              <Button
                onClick={handleConnect}
                disabled={isConnecting}
                className="w-full"
              >
                {isConnecting ? "Connecting..." : "Connect"}
              </Button>
            ) : (
              <Button
                onClick={handleDisconnect}
                variant="outline"
                className="w-full"
              >
                Disconnect
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
