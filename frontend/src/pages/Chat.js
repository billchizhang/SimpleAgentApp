import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { chatAPI } from '../services/api';
import AdminSidebar from '../components/AdminSidebar';
import '../styles/Chat.css';

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);

  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = {
      type: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const userQuery = input;
    setInput('');
    setLoading(true);

    // Create placeholder for streaming response
    const agentMessageId = Date.now();
    const agentMessage = {
      id: agentMessageId,
      type: 'agent',
      content: '',
      steps: [],
      timestamp: new Date().toLocaleTimeString(),
      streaming: true,
    };
    setMessages((prev) => [...prev, agentMessage]);

    try {
      let fullContent = '';
      const steps = [];

      await chatAPI.sendMessageStream(userQuery, chatHistory, (chunk) => {
        if (chunk.type === 'content') {
          // Append content progressively
          fullContent += chunk.data;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === agentMessageId
                ? { ...msg, content: fullContent }
                : msg
            )
          );
        } else if (chunk.type === 'step') {
          // Add step to the steps array
          steps.push(chunk.data);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === agentMessageId
                ? { ...msg, steps: [...steps] }
                : msg
            )
          );
        } else if (chunk.type === 'metadata') {
          // Final metadata - mark as complete
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === agentMessageId
                ? { ...msg, steps: chunk.data.steps || steps, streaming: false }
                : msg
            )
          );

          // Update chat history for context
          const newHistory = [...chatHistory];
          newHistory.push({ role: 'user', content: userQuery });
          newHistory.push({ role: 'assistant', content: fullContent || '' });
          setChatHistory(newHistory);
        } else if (chunk.type === 'error') {
          // Handle error
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === agentMessageId
                ? {
                    ...msg,
                    type: 'error',
                    content: chunk.data,
                    streaming: false,
                  }
                : msg
            )
          );
        }
      });
    } catch (error) {
      console.error('Streaming error:', error);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === agentMessageId
            ? {
                ...msg,
                type: 'error',
                content: 'Failed to get response from server',
                streaming: false,
              }
            : msg
        )
      );
    }

    setLoading(false);
  };

  const renderMessage = (message, index) => {
    if (message.type === 'user') {
      return (
        <div key={index} className="message user-message">
          <div className="message-header">
            <strong>You</strong>
            <span className="timestamp">{message.timestamp}</span>
          </div>
          <div className="message-content">{message.content}</div>
        </div>
      );
    }

    if (message.type === 'agent') {
      return (
        <div key={index} className="message agent-message">
          <div className="message-header">
            <strong>Agent</strong>
            <span className="timestamp">{message.timestamp}</span>
            {message.streaming && <span className="streaming-indicator"> ●</span>}
          </div>
          <div className="message-content">
            {message.content}
            {message.streaming && <span className="cursor">|</span>}
          </div>
          {message.steps && message.steps.length > 0 && (
            <div className="reasoning-steps">
              <details>
                <summary>View reasoning steps ({message.steps.length})</summary>
                <div className="steps-content">
                  {message.steps.map((step, stepIndex) => (
                    <div key={stepIndex} className={`step step-${step.step_type}`}>
                      <strong>{step.step_type.toUpperCase()}:</strong> {step.description}
                    </div>
                  ))}
                </div>
              </details>
            </div>
          )}
        </div>
      );
    }

    if (message.type === 'error') {
      return (
        <div key={index} className="message error-message">
          <div className="message-header">
            <strong>Error</strong>
            <span className="timestamp">{message.timestamp}</span>
          </div>
          <div className="message-content">{message.content}</div>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="header-left">
          <h2>SimpleAgentApp Chat</h2>
          <span className="user-info">
            Logged in as: <strong>{user?.username}</strong> ({user?.role})
          </span>
        </div>
        <button onClick={handleLogout} className="logout-button">
          Logout
        </button>
      </div>

      <div className="chat-main">
        <div className="chat-messages">
          <div className="messages-container">
            {messages.length === 0 && (
              <div className="welcome-message">
                <h3>Welcome to SimpleAgentApp!</h3>
                <p>Ask me anything. I can help you with:</p>
                <ul>
                  <li>Weather information</li>
                  <li>Text transformations (uppercase, lowercase)</li>
                  <li>Word counting</li>
                  <li>Calculations</li>
                </ul>
              </div>
            )}
            {messages.map((message, index) => renderMessage(message, index))}
            {loading && (
              <div className="message agent-message loading">
                <div className="message-header">
                  <strong>Agent</strong>
                </div>
                <div className="message-content">
                  <span className="loading-dots">Thinking</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSubmit} className="chat-input-form">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message here..."
              disabled={loading}
              className="chat-input"
            />
            <button type="submit" disabled={loading || !input.trim()} className="send-button">
              Send
            </button>
          </form>
        </div>

        {isAdmin() && (
          <div className="sidebar-container">
            <AdminSidebar />
          </div>
        )}
      </div>
    </div>
  );
};

export default Chat;
