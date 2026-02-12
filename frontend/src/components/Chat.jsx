import { useState, useRef, useEffect } from 'react';
import { createThread, streamAgentResponse } from '../services/langgraph';
import './Chat.css';

function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [threadId, setThreadId] = useState(null);
  const [error, setError] = useState(null);
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
        
        // Handle different LangGraph streaming event formats
        let messageContent = null;
        
        // Format 1: Array format ['messages', {...}]
        if (Array.isArray(data) && data[0] === 'messages' && data[1]) {
          const message = data[1];
          if (message.role === 'assistant' && message.content) {
            messageContent = typeof message.content === 'string' 
              ? message.content 
              : JSON.stringify(message.content);
          }
        }
        // Format 2: Object with event property
        else if (data.event === 'messages/partial' || data.event === 'messages/complete') {
          if (data.data && data.data.content) {
            messageContent = typeof data.data.content === 'string'
              ? data.data.content
              : JSON.stringify(data.data.content);
          }
        }
        // Format 3: Direct message object
        else if (data.role === 'assistant' && data.content) {
          messageContent = typeof data.content === 'string'
            ? data.content
            : JSON.stringify(data.content);
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
      setError('Failed to send message. Make sure LangGraph dev server is running on port 2024.');
      console.error(err);
      // Remove the empty assistant message
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
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
              {msg.role === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message-content">
              <div className="message-role">{msg.role === 'user' ? 'You' : 'Assistant'}</div>
              <div className="message-text">
                {msg.content || (msg.isStreaming ? 'Thinking...' : '')}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about your data..."
          disabled={isLoading || !threadId}
          className="message-input"
        />
        <button 
          type="submit" 
          disabled={isLoading || !threadId || !input.trim()}
          className="send-button"
        >
          {isLoading ? '⏳' : '📤'}
        </button>
      </form>
    </div>
  );
}

export default Chat;
