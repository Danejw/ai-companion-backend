# AI Companion Backend

This project powers a conversational AI companion. The backend is built with **FastAPI** and communicates with **Supabase** for data storage and retrieval.

## Purpose
The application offers a personalized chat experience. It learns from the user's messages, tracks personality traits (MBTI and OCEAN), extracts useful memories, and integrates with tools like push notifications and multistep task planning. The goal is to provide supportive, meaningful conversations that feel human.

## Repository Layout
- `app/` – Main application code
  - `main.py` sets up the FastAPI instance, CORS, and routes.
  - `routes/` contains API endpoints (MBTI, OCEAN, knowledge, notifications, etc.).
  - `websockets/` manages real‑time chat orchestration and context storage.
  - `function/` and `personal_agents/` implement features like memory extraction, notification scheduling, and specialized agent logic.
  - `psychology/` handles MBTI and OCEAN analysis as well as intent and behavior classification.
  - `supabase/` wraps database calls for storing memories, profiles, and conversation history.
  - `utils/` holds helper utilities.
- `client/` – Minimal HTML pages for development and Stripe checkout examples.
- `research/` – Markdown resources about mental health topics.
- `requirements.txt` – Python dependencies.

Start by exploring `app/main.py` and the `routes` and `websockets` directories to see how incoming requests are processed.

## Testing
To ensure code quality and functionality, the project uses pytest for unit tests and Ruff for linting. Here are the key testing commands:

### Running Tests
```bash
# Run all tests with minimal output
pytest -q

# Run tests with detailed output
pytest
```

### Code Quality Checks
```bash
# Check code style and quality without making changes
ruff check .

# Automatically fix code style issues
ruff check --fix .
```

Make sure to run these commands from the project root directory. The test suite should pass and code should be free of linting errors before submitting changes.
