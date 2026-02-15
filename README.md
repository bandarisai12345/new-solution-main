

## Project Structure

```
backend/          # Python backend application
  agents/         # AI agents (intent, semantic, SQL, response)
  utilities/      # Database connections, validators, config
  prompts/        # Prompt templates
  main.py         # Entry point

frontend/         # React frontend application
  src/
    components/   # React components 
    App.js        # Main app component

# Database files
  cleaned_cosmetics.csv       # Product data
  product_embeddings.npy      # Vector embeddings
  product_texts.txt           # Text data
```

## Getting Started

### Prerequisites

- Python 3.11.5
- Node.js 14+
- npm
- Model - phi3 (ollama) {Install Ollama locally}
- Vector DB - Pinecone
- DB - sqlite3

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Configure environment settings in `utilities/config.py`

4. Run the backend server:
   ```bash
   python main.py
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

The application will open at `http://localhost:3000`


## Key Components

- **Intent Agent**: Determines user intent from queries
- **Semantic Agent**: Performs semantic search on product data
- **SQL Agent**: Generates and executes SQL queries
- **Response Generator**: Creates human-readable responses
- **Vector Search**: Uses embeddings for similarity search

## Technologies

- **Python**: FastAPI, SQLAlchemy, embeddings
- **React**: JavaScript, CSS for UI
- **Database**: SQLite
- **ML**: Vector embeddings, semantic search


