# To-Do List API

A lightweight, containerized REST API for managing tasks with persistent SQLite storage, Pydantic input validation, and header-based API key authentication.

---

## Architecture

The service is built with **FastAPI** and organized into two decoupled layers: an HTTP routing/validation layer (`app/main.py`) and a SQLite persistence layer (`app/storage.py`). Incoming requests are validated against strict Pydantic schemas and path constraints before hitting parameterized SQL queries, preventing SQL injection and ensuring malformed payloads return structured `422` JSON responses rather than unhandled `500` errors. Read endpoints (`GET /tasks`) remain publicly accessible, while state-mutating endpoints (`POST`, `PUT`, `DELETE`) are protected via FastAPI dependency injection (`Depends`) using constant-time key comparison (`secrets.compare_digest`). The application is packaged into a slim Python Docker image that dynamically binds to the host's `$PORT` environment variable for serverless cloud deployment.

---

## Project Structure

```text
todo-list-api/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, auth dependency, schemas, and CRUD routes
│   └── storage.py       # SQLite connection management and parameterized queries
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
└── requirements.txt
```

---

## Quickstart (Local Setup)

### 1. Clone and install dependencies

```bash
git clone https://github.com/SuryaPrakash-24/todo-list-api.git
cd todo-list-api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy the example environment file and set your API key:

```bash
cp .env.example .env
export API_KEY="your-secret-key"      # On Windows PowerShell: $env:API_KEY="your-secret-key"
export DB_PATH="tasks.db"
```

### 3. Run the server

```bash
uvicorn app.main:app --reload
```

Open **`http://127.0.0.1:8000/docs`** in your browser to explore and test endpoints interactively via Swagger UI.

### Running with Docker

```bash
docker build -t todo-api .
docker run -p 8080:8080 -e PORT=8080 -e API_KEY="your-secret-key" todo-api
```

---

## API Reference & Usage Examples

| Method   | Endpoint           |     Auth Required     | Description                  |
| :------- | :----------------- | :-------------------: | :--------------------------- |
| `GET`    | `/`                |          No           | Health check                 |
| `GET`    | `/tasks`           |          No           | List all tasks               |
| `GET`    | `/tasks/{task_id}` |          No           | Retrieve a single task by ID |
| `POST`   | `/tasks`           | **Yes** (`X-API-Key`) | Create a new task            |
| `PUT`    | `/tasks/{task_id}` | **Yes** (`X-API-Key`) | Update an existing task      |
| `DELETE` | `/tasks/{task_id}` | **Yes** (`X-API-Key`) | Delete a task                |

_(Replace `BASE_URL` below with `http://127.0.0.1:8000` locally or your live deployed URL)._

### Create a Task (`POST /tasks`)

```bash
curl -X POST "http://127.0.0.1:8000/tasks" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{
    "title": "Ship capstone API",
    "description": "Write README and push final commit",
    "completed": false
  }'
```

### List All Tasks (`GET /tasks`)

```bash
curl "http://127.0.0.1:8000/tasks"
```

### Update a Task (`PUT /tasks/1`)

```bash
curl -X PUT "http://127.0.0.1:8000/tasks/1" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{
    "title": "Ship capstone API",
    "description": "Deployed and verified",
    "completed": true
  }'
```

### Python `requests` Example

```python
import requests

BASE_URL = "http://127.0.0.1:8000"
HEADERS = {"X-API-Key": "your-secret-key"}

# 1. Create a task
res = requests.post(
    f"{BASE_URL}/tasks",
    headers=HEADERS,
    json={"title": "Review PRs", "completed": False},
    timeout=5
)
res.raise_for_status()
task_id = res.json()["task"]["id"]

# 2. Fetch all tasks (public endpoint)
tasks = requests.get(f"{BASE_URL}/tasks", timeout=5).json()
print(tasks)
```

---

## What I Learned

- **Designing clean HTTP contracts:** Separating path parameters (identifying a specific resource like `/tasks/1`), query parameters (filtering/modifying behavior), and JSON request bodies (structured payloads for `POST`/`PUT`) makes APIs predictable and self-documenting in OpenAPI/Swagger.
- **Defense-in-depth validation & error handling:** Relying on Pydantic field constraints (`min_length`, `gt=0`) alongside custom exception handlers ensures bad client inputs fail fast with actionable `400`, `401`, `404`, and `422` JSON errors rather than leaking internal Python stack traces (`500`).
- **Decoupling storage from routing:** Moving from an in-memory Python list to SQLite highlighted how separating persistence logic (`storage.py`) from HTTP handlers (`main.py`) prevents index-shifting bugs and keeps business logic testable.
- **Production security & container habits:** Secrets belong strictly in environment variables (never hardcoded or committed to Git), API keys should be verified using constant-time comparisons (`secrets.compare_digest`) to prevent timing attacks, and serverless containers must bind dynamically to `$PORT`.
