import { useState, useRef, useEffect } from 'react';
import { createThread, streamAgentResponse, resumeRun } from '../services/langgraph';
import './Chat.css';

function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [threadId, setThreadId] = useState(null);
  const [error, setError] = useState(null);
  const [isPaused, setIsPaused] = useState(false);
  const [generatedSql, setGeneratedSql] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize thread on mount
  useEffect(() => {
    async function initThread() {
      try {
        const thread = await createThread();
        setThreadId(thread.thread_id);
      } catch (err) {
        setError('Failed to initialize chat. Make sure LangGraph dev server is running.');
        console.error(err);
      }
    }
    initThread();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || !threadId || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setError(null);

    // Add user message to chat
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    // Add placeholder for assistant response
    const assistantMessageIndex = messages.length + 1;
    setMessages(prev => [...prev, { role: 'assistant', content: '', isStreaming: true }]);

    try {
      await streamAgentResponse(threadId, userMessage, (data) => {
        console.log('Received data:', data);
        
        let messageContent = null;
        
        // Check if we're at a breakpoint (generated_sql exists but no final_response)
        if (data && data.generated_sql && !data.final_response) {
          console.log('Human review breakpoint detected');
          setGeneratedSql(data.generated_sql);
          setIsPaused(true);
          setIsLoading(false);
          
          // Update message to show we're waiting for review
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[assistantMessageIndex] = {
              role: 'assistant',
              content: 'I\'ve generated a SQL query that needs your review before execution.',
              isStreaming: false,
              needsReview: true
            };
            return newMessages;
          });
          return;
        }
        
        // stream_mode='values' returns the full graph state
        // Look for final_response directly in the state object
        if (data && data.final_response) {
          messageContent = typeof data.final_response === 'string'
            ? data.final_response
            : JSON.stringify(data.final_response);
        }
        // Also check inside node update wrappers (stream_mode='updates' format)
        else if (data && typeof data === 'object') {
          for (const nodeOutput of Object.values(data)) {
            if (nodeOutput && nodeOutput.final_response) {
              messageContent = typeof nodeOutput.final_response === 'string'
                ? nodeOutput.final_response
                : JSON.stringify(nodeOutput.final_response);
              break;
            }
          }
        }
        
        if (messageContent) {
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[assistantMessageIndex] = {
              role: 'assistant',
              content: messageContent,
              isStreaming: true
            };
            return newMessages;
          });
        }
      });

      // Mark streaming as complete (only if not paused)
      if (!isPaused) {
        setMessages(prev => {
          const newMessages = [...prev];
          if (newMessages[assistantMessageIndex]) {
            newMessages[assistantMessageIndex].isStreaming = false;
          }
          return newMessages;
        });
      }
    } catch (err) {
      setError('Failed to send message. Make sure LangGraph dev server is running on port 2024.');
      console.error(err);
      // Remove the empty assistant message
      setMessages(prev => prev.slice(0, -1));
    } finally {
      if (!isPaused) {
        setIsLoading(false);
      }
    }
  };

  const handleApprove = async () => {
    setIsPaused(false);
    setIsLoading(true);
    setError(null);

    // Add a message showing we approved
    setMessages(prev => [...prev, {
      role: 'system',
      content: '✓ SQL query approved. Executing...'
    }]);

    // Add placeholder for final response
    const assistantMessageIndex = messages.length + 1;
    setMessages(prev => [...prev, { role: 'assistant', content: '', isStreaming: true }]);

    try {
      await resumeRun(threadId, (data) => {
        console.log('Resume data:', data);
        
        let messageContent = null;
        
        if (data && data.final_response) {
          messageContent = typeof data.final_response === 'string'
            ? data.final_response
            : JSON.stringify(data.final_response);
        }
        else if (data && typeof data === 'object') {
          for (const nodeOutput of Object.values(data)) {
            if (nodeOutput && nodeOutput.final_response) {
              messageContent = typeof nodeOutput.final_response === 'string'
                ? nodeOutput.final_response
                : JSON.stringify(nodeOutput.final_response);
              break;
            }
          }
        }
        
        if (messageContent) {
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[assistantMessageIndex] = {
              role: 'assistant',
              content: messageContent,
              isStreaming: true
            };
            return newMessages;
          });
        }
      });

      // Mark streaming as complete
      setMessages(prev => {
        const newMessages = [...prev];
        if (newMessages[assistantMessageIndex]) {
          newMessages[assistantMessageIndex].isStreaming = false;
        }
        return newMessages;
      });
    } catch (err) {
      setError('Failed to resume execution.');
      console.error(err);
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
      setGeneratedSql(null);
    }
  };

  const handleReject = () => {
    setIsPaused(false);
    setGeneratedSql(null);
    setIsLoading(false);
    
    // Add a message showing we rejected
    setMessages(prev => [...prev, {
      role: 'system',
      content: '✗ SQL query rejected. Please provide more guidance or ask a different question.'
    }]);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>AI Data Analyzer</h2>
        {threadId && <span className="thread-id">Thread: {threadId.slice(0, 8)}...</span>}
      </div>

      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      <div className="messages-container">
        {messages.length === 0 && (
          <div className="welcome-message">
            <h3>Welcome to AI Data Analyzer</h3>
            <p>Ask questions about your e-commerce data and get insights with visualizations.</p>
            <div className="example-queries">
              <p><strong>Try asking:</strong></p>
              <ul>
                <li>"What are the top selling products?"</li>
                <li>"Show me revenue trends over time"</li>
                <li>"Which cities have the most customers?"</li>
              </ul>
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'user' ? '👤' : msg.role === 'system' ? '⚙️' : '🤖'}
            </div>
            <div className="message-content">
              <div className="message-role">
                {msg.role === 'user' ? 'You' : msg.role === 'system' ? 'System' : 'Assistant'}
              </div>
              <div className="message-text">
                {msg.content || (msg.isStreaming ? 'Thinking...' : '')}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {isPaused && generatedSql && (
        <div className="review-panel">
          <div className="review-header">
            <span className="review-icon">🔍</span>
            <h3>SQL Query Review Required</h3>
          </div>
          <div className="review-content">
            <p className="review-description">
              Please review the generated SQL query before execution:
            </p>
            <pre className="sql-preview">
              <code>{generatedSql}</code>
            </pre>
            <div className="review-actions">
              <button 
                onClick={handleApprove} 
                className="btn-approve"
                disabled={isLoading}
              >
                ✓ Approve & Execute
              </button>
              <button 
                onClick={handleReject} 
                className="btn-reject"
                disabled={isLoading}
              >
                ✗ Reject
              </button>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={isPaused ? "Please review the SQL query above..." : "Ask a question about your data..."}
          disabled={isLoading || !threadId || isPaused}
          className="message-input"
        />
        <button 
          type="submit" 
          disabled={isLoading || !threadId || !input.trim() || isPaused}
          className="send-button"
        >
          {isLoading ? '⏳' : '📤'}
        </button>
      </form>
    </div>
  );
}

export default Chat;
