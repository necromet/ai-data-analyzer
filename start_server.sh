#!/usr/bin/env bash
# run_all.sh - simple CLI to start frontend, langgraph server, and DB API server
# Usage: ./run_all.sh start|stop|status|logs [service]
# Services: frontend, langgraph, db, all

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$ROOT_DIR/logs"
PID_DIR="$ROOT_DIR/pids"

mkdir -p "$LOG_DIR" "$PID_DIR"

# Default commands (can be overridden by env vars)
: ${FRONTEND_CMD:="cd '$ROOT_DIR/agent_frontend/apps/web' && npm run dev"}
: ${LANGGRAPH_CMD:="cd '$ROOT_DIR/langgraph_app' && '$ROOT_DIR/.venv/bin/langgraph' dev"}
: ${DB_CMD:="cd '$ROOT_DIR' && '$ROOT_DIR/.venv/bin/python' db_api_server.py"}

start_service() {
  name="$1"
  cmd="$2"
  log="$LOG_DIR/$name.log"
  pidfile="$PID_DIR/$name.pid"

  if [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo "$name is already running (PID $(cat "$pidfile"))."
    return
  fi

  echo "Starting $name... (logging to $log)"
  setsid bash -lc "$cmd" > "$log" 2>&1 &
  pid=$!
  echo $pid > "$pidfile"
  sleep 0.2
  echo "$name started with PID $pid"
}

stop_service() {
  name="$1"
  pidfile="$PID_DIR/$name.pid"

  if [ ! -f "$pidfile" ]; then
    echo "$name not running (no pidfile)."
    return
  fi

  pid=$(cat "$pidfile")
  if kill -0 "$pid" 2>/dev/null; then
    echo "Stopping $name (PID $pid)..."
    kill "$pid" || true
    sleep 0.5
    if kill -0 "$pid" 2>/dev/null; then
      echo "PID $pid still alive; killing..."
      kill -9 "$pid" || true
    fi
  else
    echo "Process $pid not running. Removing stale pidfile."
  fi
  rm -f "$pidfile"
}

status_service() {
  name="$1"
  pidfile="$PID_DIR/$name.pid"
  if [ -f "$pidfile" ]; then
    pid=$(cat "$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
      echo "$name: running (PID $pid)"
    else
      echo "$name: pidfile exists but process $pid not running"
    fi
  else
    echo "$name: not running"
  fi
}

logs_service() {
  name="$1"
  log="$LOG_DIR/$name.log"
  if [ ! -f "$log" ]; then
    echo "No logs for $name yet: $log"
    return
  fi
  tail -n +1 -f "$log"
}

case "${1:-}" in
  start)
    echo "Starting all services..."
    start_service frontend "$FRONTEND_CMD"
    start_service langgraph "$LANGGRAPH_CMD"
    start_service db "$DB_CMD"
    ;;
  stop)
    echo "Stopping all services..."
    stop_service frontend
    stop_service langgraph
    stop_service db
    ;;
  status)
    status_service frontend
    status_service langgraph
    status_service db
    ;;
  logs)
    svc=${2:-all}
    if [ "$svc" = "all" ]; then
      echo "Tailing all logs (press Ctrl-C to stop)."
      tail -n +1 -f "$LOG_DIR"/*.log
    else
      logs_service "$svc"
    fi
    ;;
  *)
    cat <<EOF
Usage: $0 {start|stop|status|logs [service]}

Commands:
  start         Start frontend, langgraph, and db services
  stop          Stop all services
  status        Show status of each service
  logs [svc]    Tail logs for a service (frontend|langgraph|db) or 'all'

You can override default commands by exporting environment variables before running:
  FRONTEND_CMD="cd path && npm run dev"
  LANGGRAPH_CMD="cd path && langgraph dev"
  DB_CMD="python3 db_api_server.py"

Logs: $LOG_DIR
PIDs:  $PID_DIR

Example:
  FRONTEND_CMD='cd agent_frontend/apps/web && npm run dev -- --host' ./run_all.sh start
EOF
    exit 1
    ;;
esac
