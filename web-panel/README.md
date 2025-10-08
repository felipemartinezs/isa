# Inventory Scanner Pro - Web Panel

Next.js 14 web panel with real-time SSE updates, modern UI, and comprehensive BOM management.

## Features

- **Real-time Feed**: Live scanning updates via SSE
- **Article Management**: Upload and manage article database
- **BOM Management**: Upload and manage BOMs by category
- **Session Analysis**: View and analyze scan sessions with comparison
- **Modern UI**: Built with TailwindCSS and shadcn/ui components
- **Authentication**: Secure JWT-based login

## Setup

1. **Install dependencies**:
```bash
npm install
```

2. **Configure environment**:
```bash
cp .env.example .env.local
# Edit .env.local and set NEXT_PUBLIC_API_URL
```

3. **Run development server**:
```bash
npm run dev
```

4. **Build for production**:
```bash
npm run build
npm start
```

## Environment Variables

- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)

## Pages

- `/login`: Authentication page
- `/dashboard`: Main dashboard with tabs for:
  - Real-time Feed
  - Sessions
  - Article Database
  - BOM Management

## Components

- `ArticleUpload`: Excel upload for article database
- `BOMUpload`: Excel upload for BOMs
- `RealtimeFeed`: Live scanning feed with SSE
- `SessionsView`: Session analysis with BOM comparison

## Technology Stack

- **Framework**: Next.js 14 (App Router)
- **Styling**: TailwindCSS
- **Components**: shadcn/ui (Radix UI)
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **Real-time**: Server-Sent Events (SSE)

## Deployment to Google App Engine

1. Create `app.yaml`:
```yaml
runtime: nodejs20
env: standard
handlers:
  - url: /.*
    script: auto
    secure: always

env_variables:
  NEXT_PUBLIC_API_URL: "https://your-api-url.com"
```

2. Deploy:
```bash
gcloud app deploy
```
