# Learn Loop

An age-adaptive AI learning assistant designed to help children understand academic concepts through cognitively appropriate explanations. The system focuses on one concept at a time, dynamically adjusting explanation depth and language complexity based on the learner's selected age level.

## 🎯 Project Overview

Learn Loop is a parent-led, cognitively aware AI learning companion. Designed for homeschoolers and active parents, it allows adults to curate their child's educational journey by pinning target topics and uploading specific curriculum documents that ground the AI's explanations.

### Key Features

- **Age-Adaptive Explanations**: Dynamically adjusts explanations for ages 6, 8, and 10
- **Parent-Managed Learning Paths**: Parents pin target topics and upload curriculum documents
- **Student Code System**: Children access their learning sessions via unique codes (e.g., `LEO-123`)
- **Hybrid Grounding (RAG)**: Uses uploaded curriculum documents with fallback to LLM knowledge
- **Dual-Mode Interaction**: Supports both text and voice input for children
- **Understanding Assessment**: Non-exam based classification (understood, partial, confused)
- **Parent Insights Dashboard**: Real-time progress tracking and AI-generated insights
- **Concept-Based Micro-Learning**: Focuses on one concept per session

## 🏗️ Architecture

### Tech Stack

**Backend:**
- **FastAPI** - Python web framework
- **OpenAI GPT-4o** - LLM for explanations and evaluations
- **Weaviate** - Vector database for RAG (curriculum documents)
- **Supabase** - PostgreSQL database and authentication
- **OpenAI Whisper** - Speech-to-text for voice input

**Frontend:**
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Redux Toolkit** - State management
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations
- **Lucide React** - Icons

### Project Structure

```
learn_loop/
├── api/                    # Backend FastAPI application
│   ├── agents/            # AI agents (Explainer, Evaluator, Insight)
│   ├── core/              # Configuration and settings
│   ├── database/          # Database migrations and seeds
│   ├── models/            # Pydantic schemas
│   ├── routes/            # API endpoints
│   ├── services/          # External service integrations
│   ├── tests/             # Unit and integration tests
│   ├── main.py            # FastAPI application entry point
│   └── requirements.txt   # Python dependencies
│
├── client/                # Frontend React application
│   ├── src/
│   │   ├── features/      # Redux slices and feature components
│   │   ├── components/    # Reusable UI components
│   │   ├── services/      # API client
│   │   └── store/         # Redux store configuration
│   └── package.json      # Node.js dependencies
│
└── specs/                 # Project specifications
    ├── SPEC.md            # Main system specification
    ├── API_CONTRACTS.md   # API endpoint documentation
    ├── AGENT_SPECIFICATIONS.md  # AI agent details
    └── IMPLEMENTATION_PLAN.md    # Development roadmap
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.13+** (or 3.11+)
- **Node.js 20.19+** (or 22.12+)
- **PostgreSQL** (via Supabase)
- **Weaviate Cloud** account (or self-hosted)
- **OpenAI API** key

### Backend Setup

1. **Navigate to the API directory:**
   ```bash
   cd learn_loop/api
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the `api/` directory:
   ```env
   # OpenAI
   OPENAI_API_KEY=your_openai_api_key_here

   # Weaviate
   WEAVIATE_CLUSTER_URL=your_weaviate_cluster_url
   WEAVIATE_API_KEY=your_weaviate_api_key

   # Supabase
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your_supabase_anon_key
   SUPABASE_DB_URL=postgresql://user:password@host:port/dbname

   # Application
   PROJECT_NAME=Learn Loop API
   DEBUG=True
   ```

5. **Initialize Weaviate schema:**
   ```bash
   python scripts/init_weaviate.py
   ```

6. **Run database migrations:**
   ```bash
   python database/migrate.py
   ```

7. **Seed test data (optional):**
   ```bash
   python database/seed_test_child.py
   ```

8. **Run the development server:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   The API will be available at `http://localhost:8000`
   - API docs: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/health`

### Frontend Setup

1. **Navigate to the client directory:**
   ```bash
   cd learn_loop/client
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run the development server:**
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:5173`

4. **Build for production:**
   ```bash
   npm run build
   ```

## 🧪 Testing

### Backend Tests

Run all tests:
```bash
cd learn_loop/api
pytest
```

Run with coverage:
```bash
pytest --cov=. --cov-report=html
```

Run specific test file:
```bash
pytest tests/unit/test_explainer_agent.py
```

### Frontend Tests

(Add when test setup is configured)

## 📊 Database Schema

### Key Tables

- **`children`**: Child profiles with learning codes and target topics
- **`sessions`**: Learning sessions linked to children
- **`interactions`**: Chat messages with understanding states
- **`curriculum_documents`**: Uploaded curriculum files
- **`child_curriculum`**: Many-to-many relationship between children and documents

See `api/database/schema.sql` for the complete schema.

## 🔌 API Endpoints

### Session Management

- `POST /api/v1/sessions/start` - Start a new learning session
- `POST /api/v1/sessions/{session_id}/interact` - Send message or audio

### Parent Management

- `GET /api/v1/parent/children` - Get all children
- `POST /api/v1/parent/children` - Create a child profile
- `PATCH /api/v1/parent/children/{child_id}` - Update child profile
- `GET /api/v1/parent/curriculum` - Get curriculum documents
- `POST /api/v1/parent/curriculum/upload` - Upload curriculum document
- `GET /api/v1/parent/insights` - Get learning insights and stats

See `specs/API_CONTRACTS.md` for detailed API documentation.

## 🤖 AI Agents

### Explainer Agent
Generates age-adaptive explanations based on the child's age level and uses RAG to ground responses in uploaded curriculum.

### Evaluator Agent
Assesses child understanding from their responses, classifying as: `understood`, `partial`, or `confused`.

### Insight Agent
Generates parent-facing summaries with achievements, challenges, and recommended next steps.

See `specs/AGENT_SPECIFICATIONS.md` for detailed agent specifications.

## 🎨 UI/UX

The frontend features a professional "Emerald & White" theme with:
- Clean, modern design
- Progress visualization (Progress Gauge)
- Parent dashboard with child management
- Real-time chat interface
- Voice input support

## 🔐 Environment Variables

### Required

- `OPENAI_API_KEY` - OpenAI API key for LLM and Whisper
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase anon/public key
- `SUPABASE_DB_URL` - Direct PostgreSQL connection string
- `WEAVIATE_CLUSTER_URL` - Weaviate cluster endpoint
- `WEAVIATE_API_KEY` - Weaviate API key

### Optional

- `PROJECT_NAME` - Application name (default: "Learn Loop API")
- `DEBUG` - Enable debug mode (default: False)

## 📝 Development Workflow

1. **Backend changes**: The server auto-reloads on file changes (via `--reload`)
2. **Frontend changes**: Vite HMR (Hot Module Replacement) updates the UI automatically
3. **Database changes**: Update `schema.sql` and run `python database/migrate.py`
4. **Weaviate changes**: Update `scripts/init_weaviate.py` and re-run

## 🐛 Troubleshooting

### Backend Issues

**Port already in use:**
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9
```

**Database connection errors:**
- Verify `SUPABASE_DB_URL` is correct
- Use the connection pooler URL if direct connection fails
- Ensure password is URL-encoded if it contains special characters

**Weaviate connection errors:**
- Verify cluster URL and API key
- Check that the collection is initialized: `python scripts/init_weaviate.py`

### Frontend Issues

**Node version incompatible:**
```bash
# Use nvm to switch versions
nvm install 20
nvm use 20
```

**Module not found errors:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

## 📚 Additional Documentation

- **Main Specification**: `specs/SPEC.md`
- **API Contracts**: `specs/API_CONTRACTS.md`
- **Agent Specifications**: `specs/AGENT_SPECIFICATIONS.md`
- **Implementation Plan**: `specs/IMPLEMENTATION_PLAN.md`

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Add tests if applicable
4. Submit a pull request

## 📄 License

[Add your license here]

## 👥 Authors

[Add author information here]

## 🙏 Acknowledgments

- OpenAI for GPT-4o and Whisper
- Weaviate for vector database
- Supabase for backend infrastructure
- FastAPI and React communities

---

**Note**: This is an educational project. Ensure you have proper API keys and database access before running in production.

## 🌍 Deploy (free/cheap)

Best practice: **Frontend on a static host** + **Backend as an API service**, using your existing Supabase + Weaviate + OpenAI keys.

### Frontend (Vercel / Netlify)

- **Build**: `npm run build`
- **Output**: `client/dist`
- **Env var (required)**:
  - `VITE_API_BASE_URL` = `https://YOUR_BACKEND_DOMAIN/api/v1`

### Backend (Railway / Render / Fly.io)

Recommended start command:

- `uvicorn main:app --host 0.0.0.0 --port $PORT`

Or use the provided Dockerfile:

- `api/Dockerfile`

Backend env vars (minimum):
- `OPENAI_API_KEY`
- `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_DB_URL`
- `WEAVIATE_URL`, `WEAVIATE_API_KEY`
- `JWT_SECRET` (change for production)
- `OPIK_API_KEY` (optional), `OPIK_PROJECT` (optional), `OPIK_URL` (optional)

### Important: curriculum file storage

Curriculum uploads are currently stored on the backend filesystem. On many free hosts the filesystem is **ephemeral**, so uploads may disappear on redeploy/restart. For production you’ll want persistent disk or an object store (S3/Supabase Storage).

### Railway note (monorepo)

You have **two options**:

1) **Recommended (2 services)** in one Railway project:
- **Backend service**: set root directory to `api/` (or deploy using `api/Dockerfile`)
- **Frontend service**: set root directory to `client/` (or deploy frontend to Vercel instead)

2) **Single Railway service (one deploy)**:
- Use the repo-root `Dockerfile` (builds `client` and runs `api`)
- Set `SERVE_CLIENT=true` in backend env vars (so FastAPI serves the built frontend)

