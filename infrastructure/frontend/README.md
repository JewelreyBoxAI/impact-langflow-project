# Impact LangFlow Frontend

A production-ready Next.js React frontend for the Impact LangFlow AI Platform, featuring the Recruiting Agent with advanced chat capabilities, SMS/voice integration, and mobile-first responsive design.

## Features

- **🤖 AI Recruiting Agent**: Full-featured chat interface with Katelyn, your AI recruiting assistant
- **📱 Mobile-First Design**: Responsive layout with mobile drawer navigation
- **🌙 Dark/Light Mode**: System-aware theme toggle with persistent preferences
- **💬 Advanced Chat**: Real-time messaging with SMS status indicators and voice toggles
- **📋 Session Management**: Persistent conversation history with local storage
- **🎨 Modern UI**: ShadCN components with Tailwind CSS and Impact Blue theming
- **⚡ Performance**: Optimized with Next.js 14+ App Router and TypeScript

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

## Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── agents/
│   │   ├── recruiting/     # Main recruiting agent page
│   │   ├── supervisor/     # Placeholder supervisor page
│   │   ├── admin/          # Placeholder admin page
│   │   └── operations/     # Placeholder operations page
│   ├── layout.tsx          # Root layout with providers
│   └── page.tsx           # Home page (redirects to recruiting)
├── components/
│   ├── chat/              # Chat interface components
│   ├── sidebar/           # Navigation and conversation sidebar
│   └── shared/            # Reusable UI components
├── context/               # React context providers
├── hooks/                 # Custom React hooks
├── icons/                 # Custom icon components
├── lib/                   # Utilities and API client
├── styles/               # Global styles and theme
└── public/               # Static assets
```

## Environment Configuration

Copy `.env.example` to `.env.local` and configure:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENV=development
NEXT_PUBLIC_SUPPORT_PHONE=+1-555-0123
NEXT_PUBLIC_USE_WEBSOCKETS=false
```

## Agent Features

### Recruiting Agent (Katelyn) ✅
- Full chat interface with real-time messaging
- SMS status indicators (delivered, failed, queued)
- Voice toggle (ready for integration)
- Session persistence and conversation history
- Mobile-responsive design with sidebar navigation

### Coming Soon Agents 🚧
- **Supervisor Agent**: Performance analytics and oversight
- **Admin Agent**: System administration and user management
- **Operations Agent**: Workflow automation and analytics

## API Integration

The frontend is designed to integrate with FastAPI endpoints:

- `POST /api/v1/agents/recruiting/invoke` - Send messages
- `GET /api/v1/agents/recruiting/conversations` - Get conversation history
- `POST /api/v1/agents/recruiting/conversations/:id/message` - Send to specific conversation

## Technology Stack

- **Framework**: Next.js 14+ with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS with custom theme tokens
- **Components**: Radix UI primitives with ShadCN
- **Icons**: Lucide React
- **Animations**: Framer Motion
- **State Management**: React Context + Zustand
- **Storage**: localStorage for session persistence

## Development

```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Development with hot reload
npm run dev
```

## Deployment

This is a standard Next.js application that can be deployed to:

- **Vercel** (recommended): Push to GitHub and connect
- **Netlify**: Build command `npm run build`, publish directory `out`
- **Docker**: Standard Next.js container setup
- **Self-hosted**: `npm run build && npm start`

## Contributing

1. Follow the established component architecture (Atomic Design)
2. Use TypeScript for all new code
3. Maintain mobile-first responsive design
4. Test thoroughly across devices and themes
5. Follow the established naming conventions and file structure

## Support

For technical support or questions about the Impact LangFlow platform, contact the development team.