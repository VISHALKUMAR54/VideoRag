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