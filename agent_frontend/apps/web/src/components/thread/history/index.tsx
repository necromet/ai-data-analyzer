import { Button } from "@/components/ui/button";
import { useThreads } from "@/providers/Thread";
import { Thread } from "@langchain/langgraph-sdk";
import { useEffect, useCallback, useState } from "react";
import { getContentString } from "../utils";
import { useQueryState } from "nuqs";
import { Skeleton } from "@/components/ui/skeleton";
import { RefreshCw, Plus, AlertCircle } from "lucide-react";
import { toast } from "sonner";

function ThreadList({
  threads,
  onThreadClick,
}: {
  threads: Thread[];
  onThreadClick?: (threadId: string) => void;
}) {
  const [threadId, setThreadId] = useQueryState("threadId");

  if (threads.length === 0) {
    return (
      <div className="h-full flex items-center justify-center px-4">
        <p className="text-sm text-gray-500 text-center">
          No threads yet. Start a new conversation!
        </p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col w-full gap-2 items-start justify-start overflow-y-scroll px-2 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-gray-300 [&::-webkit-scrollbar-track]:bg-transparent">
      {threads.map((t) => {
        let itemText = t.thread_id;
        if (
          typeof t.values === "object" &&
          t.values &&
          "messages" in t.values &&
          Array.isArray(t.values.messages) &&
          t.values.messages?.length > 0
        ) {
          const firstMessage = t.values.messages[0];
          itemText = getContentString(firstMessage.content);
        }
        const isActive = t.thread_id === threadId;
        return (
          <div key={t.thread_id} className="w-full">
            <Button
              variant={isActive ? "secondary" : "ghost"}
              className={`text-left items-start justify-start font-normal w-full h-auto py-2 px-3 ${
                isActive ? "bg-gray-100 dark:bg-gray-800" : ""
              }`}
              onClick={(e) => {
                e.preventDefault();
                onThreadClick?.(t.thread_id);
                if (t.thread_id === threadId) return;
                setThreadId(t.thread_id);
              }}
            >
              <p className="truncate text-ellipsis text-sm">{itemText}</p>
            </Button>
          </div>
        );
      })}
    </div>
  );
}

function ThreadHistoryLoading() {
  return (
    <div className="h-full flex flex-col w-full gap-2 items-start justify-start overflow-y-scroll px-2 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-gray-300 [&::-webkit-scrollbar-track]:bg-transparent">
      {Array.from({ length: 30 }).map((_, i) => (
        <Skeleton key={`skeleton-${i}`} className="w-full h-10" />
      ))}
    </div>
  );
}

export default function ThreadHistory() {
  const { getThreads, threads, setThreads, threadsLoading, setThreadsLoading } =
    useThreads();
  const [, setThreadId] = useQueryState("threadId");
  const [error, setError] = useState<string | null>(null);

  const loadThreads = useCallback(() => {
    if (typeof window === "undefined") return;
    setThreadsLoading(true);
    setError(null);
    getThreads()
      .then((loadedThreads) => {
        setThreads(loadedThreads);
        console.log(`Loaded ${loadedThreads.length} threads from LangGraph`);
      })
      .catch((err) => {
        console.error("Error loading threads:", err);
        const errorMessage = err?.message || "Failed to load threads";
        setError(errorMessage);
        toast.error("Failed to load thread history", {
          description: errorMessage,
          richColors: true,
        });
      })
      .finally(() => setThreadsLoading(false));
  }, [getThreads, setThreads, setThreadsLoading]);

  useEffect(() => {
    loadThreads();
  }, [loadThreads]);

  const handleNewThread = () => {
    setThreadId(null);
  };

  return (
    <div className="h-full flex flex-col pt-4">
      <div className="px-4 pb-3 flex items-center justify-between gap-2">
        <Button
          onClick={handleNewThread}
          className="flex-1 gap-2"
          variant="default"
        >
          <Plus className="size-4" />
          New Thread
        </Button>
        <Button
          onClick={loadThreads}
          variant="outline"
          size="icon"
          disabled={threadsLoading}
        >
          <RefreshCw className={`size-4 ${threadsLoading ? "animate-spin" : ""}`} />
        </Button>
      </div>
      {error && (
        <div className="px-4 pb-3">
          <div className="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
            <AlertCircle className="size-4 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-red-800 dark:text-red-200">
              <p className="font-medium">Failed to load threads</p>
              <p className="text-xs mt-1 text-red-600 dark:text-red-300">{error}</p>
            </div>
          </div>
        </div>
      )}
      {threadsLoading ? (
        <ThreadHistoryLoading />
      ) : (
        <ThreadList threads={threads} />
      )}
    </div>
  );
}
