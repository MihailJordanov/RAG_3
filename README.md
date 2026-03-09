# 🧠 RAG 3 — Document AI Chat Platform

RAG 3 is a **full-stack Retrieval-Augmented Generation (RAG) platform** that allows users to upload documents and interact with them through an AI-powered chat interface.

The system processes documents, builds semantic embeddings, and retrieves the most relevant information to generate accurate answers using large language models.

🔗 **Live Demo**  
https://rag-3.duckdns.org/projects

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

![Screenshot](images/image_09_03_26_1.png)
![Screenshot](images/image_09_03_26_2.png)
![Screenshot](images/image_09_03_26_3.png)
![Screenshot](images/image_09_03_26_4.png)
![Screenshot](images/image_09_03_26_5.png)
![Screenshot](images/image_09_03_26_6.png)
![Screenshot](images/image_09_03_26_7.png)
![Screenshot](images/image_09_03_26_8.png)
![Screenshot](images/image_09_03_26_9.png)
![Screenshot](images/image_09_03_26_10.png)

---

# 📚 Future Improvements

- Advanced evaluation metrics for retrieval quality
- Streaming responses from the LLM
- Support for more document formats
- Improved UI for large projects
- User project sharing

---

# ⭐ Why this project

RAG 3 was created as an exploration of modern **AI search systems and document-based conversational interfaces**.

The project focuses on combining **LLMs with advanced retrieval techniques** to improve answer accuracy and reliability.

---

# 🤝 Contributions

Contributions, ideas, and improvements are always welcome.

If you find the project interesting, feel free to fork it or open a pull request.

---

# 👨‍💻 Author

**Mihail Yordanov**

GitHub  
https://github.com/MihailJordanov

