import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Authentication API
export const authAPI = {
  login: async (username, password) => {
    const response = await api.post('/auth/login', { username, password });
    return response.data;
  },

  createUser: async (username, password, email, role = 'user') => {
    const response = await api.post('/auth/create_user', {
      username,
      password,
      email,
      role,
    });
    return response.data;
  },
};

// Chat/Query API
export const chatAPI = {
  sendMessage: async (query, chatHistory = []) => {
    const response = await api.post('/query', {
      query,
      chat_history: chatHistory,
      use_react: true,
    });
    return response.data;
  },

  sendMessageStream: async (query, chatHistory = [], onChunk) => {
    const response = await fetch(`${API_BASE_URL}/query/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        chat_history: chatHistory,
        use_react: true,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          break;
        }

        // Decode the chunk and add to buffer
        buffer += decoder.decode(value, { stream: true });

        // Split by newlines to get complete JSON objects
        const lines = buffer.split('\n');

        // Keep the last incomplete line in the buffer
        buffer = lines.pop() || '';

        // Process each complete line
        for (const line of lines) {
          if (line.trim()) {
            try {
              const chunk = JSON.parse(line);
              onChunk(chunk);
            } catch (error) {
              console.error('Failed to parse chunk:', line, error);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  },

  getTools: async () => {
    const response = await api.get('/tools');
    return response.data;
  },
};

// Health Check
export const healthAPI = {
  check: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
