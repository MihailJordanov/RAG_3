# 🧠 RAG 3 — Document AI Chat Platform

RAG 3 is a **full-stack Retrieval-Augmented Generation (RAG) platform** that allows users to upload documents and interact with them through an AI-powered chat interface.

The system processes documents, builds semantic embeddings, and retrieves the most relevant information to generate accurate answers using large language models.

🔗 **Live Demo**  
https://rag-3.duckdns.org

---

# ✨ Features

- 📄 Upload and chat with your own documents
- 🔎 **Hybrid retrieval** (BM25 + vector embeddings)
- 🧠 **Multi-query retrieval** for improved search quality
- 🔀 **Reciprocal Rank Fusion (RRF)** for combining retrieval results
- 🏆 **Reranking** to select the most relevant context
- 🧩 Semantic and recursive **document chunking**
- 🖼 **Multimodal document processing** with OCR support
- ⚡ Fast API-based backend with asynchronous processing
- 👤 User authentication and guest sessions
- 🐳 Fully **Dockerized deployment**

---

# 🏗 Architecture

The system follows a classic **RAG pipeline**:

```
📄 Document Upload
      ↓
⚙️ Document Processing
      ↓
✂️ Chunking
      ↓
🧠 Embeddings Generation
      ↓
🗄 Vector Database Indexing
      ↓
🔎 Retrieval (Hybrid Search)
      ↓
🏆 Reranking
      ↓
🤖 LLM Answer Generation
```


---

# 🔎 Retrieval Techniques

To improve answer quality, the system combines several advanced retrieval techniques:

- **Vector Search** using embeddings
- **BM25 lexical search**
- **Hybrid Retrieval (BM25 + embeddings)**
- **Multi-query retrieval**
- **Reciprocal Rank Fusion (RRF)**
- **Reranking**

These techniques significantly improve context relevance and answer accuracy.

---

# 📦 Tech Stack

### Backend
- Python
- FastAPI
- LangChain

### AI / NLP
- Retrieval-Augmented Generation (RAG)
- Vector embeddings
- Hybrid search
- Reranking

### Databases
- PostgreSQL
- ChromaDB (vector database)
- Redis

### Document Processing
- Unstructured
- OCR (Tesseract / Google Vision)

### Frontend
- React
- Next.js
- TypeScript

### Infrastructure
- Docker
- Nginx
- Linux server deployment

---

# 🚀 Running the Project

### 1️⃣ Clone the repository

```bash
git clone https://github.com/MihailJordanov/RAG_3.git
cd RAG_3
```

### 2️⃣ Start with Docker

```bash
docker compose up --build
```

### 3️⃣ Open the application

```text
http://localhost
```


---

# 📷 Screenshots

Below are some screenshots of the system.

<h2 align="center">📷 Screenshots</h2>

<div align="center">
  <img src="history/images/image_09_03_26_1_new.png" width="900" alt="Screenshot 1" />
  <br><br>
  <img src="history/images/image_09_03_26_2.png" width="900" alt="Screenshot 2" />
  <br><br>
  <img src="history/images/image_09_03_26_3.png" width="900" alt="Screenshot 3" />
  <br><br>
  <img src="history/images/image_09_03_26_4.png" width="900" alt="Screenshot 4" />
  <br><br>
  <img src="history/images/image_09_03_26_5.png" width="900" alt="Screenshot 5" />
  <br><br>
  <img src="history/images/image_09_03_26_6.png" width="900" alt="Screenshot 6" />
  <br><br>
  <img src="history/images/image_09_03_26_7.png" width="900" alt="Screenshot 7" />
  <br><br>
  <img src="history/images/image_09_03_26_8.png" width="900" alt="Screenshot 8" />
  <br><br>
  <img src="history/images/image_09_03_26_9.png" width="900" alt="Screenshot 9" />
  <br><br>
  <img src="history/images/image_09_03_26_10.png" width="900" alt="Screenshot 10" />
</div>

---

# 👨‍💻 Author

**Mihail Yordanov**

GitHub  
https://github.com/MihailJordanov
