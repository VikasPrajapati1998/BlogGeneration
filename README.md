# AI Blog Generator

A complete blog generation application using LangChain, LangGraph, FastAPI, and MySQL.

## Features

- **Multi-Agent Blog Generation**: Uses LangGraph with 4 specialized agents:
  - Research Agent: Creates blog outlines
  - Title Agent: Generates engaging titles
  - Writer Agent: Writes comprehensive content
  - Editor Agent: Refines and polishes the content

- **FastAPI Backend**: RESTful API with MySQL database
- **Responsive Frontend**: Clean HTML/CSS/JavaScript interface
- **Full CRUD Operations**: Create, read, and delete blog posts

## Project Structure

```
blog_generation/
├── main.py              # FastAPI application
├── database.py          # Database models and connection
├── blog_agents.py       # LangGraph workflow and agents
├── requirements.txt     # Python dependencies
├── static/
│   ├── index.html      # Frontend UI
│   ├── style.css       # Styling
│   └── script.js       # JavaScript logic
└── README.md           # This file
```

## Prerequisites

1. **Python 3.8+**
2. **MySQL Server** running on localhost
3. **Ollama** with llama3.2:1b model installed

### Install Ollama and Model

```bash
# Install Ollama (if not already installed)
# Visit: https://ollama.ai

# Pull the model
ollama pull llama3.2:1b
```

## Setup Instructions

### 1. Create MySQL Database

```bash
mysql -u root -p
```

```sql
CREATE DATABASE blog_db;
EXIT;
```

### 2. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 3. Create Project Structure

```bash
mkdir blog_generation
cd blog_generation

# Create static folder
mkdir static

# Copy all files to respective locations:
# - main.py, database.py, blog_agents.py, requirements.txt in root
# - index.html, style.css, script.js in static/
```

### 4. Run the Application

```bash
# Make sure Ollama is running
ollama serve

# In another terminal, run the FastAPI app
python main.py
```

The application will be available at: **http://localhost:8000**

## Usage

1. **Generate a Blog**:
   - Enter a topic in the input field
   - Click "Generate Blog"
   - Wait for the AI agents to create your content
   - The generated blog will appear below

2. **View All Blogs**:
   - Scroll down to see all generated blogs
   - Click "View Full" to see complete content
   - Click "Delete" to remove a blog

3. **API Endpoints**:
   - `POST /api/generate` - Generate new blog
   - `GET /api/blogs` - Get all blogs
   - `GET /api/blogs/{id}` - Get specific blog
   - `DELETE /api/blogs/{id}` - Delete blog

## How It Works

### LangGraph Workflow

The blog generation follows this workflow:

```
Research → Title → Writer → Editor
```

1. **Research Agent**: Analyzes the topic and creates a structured outline
2. **Title Agent**: Generates an SEO-friendly, engaging title
3. **Writer Agent**: Writes comprehensive content based on the outline
4. **Editor Agent**: Reviews and refines the content for clarity and quality

### Agent Communication

Each agent receives the state from the previous agent and adds its contribution:
- State contains: topic, title, outline, content, refined_content
- Agents pass the enriched state through the workflow
- Final output is saved to the MySQL database

## Configuration

### Change LLM Model

Edit `blog_agents.py`:

```python
llm = ChatOllama(
    model="llama3.2:1b",  # Change to: qwen2.5:0.5b, mistral:latest, etc.
    temperature=0.7,
)
```

### Change Database Settings

Edit `database.py`:

```python
DATABASE_URL = "mysql+pymysql://root:YOUR_PASSWORD@localhost/blog_db"
```

## Troubleshooting

**Database Connection Error**:
- Verify MySQL is running
- Check username/password in `database.py`
- Ensure `blog_db` database exists

**Ollama Connection Error**:
- Make sure Ollama is running: `ollama serve`
- Verify model is installed: `ollama list`
- Pull model if missing: `ollama pull llama3.2:1b`

**Generation Takes Too Long**:
- The model needs time to generate quality content
- Smaller models (qwen2.5:0.5b) are faster but may produce lower quality
- Larger models (mistral:latest) are slower but higher quality

## Future Enhancements

- Add blog editing functionality
- Implement user authentication
- Add blog categories and tags
- Export blogs to PDF/Markdown
- Add image generation for blog posts
- Implement blog search functionality

## License

MIT License - Feel free to use and modify for your projects!