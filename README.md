# VideoRag - Video/reel Retrieval-Augmented Generation

## Project Overview:
This is an assignment project given by Techsolv IT Service titled VideoRag which is a full-stack RAG application which uses YouTube's video and Instagram's reel URL to retrieve transcript and metadata (views, likes, comments, creator, follower count, hashtags, upload date, duration) from the uploaded URL, once the transcript and metadata is retrieved then comes the main steps for RAG and those are 'Chunking and Embedding' of the data and storing it into QDrant vectorDB.

Once the embeddigs stage is done then user is allowed to ask questions related to each video one by one or user can ask questions related to both videos at once. Once the prompt is provided, the LLM will try to generate a response based on the question and the retrieved context from the vectorDB and strems the response back to the UI where user can see and read the response given by the LLM.

## Goal Of The Project:
To deliver a full stack rag application which has lower latency, cost effective and with no lag.

## Tech Stack:
- FastAPI (backend)
- Next.js (frontend)
- Qdrant (vector store)
- Redis (caching and history)
- LangGraph (agent orchestration)
- BGE-small (embeddings)
- Groq (LLM)

## Documentation:
Refer the below listed document for in-depth understanding of the project working and the plan to accomplish this project:
- VideoRAG_Project_Documentation.pdf

## Backend Architecture:
The backend is built with FastAPI:
- main.py -> Entrypoint for the API, handles server lifespan events, CORS configurations, and routers.
- config.py -> Manages app configuration and environment variables.
- models.py -> Defines Pydantic data schemas for ingestion requests/responses, chat prompts, and video metadata.
- state.py -> Manages state storage and pub/sub events using Redis.
- routes -> Directory for API route groups (e.g., status, chat, ingest).

## Core RAG Pipeline & Services:
The backend implements the following processing services:
- Ingestion Service (`services/ingestion.py`): Fetches transcripts and metadata (engagement metrics, duration, follows) for YouTube videos (using YouTube Data API v3/transcripts API) and Instagram Reels (using scrape options).
- Chunker Service (`services/chunker.py`): Chunks text transcripts into overlapping blocks of specified size for fine-grained context retrieval.
- Embedder Service (`services/embedder.py`): Generates vector embeddings for transcript chunks using the `BAAI/bge-small-en-v1.5` model.
- Vector Store Service (`services/vector_store.py`): Sets up and manages collections in Qdrant Vector DB, indexing chunk vectors.
- LLM Service (`services/llm.py`): Orchestrates conversational RAG workflows using LangGraph and Groq's `llama-3.3-70b-versatile` model.

## Backend Setup:
To run the backend server locally:
1. Navigate to the backend directory:
```bash
   cd backend
```
2. Create and activate virtual environment
```bash
   python -m venv .venv
   .venv\Scripts\activate
```
3. Install dependencies
```bash
   pip install -r requirements.txt
```
4. Configure environment variables:
```bash
   Copy .env.example to .env
```
   Fill in your API keys (YOUTUBE_API_KEY, OPENAI_API_KEY, GROQ_API_KEY)

5. Run the server:
```bash
   uvicorn main:app --reload
```
Interactive API documentation will be available at http://localhost:8000/docs.

## Testing:
The project includes test scripts to validate ingestion, chunking, and RAG pipelines:
- `tests/test_chunks.py` - Verifies text chunking and overlap parameters.
- `tests/test_youtube.py` - Unit tests for YouTube's transcript and metadata retrieval.
- `tests/test_instagram.py` - Unit tests for Instagram's transcript and metadata retrieval.
- `tests/test_pipeline.py` - Validates the full ingestion pipeline.
- `tests/test_rag.py` - Validates context retrieval and LLM prompt and response.
- `tests/test_e2e.py` - Performs an end-to-end system test.

### Running Tests:
To run the validation test scripts:
1. Ensure your virtual environment is active:
```bash
   cd backend
   .venv\Scripts\activate
   python tests/file_name.py
```
## Frontend Architecture:
The frontend is built with Next.js 16 using Tailwind CSS 4:
- `app/` - Handles the application layouts and main page view.
- `components/` - Reusable UI widgets (e.g., chat components, metadata comparisons, input fields).
- `hooks/` - Custom React hooks for API interaction, managing chat sessions, and WebSocket event handling.
- `lib/` - Client-side network service configurations and helper functions.


## Frontend Setup:
To run the frontend application locally:
1. Navigate to the frontend directory:
```bash
   cd frontend
```
2. Install dependencies:
```bash
   npm install
```
3. Configure environment variables:
Create a file named .env.local in the frontend folder.
Add the backend service endpoints:
```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_WS_URL=ws://localhost:8000
```
   Update NEXT_PUBLIC_API_URL to match your backend URL (default: http://localhost:8000/api).

4. Run the development server:
```bash
   npm run dev
```
The application will be accessible at http://localhost:3000.

## Running with Docker:
The project supports containerization using Docker Compose, running four primary services:
- qdrant (port 6333): Vector database for transcript searches.
- redis (port 6379): Cache and event hub (pub/sub).
- backend (port 8000): FastAPI application service.
- frontend (port 3000): Next.js web interface client.

### Getting Started with Docker:
1. Configure credentials:
   - Ensure `backend/.env` is set up with valid API keys (it is loaded by the backend container).
2. Run Docker Compose command to build and launch all services in the background:
   ```bash
   docker compose up -d --build
   ```

## Access the services:
- Frontend web application: http://localhost:3000
- Backend API documentation: http://localhost:8000/docs
- Qdrant UI dashboard: http://localhost:6333/dashboard