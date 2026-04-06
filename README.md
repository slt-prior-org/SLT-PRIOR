
# HeartWise 2.0 (SLT-PRIOR)

<img width="1536" height="1024" alt="heartwise2_logo" src="https://github.com/user-attachments/assets/9e2f50ba-e958-468f-acc6-fef5baab3852" />


## 📚 About

HeartWise 2.0 is a web application that provides evidence-based information and treatment guidance for patients with coronary artery disease. The application combines a chatbot interface, a retrieval-augmented generation (RAG) pipeline, and professional review workflows to support safe and context-aware health communication.

The chatbot answers general questions based on official clinical care guidelines and patient education materials (n=106). If a message requires personal medical assessment, the conversation can be escalated to a healthcare professional. The system also includes emergency detection, guideline excerpt retrieval, and AI-generated summaries to support professional review.

## ✨ Main Features

- Patient chatbot for coronary artery disease related questions
- Retrieval-augmented generation (RAG) based on official guideline material
- Emergency message detection for urgent situations
- Safety classification for deciding whether AI can answer directly
- Escalation flow from chatbot to healthcare professional
- Professional dashboard for reviewing and handling flagged chats
- AI-generated chat summaries and draft responses for professionals
- Real-time chat updates via WebSocket
- Finnish and English language support

## Architecture Overview

The project is divided into two main parts:

### Frontend
- Vue 3
- Pinia
- Vue Router
- Vue I18n
- Axios
- WebSocket client
- Vitest

### Backend
- FastAPI
- Python
- MongoDB
- Pydantic
- JWT authentication
- WebSocket endpoints

### AI and Data Layer
- Google Gemini
- LangChain
- Chroma vector store
- Google Cloud Storage
- PyPDF2
- Langdetect

## How It Works

1. A patient logs in and starts a chat.
2. The frontend sends messages to the FastAPI backend.
3. The backend first checks for emergency-related content.
4. If the message is non-emergency, it is classified as either:
   - `SAFE`: the chatbot can answer using RAG
   - `NEEDS_REVIEW`: the message may require professional review
5. For safe questions, the RAG pipeline retrieves relevant guideline content and generates a response.
6. For review-needed questions, the system either:
   - shows a relevant guideline excerpt, or
   - forwards the conversation to a professional workflow
7. Professionals can claim chats, read AI-generated summaries, review patient context, and respond in real time.

## 📁 Project Structure

```text
.
├── frontend/        # Vue application
├── backend/         # FastAPI application
├── docker-compose.yaml
├── README.md
└── .github/         # CI pipeline
```

## Requirements

- Python 3.10+ recommended
- Node.js LTS
- MongoDB connection
- Google API key for Gemini
- Google Cloud credentials for guideline document access

## 🔐 Environment Configuration

The backend requires environment variables such as:

```env
GEMINI_API=your_api_key
MONGO_URI=your_mongodb_uri
JWT_SECRET=your_jwt_secret
JWT_ALG=HS256
JWT_EXPIRES_MIN=60
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

## Running the Application

### 🐳 With Docker Compose

```bash
docker compose up --build
```

Services:
- Frontend: `http://localhost:8080`
- Backend: `http://localhost:8000`
- Chroma: internal vector database service

### 🛠️ Manual Development Setup

#### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend
npm install
npm run serve
```

## Testing

### Backend

```bash
cd backend
pytest -v -m "not integration" tests/
```

### Frontend

```bash
cd frontend
npm test
```

## CI

The repository includes a GitHub Actions CI pipeline that:
- runs backend tests
- runs frontend tests
- performs a Docker-based smoke test

## Tech Stack

### 🎨 Frontend
- Vue 3
- Pinia
- Vue Router
- Vue I18n
- Axios
- Vitest

### ⚙️ Backend
- FastAPI
- MongoDB
- Pydantic
- JWT
- WebSocket

### 🧠 AI
- Google Gemini 2.5 Flash Lite
- LangChain
- Chroma DB
- Google Cloud Storage

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 👥 Authors

- [riinaeer](https://github.com/riinaeer)
- [aleksiIso-seppala](https://github.com/aleksiIso-seppala)
- [KN5T](https://github.com/orgs/slt-prior-org/people/KN5T)
- [timikalervo](https://github.com/orgs/slt-prior-org/people/timikalervo)
- [jantsu99](https://github.com/orgs/slt-prior-org/people/jantsu99)
- [JaaniKi](https://github.com/orgs/slt-prior-org/people/JaaniKi)
- [matildavilhelmiina](https://github.com/orgs/slt-prior-org/people/matildavilhelmiina)

## 🚫 Contribution

Please do not contribute to this project.

This repository is a school project created for educational purposes. It is published for demonstration and portfolio use, but pull requests and external contributions are not being accepted.
