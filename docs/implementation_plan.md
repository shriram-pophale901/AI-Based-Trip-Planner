# Puneri Pulse: Enterprise Upgrade Plan 🚀

This plan outlines the steps to add advanced, enterprise-grade features to your project. This will make the project significantly more complex and impressive for technical interviews and your CV.

## User Review Required

> [!IMPORTANT]
> Please review the Open Questions section and provide your preferences before we begin coding. Once you approve, we will implement these features step-by-step.

## Open Questions

> [!WARNING]  
> 1. **Routing API**: To get real-world driving distances (instead of straight lines), we can use the **OSRM Public API** (Free, but has rate limits) OR **Google Maps Distance Matrix API** (Requires a Google Cloud billing account). Which one do you prefer? (Recommendation: OSRM is great for free projects).
> 2. **Docker Environment**: Have you installed **Docker Desktop** on your Windows machine? We will need this to run Redis, RabbitMQ, and your app containers.
> 3. **RAG Chatbot**: You are currently using the Gemini API. Are we continuing with Gemini for generating Embeddings in the new RAG (LangChain) setup?

---

## Proposed Changes

We will execute this plan in 5 phases. We will tackle one phase at a time to ensure everything works perfectly.

### Phase 1: Containerization & Caching (Docker + Redis)
We will make the application "Microservice-ready" by containerizing the frontend and backend, and adding Redis to speed up route calculations.

#### [NEW] docker-compose.yml
- Create a compose file to orchestrate 4 services: `frontend`, `backend`, `redis` (for caching), and `rabbitmq` (for background tasks).

#### [NEW] backend/Dockerfile & frontend/Dockerfile
- Create Dockerfiles for both services.

#### [MODIFY] backend/main.py
- Integrate `redis` using `aioredis` or standard `redis-py`.
- Cache the `/api/plan` endpoint responses so that identical trip requests (same budget, days, group) return instantly.

---

### Phase 2: RAG-Based Travel Assistant (LangChain)
We will upgrade your current basic Gemini chatbot to a highly advanced RAG system.

#### [MODIFY] backend/main.py
- Refactor `/api/chat` to use LangChain.

#### [NEW] backend/rag_engine.py
- Load `pune_pois.csv` into a Vector Database (like FAISS or ChromaDB).
- Use `GoogleGenerativeAIEmbeddings` to embed the POI data.
- When a user asks a question, retrieve the top 3 relevant POIs from the Vector DB and send them as context to Gemini. This prevents hallucinations.

#### [MODIFY] backend/requirements.txt
- Add `langchain`, `langchain-google-genai`, `faiss-cpu`, `sentence-transformers`.

---

### Phase 3: Real-Time Dynamic Routing (OSRM)
We will replace the basic `haversine` math with actual road distances, showing you know Operations Research concepts (Vehicle Routing Problem).

#### [MODIFY] backend/recommender.py
- Create a new function `get_osrm_distance_matrix(coords)` that calls the OSRM API.
- Update the `ga_tsp_tw` (Genetic Algorithm) and `proximity_cluster` to use real driving times instead of assuming a constant 30km/h speed.

---

### Phase 4: Hybrid Recommendation Retraining Pipeline
You have SVD weights, but we need an automated way to retrain them as new feedback comes in.

#### [NEW] backend/retrain_model.py
- Create a script that reads `user_ratings.csv` and `feedback.csv`.
- Uses the `Surprise` library (or pure numpy) to perform SVD Matrix Factorization.
- Automatically saves new `svd_weights.pkl` when triggered.

#### [MODIFY] backend/main.py
- Add a new endpoint `/api/retrain` to trigger this pipeline (simulating a real MLOps pipeline).

---

### Phase 5: Asynchronous Background Tasks (Celery)
We will add Celery to handle heavy tasks in the background, a key skill for senior backend roles.

#### [NEW] backend/celery_worker.py
- Set up Celery connected to RabbitMQ (Broker) and Redis (Backend).
- Create a task `generate_itinerary_pdf(itinerary_data)` that builds a PDF report.

#### [MODIFY] backend/main.py
- Add an endpoint `/api/export_pdf`. Instead of blocking the UI, this endpoint will dispatch the Celery task and immediately return a `task_id` for the frontend to poll.

---

## Verification Plan

### Automated Tests
- Run API endpoints locally to ensure Redis caches responses.
- Test the LangChain RAG by asking a highly specific question about a POI in the CSV (e.g., "What are the timings of Shaniwar Wada?") to verify it pulls from the DB, not generic internet knowledge.

### Manual Verification
- Run `docker-compose up` to ensure all 4 containers start cleanly.
- Monitor Celery logs to ensure PDF generation runs completely in the background.
