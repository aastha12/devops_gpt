# 🛠️ Project Plan: DevOps GPT (AI Incident Commander)

## 🔹 Goal:

An AI assistant that:

- Analyzes new incident descriptions
- Finds similar past incidents using MongoDB Vector Search
- Suggests likely causes and possible mitigation steps

## 📦 Step-by-Step Project Plan

### 1. Data Collection ✅ 

- Scrape incidents from Gitlab api 
- Save results locally to avoid rerunning heavy queries
- Store raw incident data in Atlast

### 2. Vector Embedding + MongoDB Atlas ✅ 

- Generate embeddings  
- Store embeddings in MongoDB Atlas Vector Store 
- Use MongoDB’s Vector Search to retrieve semantically similar past incidents

### 3. Build AI Incident Assistant

- User pastes a new incident log into the UI
- App does:
    - Embed the input
    - Query MongoDB to find 3 most similar incidents
    - Use LLM (OpenAI, Claude, or Gemini) to:
        - Summarize common root causes
        - Recommend first troubleshooting steps
    - Use LLM-as-Judge to evaluate responses
