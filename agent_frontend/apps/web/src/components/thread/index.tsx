import { v4 as uuidv4 } from "uuid";
import { ReactNode, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { useStreamContext } from "@/providers/Stream";
import { useState, FormEvent } from "react";
import { Button } from "../ui/button";
import { Checkpoint, Message } from "@langchain/langgraph-sdk";
import { AssistantMessage, AssistantMessageLoading } from "./messages/ai";
import { HumanMessage } from "./messages/human";
import {
  DO_NOT_RENDER_ID_PREFIX,
  ensureToolCallsHaveResponses,
} from "@/lib/ensure-tool-responses";
import { isAgentInboxInterruptSchema } from "@/lib/agent-inbox-interrupt";
import { ThreadView } from "./agent-inbox";
import { GenericInterruptView } from "./messages/generic-interrupt";
import { CometSVG } from "../icons/comet";
import { TooltipIconButton } from "./tooltip-icon-button";
import {
  ArrowDown,
  LoaderCircle,
  PanelRightOpen,
  PanelRightClose,
  SquarePen,
  Moon,
  Sun,
  ChevronDown,
  Database,
} from "lucide-react";
import { useQueryState, parseAsBoolean } from "nuqs";
import { StickToBottom, useStickToBottomContext } from "use-stick-to-bottom";
import Sidebar from "../sidebar";
import { toast } from "sonner";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { Label } from "../ui/label";
import { Switch } from "../ui/switch";
import { GitHubSVG } from "../icons/github";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../ui/tooltip";
import {
  Sheet,
  SheetContent,
} from "../ui/sheet";

function StickyToBottomContent(props: {
  content: ReactNode;
  footer?: ReactNode;
  className?: string;
  contentClassName?: string;
}) {
  const context = useStickToBottomContext();
  return (
    <div
      ref={context.scrollRef}
      style={{ width: "100%", height: "100%" }}
      className={props.className}
    >
      <div ref={context.contentRef} className={props.contentClassName}>
        {props.content}
      </div>

      {props.footer}
    </div>
  );
}

function ScrollToBottom(props: { className?: string }) {
  const { isAtBottom, scrollToBottom } = useStickToBottomContext();

  if (isAtBottom) return null;
  return (
    <Button
      variant="outline"
      className={props.className}
      onClick={() => scrollToBottom()}
    >
      <ArrowDown className="w-4 h-4" />
      <span>Scroll to bottom</span>
    </Button>
  );
}

function OpenGitHubRepo() {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <a
            href="https://github.com/necromet"
            target="_blank"
            className="flex items-center justify-center"
          >
            <GitHubSVG width="24" height="24" />
          </a>
        </TooltipTrigger>
        <TooltipContent side="left">
          <p>Open GitHub repo</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

function DarkModeToggle() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const isDarkMode = document.documentElement.classList.contains("dark");
    setIsDark(isDarkMode);
  }, []);

  const toggleDarkMode = () => {
    const newDarkMode = !isDark;
    setIsDark(newDarkMode);
    if (newDarkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            onClick={toggleDarkMode}
            className="flex items-center justify-center hover:opacity-70 transition-opacity"
            aria-label="Toggle dark mode"
          >
            {isDark ? (
              <Sun className="size-5" />
            ) : (
              <Moon className="size-5" />
            )}
          </button>
        </TooltipTrigger>
        <TooltipContent side="left">
          <p>{isDark ? "Switch to light mode" : "Switch to dark mode"}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

const OLIST_TABLES = [
  { name: "customers", desc: "Customer data with unique IDs and location info" },
  { name: "geolocation", desc: "ZIP code to lat/lng coordinates mapping" },
  { name: "order_items", desc: "Individual items within each order (product, seller, price, freight)" },
  { name: "order_payments", desc: "Payment details per order (type, installments, value)" },
  { name: "order_reviews", desc: "Customer reviews and ratings for orders" },
  { name: "orders", desc: "Order records with status and timestamps (purchased, shipped, delivered)" },
  { name: "product_category", desc: "Product category translations (Portuguese to English)" },
  { name: "products", desc: "Product catalog with dimensions, weight, and category" },
  { name: "sellers", desc: "Seller data with unique IDs and location info" },
];

function DatasetInfo() {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="w-full max-w-2xl mx-auto mt-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors py-2"
      >
        <Database className="size-4" />
        <span>About the dataset</span>
        <motion.div
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown className="size-4" />
        </motion.div>
      </button>
      <AnimatePresence initial={false}>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="border rounded-lg p-4 mt-2 bg-muted/30 text-sm text-muted-foreground space-y-3 max-h-[35vh] overflow-y-auto [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-gray-300 [&::-webkit-scrollbar-track]:bg-transparent">
              <p>
                This app is connected to the <strong className="text-foreground">Olist Brazilian E-Commerce</strong> dataset
                — a real public dataset of ~100k orders from a Brazilian marketplace (2016–2018).
              </p>
              <div className="space-y-1.5">
                {OLIST_TABLES.map((t) => (
                  <div key={t.name} className="flex gap-2">
                    <code className="text-xs bg-muted px-1.5 py-0.5 rounded font-mono text-foreground whitespace-nowrap">
                      {t.name}
                    </code>
                    <span className="text-xs leading-5">{t.desc}</span>
                  </div>
                ))}
              </div>
              <p className="text-xs">
                Try asking questions like <em>"What are the top 10 product categories by revenue?"</em> or <em>"Show me average delivery time by state."</em>
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function Thread() {
  const [threadId, setThreadId] = useQueryState("threadId");
  const [chatHistoryOpen, setChatHistoryOpen] = useQueryState(
    "chatHistoryOpen",
    parseAsBoolean.withDefault(false),
  );
  const [hideToolCalls, setHideToolCalls] = useQueryState(
    "hideToolCalls",
    parseAsBoolean.withDefault(false),
  );
  const [input, setInput] = useState("");
  const [firstTokenReceived, setFirstTokenReceived] = useState(false);
  const [isDatabaseConnected, setIsDatabaseConnected] = useState(false);
  const isLargeScreen = useMediaQuery("(min-width: 1024px)");

  const stream = useStreamContext();
  const messages = stream.messages;
  const isLoading = stream.isLoading;

  const lastError = useRef<string | undefined>(undefined);

  // Check database connection status on mount and listen for connection events
  useEffect(() => {
    const checkDatabaseConnection = () => {
      const connectionId = localStorage.getItem("db_connection_id");
      setIsDatabaseConnected(!!connectionId);
    };

    // Check on mount
    checkDatabaseConnection();

    // Listen for database connection events
    const handleDatabaseConnected = () => {
      setIsDatabaseConnected(true);
    };

    const handleDatabaseDisconnected = () => {
      setIsDatabaseConnected(false);
    };

    window.addEventListener("database-connected", handleDatabaseConnected);
    window.addEventListener("database-disconnected", handleDatabaseDisconnected);

    return () => {
      window.removeEventListener("database-connected", handleDatabaseConnected);
      window.removeEventListener("database-disconnected", handleDatabaseDisconnected);
    };
  }, []);

  useEffect(() => {
    if (!stream.error) {
      lastError.current = undefined;
      return;
    }
    try {
      const message = (stream.error as any).message;
      if (!message || lastError.current === message) {
        // Message has already been logged. do not modify ref, return early.
        return;
      }

      // Message is defined, and it has not been logged yet. Save it, and send the error
      lastError.current = message;
      toast.error("An error occurred. Please try again.", {
        description: (
          <p>
            <strong>Error:</strong> <code>{message}</code>
          </p>
        ),
        richColors: true,
        closeButton: true,
      });
    } catch {
      // no-op
    }
  }, [stream.error]);

  // TODO: this should be part of the useStream hook
  const prevMessageLength = useRef(0);
  useEffect(() => {
    if (
      messages.length !== prevMessageLength.current &&
      messages?.length &&
      messages[messages.length - 1].type === "ai"
    ) {
      setFirstTokenReceived(true);
    }

    prevMessageLength.current = messages.length;
  }, [messages]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    // Check if database is connected
    if (!isDatabaseConnected) {
      toast.error("Database not connected", {
        description: "Please connect to a database before starting a chat. Open the sidebar to configure your database connection.",
        richColors: true,
        closeButton: true,
      });
      return;
    }

    setFirstTokenReceived(false);

    const newHumanMessage: Message = {
      id: uuidv4(),
      type: "human",
      content: input,
    };

    const toolMessages = ensureToolCallsHaveResponses(stream.messages);
    stream.submit(
      { messages: [...toolMessages, newHumanMessage] },
      {
        streamMode: ["values"],
        optimisticValues: (prev) => ({
          ...prev,
          messages: [
            ...(prev.messages ?? []),
            ...toolMessages,
            newHumanMessage,
          ],
        }),
      },
    );

    setInput("");
  };

  const handleRegenerate = (
    parentCheckpoint: Checkpoint | null | undefined,
  ) => {
    // Do this so the loading state is correct
    prevMessageLength.current = prevMessageLength.current - 1;
    setFirstTokenReceived(false);
    stream.submit(undefined, {
      checkpoint: parentCheckpoint,
      streamMode: ["values"],
    });
  };

  const chatStarted = !!threadId || !!messages.length;
  const hasNoAIOrToolMessages = !messages.find(
    (m) => m.type === "ai" || m.type === "tool",
  );

  return (
    <div className="flex w-full h-screen overflow-hidden">
      <div className="relative lg:flex hidden">
        <motion.div
          className="absolute h-full border-r bg-white dark:bg-gray-950 overflow-hidden z-20"
          style={{ width: 300 }}
          animate={
            isLargeScreen
              ? { x: chatHistoryOpen ? 0 : -300 }
              : { x: chatHistoryOpen ? 0 : -300 }
          }
          initial={{ x: -300 }}
          transition={
            isLargeScreen
              ? { type: "spring", stiffness: 300, damping: 30 }
              : { duration: 0 }
          }
        >
          <div className="relative h-full" style={{ width: 300 }}>
            <Sidebar />
          </div>
        </motion.div>
      </div>
      <div className="lg:hidden">
        <Sheet
          open={!!chatHistoryOpen && !isLargeScreen}
          onOpenChange={(open) => {
            if (isLargeScreen) return;
            setChatHistoryOpen(open);
          }}
        >
          <SheetContent side="left" className="lg:hidden flex p-0 w-[300px]">
            <Sidebar />
          </SheetContent>
        </Sheet>
      </div>
      <motion.div
        className={cn(
          "flex-1 flex flex-col min-w-0 overflow-hidden relative",
          !chatStarted && "grid-rows-[1fr]",
        )}
        layout={isLargeScreen}
        animate={{
          marginLeft: chatHistoryOpen ? (isLargeScreen ? 300 : 0) : 0,
          width: chatHistoryOpen
            ? isLargeScreen
              ? "calc(100% - 300px)"
              : "100%"
            : "100%",
        }}
        transition={
          isLargeScreen
            ? { type: "spring", stiffness: 300, damping: 30 }
            : { duration: 0 }
        }
      >
        {!chatStarted && (
          <div className="absolute top-0 left-0 w-full flex items-center gap-3 p-2 pl-4 z-10 h-12">
            <div className="flex items-center">
              <Button
                className="h-9 w-9 rounded-md bg-background hover:bg-muted"
                variant="ghost"
                onClick={() => setChatHistoryOpen((p) => !p)}
              >
                {chatHistoryOpen ? (
                  <PanelRightOpen className="size-5" />
                ) : (
                  <PanelRightClose className="size-5" />
                )}
              </Button>
              <div className="h-9 rounded-r-md bg-background flex items-center px-2">
                <OpenGitHubRepo />
              </div>
            </div>
          </div>
        )}
        {chatStarted && (
          <div className="flex items-center justify-between gap-3 p-2 z-10 relative h-12">
            <div className="flex items-center justify-start gap-2 relative">
              <div className="flex items-center z-10">
                <Button
                  className="h-9 w-9 rounded-md bg-background hover:bg-muted"
                  variant="ghost"
                  onClick={() => setChatHistoryOpen((p) => !p)}
                >
                  {chatHistoryOpen ? (
                    <PanelRightOpen className="size-5" />
                  ) : (
                    <PanelRightClose className="size-5" />
                  )}
                </Button>
                <motion.button
                  className="flex gap-2 items-center cursor-pointer h-9 rounded-md bg-background px-2"
                  onClick={() => setThreadId(null)}
                  animate={{
                    marginLeft: !chatHistoryOpen ? 0 : 0,
                  }}
                  transition={{
                    type: "spring",
                    stiffness: 300,
                    damping: 30,
                  }}
                >
                  <CometSVG width={24} height={24} />
                  <span className="text-lg font-semibold tracking-tight">
                    Comet
                  </span>
                </motion.button>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-3">
                <OpenGitHubRepo />
              </div>
              <TooltipIconButton
                size="lg"
                className="p-4"
                tooltip="New thread"
                variant="ghost"
                onClick={() => setThreadId(null)}
              >
                <SquarePen className="size-5" />
              </TooltipIconButton>
            </div>

            <div className="absolute inset-x-0 top-full h-5 bg-gradient-to-b from-background to-background/0" />
          </div>
        )}

        <StickToBottom className="relative flex-1 overflow-hidden">
          <StickyToBottomContent
            className={cn(
              "absolute px-4 inset-0 overflow-y-scroll [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-gray-300 [&::-webkit-scrollbar-track]:bg-transparent",
              !chatStarted && "flex flex-col items-stretch mt-[25vh]",
              chatStarted && "grid grid-rows-[1fr_auto]",
            )}
            contentClassName="pt-8 pb-16  max-w-3xl mx-auto flex flex-col gap-4 w-full"
            content={
              <>
                {messages
                  .filter((m) => !m.id?.startsWith(DO_NOT_RENDER_ID_PREFIX))
                  .map((message, index) =>
                    message.type === "human" ? (
                      <HumanMessage
                        key={message.id || `${message.type}-${index}`}
                        message={message}
                        isLoading={isLoading}
                      />
                    ) : (
                      <AssistantMessage
                        key={message.id || `${message.type}-${index}`}
                        message={message}
                        isLoading={isLoading}
                        handleRegenerate={handleRegenerate}
                      />
                    ),
                  )}
                {/* Render interrupt once, after all messages */}
                {!!stream.interrupt && (
                  <div className="flex items-start mr-auto gap-2 flex-wrap">
                    <div className="flex flex-col gap-2 w-full">
                      {isAgentInboxInterruptSchema(stream.interrupt.value) ? (
                        <ThreadView interrupt={stream.interrupt.value} />
                      ) : (
                        <GenericInterruptView interrupt={stream.interrupt.value || {}} />
                      )}
                    </div>
                  </div>
                )}
                {isLoading && !firstTokenReceived && (
                  <AssistantMessageLoading />
                )}
              </>
            }
            footer={
              <div className="sticky flex flex-col items-center gap-8 bottom-0">
                {!chatStarted && (
                  <div className="flex flex-col items-center gap-2">
                    <div className="flex gap-3 items-center">
                      <CometSVG className="flex-shrink-0 h-12" />
                      <h1 className="text-2xl font-semibold tracking-tight">
                        Comet
                      </h1>
                    </div>
                    <p className="text-sm text-muted-foreground text-center max-w-md">
                      Ask questions about your data in plain English. Comet writes the SQL, runs the query, and returns insights with visualizations.
                    </p>
                    <DatasetInfo />
                  </div>
                )}

                <ScrollToBottom className="absolute bottom-full left-1/2 -translate-x-1/2 mb-4 animate-in fade-in-0 zoom-in-95" />

                <div className="bg-muted rounded-2xl border shadow-xs mx-auto mb-8 w-full max-w-3xl relative z-10">
                  <form
                    onSubmit={handleSubmit}
                    className="grid grid-rows-[1fr_auto] gap-2 max-w-3xl mx-auto"
                  >
                    <textarea
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (
                          e.key === "Enter" &&
                          !e.shiftKey &&
                          !e.metaKey &&
                          !e.nativeEvent.isComposing
                        ) {
                          e.preventDefault();
                          const el = e.target as HTMLElement | undefined;
                          const form = el?.closest("form");
                          form?.requestSubmit();
                        }
                      }}
                      placeholder="Type your message..."
                      className="p-3.5 pb-0 border-none bg-transparent field-sizing-content shadow-none ring-0 outline-none focus:outline-none focus:ring-0 resize-none"
                    />

                    <div className="flex items-center justify-between p-2 pt-4">
                      <div>
                        <div className="flex items-center space-x-2">
                        </div>
                      </div>
                      {stream.isLoading ? (
                        <Button key="stop" onClick={() => stream.stop()}>
                          <LoaderCircle className="w-4 h-4 animate-spin" />
                          Cancel
                        </Button>
                      ) : (
                        <Button
                          type="submit"
                          className="transition-all shadow-md"
                          disabled={isLoading || !input.trim() || !isDatabaseConnected}
                        >
                          Send
                        </Button>
                      )}
                    </div>
                  </form>
                </div>
              </div>
            }
          />
        </StickToBottom>
      </motion.div>
    </div>
  );
}
