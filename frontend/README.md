# SimpleAgentApp Frontend

React-based web frontend for SimpleAgentApp with user authentication and chat interface.

## Features

- **User Authentication**: Login with username/password
- **Interactive Chat**: Chat with the AI agent powered by the backend
- **Admin Panel**: Admin-only sidebar for creating new users
- **ReAct Visualization**: View agent reasoning steps for transparency
- **Responsive Design**: Works on desktop and mobile devices

## Default Accounts

The backend automatically creates these accounts on first startup:

- **Admin Account**
  - Username: `admin`
  - Password: `AdminPass123!`
  - Access: Full access including user management

- **Demo User Account**
  - Username: `demo_user`
  - Password: `UserPass123!`
  - Access: Chat interface only

## Local Development

### Prerequisites

- Node.js 16+ and npm
- Backend services running on ports 8000 and 8001

### Setup

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm start
   ```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

The development server will proxy API requests to `http://localhost:8001` (configured in package.json).

### Environment Variables

Create a `.env.local` file in the frontend directory if you need to override the API URL:

```bash
REACT_APP_API_URL=http://custom-backend-url:8001
```

## Production Build

Build the optimized production bundle:

```bash
npm run build
```

The build output will be in the `build/` directory, which can be served with any static file server.

## Project Structure

```
frontend/
├── public/
│   └── index.html          # HTML entry point
├── src/
│   ├── components/
│   │   └── AdminSidebar.js # Admin user management component
│   ├── contexts/
│   │   └── AuthContext.js  # Authentication state management
│   ├── pages/
│   │   ├── Login.js        # Login page
│   │   └── Chat.js         # Main chat interface
│   ├── services/
│   │   └── api.js          # Backend API service layer
│   ├── styles/
│   │   ├── index.css       # Global styles
│   │   ├── Login.css       # Login page styles
│   │   ├── Chat.css        # Chat interface styles
│   │   └── AdminSidebar.css # Admin sidebar styles
│   ├── App.js              # Main app component with routing
│   └── index.js            # React entry point
├── package.json
└── README.md
```

## Backend API Integration

The frontend integrates with these backend endpoints:

### Authentication API (`/auth/*`)
- `POST /auth/login` - User login
- `POST /auth/create_user` - Create new user (admin only in UI)

### Chat API
- `POST /query` - Send message to agent
- `GET /tools` - List available tools

## Features by User Role

### All Users
- Login/logout
- Send messages to AI agent
- View agent responses with reasoning steps
- Interactive chat history

### Admin Users Only
- All user features plus:
- Create new user accounts
- Assign user roles (User/Admin)
- Manage user credentials

## Technologies Used

- **React 18** - UI framework
- **React Router 6** - Client-side routing
- **Axios** - HTTP client for API requests
- **Context API** - Global state management for authentication
- **CSS3** - Modern styling with animations

## Development Commands

```bash
# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

## Troubleshooting

### Port 3000 already in use
Kill the process using port 3000 or set a different port:
```bash
PORT=3001 npm start
```

### API connection errors
Ensure the backend services are running:
- Tool API on port 8000
- Agent API on port 8001

Check the proxy configuration in `package.json` or set `REACT_APP_API_URL` environment variable.

### Login fails
Verify the backend authentication database is initialized with default users. Check backend logs for errors.
