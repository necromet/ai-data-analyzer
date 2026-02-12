/**
 * LangGraph API Service
 * Handles communication with the LangGraph backend
 */

const API_BASE_URL = '/';  // Proxied through Vite to localhost:2024

/**
 * Create a new thread for conversation
 */
export async function createThread() {
  const response = await fetch(`${API_BASE_URL}threads`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({})
  });
  
  if (!response.ok) {
    throw new Error('Failed to create thread');
  }
  
  return response.json();
}

/**
 * Send a message to the agent and stream the response
 * @param {string} threadId - The thread ID
 * @param {string} message - The user message
 * @param {Function} onChunk - Callback for each streamed chunk
 */
export async function streamAgentResponse(threadId, message, onChunk) {
  const response = await fetch(`${API_BASE_URL}runs/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      assistant_id: 'agent',
      thread_id: threadId,
      input: {
        messages: [
          {
            role: 'user',
            content: message
          }
        ]
      },
      stream_mode: 'messages'
    })
  });

  if (!response.ok) {
    throw new Error('Failed to send message');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    
    if (done) break;
    
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    
    // Keep the last incomplete line in the buffer
    buffer = lines.pop() || '';
    
    for (const line of lines) {
      const trimmedLine = line.trim();
      if (!trimmedLine) continue;
      
      if (trimmedLine.startsWith('data: ')) {
        try {
          const jsonStr = trimmedLine.slice(6);
          const data = JSON.parse(jsonStr);
          console.log('Streaming event:', data);
          onChunk(data);
        } catch (e) {
          console.error('Failed to parse chunk:', trimmedLine, e);
        }
      } else if (trimmedLine.startsWith('event: ')) {
        console.log('Event type:', trimmedLine.slice(7));
      }
    }
  }
}

/**
 * Send a message without streaming
 * @param {string} threadId - The thread ID  
 * @param {string} message - The user message
 */
export async function sendMessage(threadId, message) {
  const response = await fetch(`${API_BASE_URL}runs/wait`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      assistant_id: 'agent',
      thread_id: threadId,
      input: {
        messages: [
          {
            role: 'user',
            content: message
          }
        ]
      }
    })
  });

  if (!response.ok) {
    throw new Error('Failed to send message');
  }

  return response.json();
}

/**
 * Get thread history
 * @param {string} threadId - The thread ID
 */
export async function getThreadHistory(threadId) {
  const response = await fetch(`${API_BASE_URL}threads/${threadId}/state`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    }
  });

  if (!response.ok) {
    throw new Error('Failed to get thread history');
  }

  return response.json();
}
