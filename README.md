# AI Blog Generator

A production-ready AI Blog Generator application using FastAPI, Google Gemini, and Next.js.

## Features

- **AI-Powered Content**: Generates blog titles, outlines, content, and SEO metadata using Google Gemini.
- **Customizable**: Users can specify topic, tone, keywords, length, and target audience.
- **Modern Stack**: Built with FastAPI (Python) and Next.js 14 (TypeScript).
- **Production Ready**: Includes Docker support, environment configuration, and structured code.

## Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local frontend dev)
- Python 3.11+ (for local backend dev)
- Google Gemini API Key

## Setup & Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd ai_blogging
```

### 2. Environment Configuration

Copy the example environment file and add your Gemini API key:

```bash
cp .env.example .env
# Edit .env and set GEMINI_API_KEY
```

### 3. Run with Docker (Recommended)

Start the backend service:

```bash
docker-compose up --build
```

The backend API will be available at `http://localhost:8000`.

### 4. Run Frontend Locally

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`.

## Project Structure

```
.
├── backend/                # FastAPI Backend
│   ├── app/
│   │   ├── api/            # API Routes
│   │   ├── core/           # Config & Settings
│   │   ├── schemas/        # Pydantic Models
│   │   ├── services/       # Business Logic (Gemini Integration)
│   │   └── main.py         # App Entry Point
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # Next.js Frontend
│   ├── src/
│   │   ├── app/            # Pages
│   │   ├── components/     # React Components
│   │   └── services/       # API Client
│   └── package.json
├── docker-compose.yml
└── .env.example
```

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for the interactive Swagger UI.

## Scaling Strategies (Bonus)

1.  **Caching**: Implement Redis caching for frequent topics to reduce API costs and latency.
2.  **Queueing**: Use Celery or RabbitMQ for background task processing if generation times increase.
3.  **Database**: Migrate from in-memory/SQLite to PostgreSQL for persistent storage of user history and generated blogs.
4.  **Rate Limiting**: Implement rate limiting middleware in FastAPI to prevent abuse.
5.  **CDN**: Serve frontend assets via a CDN (e.g., Vercel, Cloudflare) for global low latency.