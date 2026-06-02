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

## Documentation
Refer the below listed document for in-depth understanding of the project working and the plan to accomplish this project:
- VideoRAG_Project_Documentation.pdf

## Backend Architecture
The backend is built with FastAPI:
- main.py -> Entrypoint for the API, handles server lifespan events, CORS configurations, and routers.
- config.py -> Manages app configuration and environment variables.
- models.py -> Defines Pydantic data schemas for ingestion requests/responses, chat prompts, and video metadata.
- state.py -> Manages state storage and pub/sub events using Redis.
- routes -> Directory for API route groups (e.g., status, chat, ingest).

## Backend Setup
To run the backend server locally:
1. Navigate to the backend directory:
   cd backend
2. Create and activate virtual environment
   python -m venv .venv
   .venv\Scripts\activate
3. Install dependencies
   pip install -r requirements.txt
4. Configure environment variables:
   Copy .env.example to .env
   Fill in your API keys (YOUTUBE_API_KEY, OPENAI_API_KEY, GROQ_API_KEY)
5. Run the server:
   uvicorn main:app --reload

Interactive API documentation will be available at http://localhost:8000/docs.