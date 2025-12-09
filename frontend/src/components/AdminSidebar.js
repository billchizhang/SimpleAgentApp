import React, { useState } from 'react';
import { authAPI } from '../services/api';
import '../styles/AdminSidebar.css';

const AdminSidebar = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('user');
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState(''); // 'success' or 'error'
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setLoading(true);

    try {
      const response = await authAPI.createUser(username, password, email, role);

      if (response.success) {
        setMessage(`User "${username}" created successfully!`);
        setMessageType('success');
        // Clear form
        setUsername('');
        setEmail('');
        setPassword('');
        setRole('user');
      } else {
        setMessage(response.error || 'Failed to create user');
        setMessageType('error');
      }
    } catch (error) {
      console.error('Create user error:', error);
      let errorMessage = 'Failed to create user';

      // Handle FastAPI validation errors (422)
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;

        // If detail is an array of validation errors, extract messages
        if (Array.isArray(detail)) {
          errorMessage = detail.map(err => err.msg || err.message).join(', ');
        } else if (typeof detail === 'string') {
          errorMessage = detail;
        } else {
          errorMessage = 'Validation error occurred';
        }
      }

      setMessage(errorMessage);
      setMessageType('error');
    }

    setLoading(false);

    // Clear message after 5 seconds
    setTimeout(() => {
      setMessage('');
      setMessageType('');
    }, 5000);
  };

  return (
    <div className="admin-sidebar">
      <h3>Add User</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="new-username">Username</label>
          <input
            type="text"
            id="new-username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            disabled={loading}
            minLength={3}
            maxLength={50}
            placeholder="Enter username"
          />
        </div>

        <div className="form-group">
          <label htmlFor="new-email">Email</label>
          <input
            type="email"
            id="new-email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={loading}
            placeholder="user@example.com"
          />
        </div>

        <div className="form-group">
          <label htmlFor="new-password">Password</label>
          <input
            type="password"
            id="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={loading}
            minLength={8}
            maxLength={12}
            placeholder="8-12 characters"
          />
        </div>

        <div className="form-group">
          <label htmlFor="new-role">Role</label>
          <select
            id="new-role"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            disabled={loading}
          >
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>
        </div>

        {message && (
          <div className={`message ${messageType}`}>
            {message}
          </div>
        )}

        <button type="submit" disabled={loading} className="create-button">
          {loading ? 'Creating...' : 'Create User'}
        </button>
      </form>
    </div>
  );
};

export default AdminSidebar;
