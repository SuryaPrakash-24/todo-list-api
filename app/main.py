import os
import secrets
from contextlib import asynccontextmanager
from typing import Annotated, Optional
from fastapi import FastAPI, Depends, HTTPException, Path, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from app import storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    storage.init_db()
    yield


app = FastAPI(
    title="To-Do List API",
    description="Persistent CRUD API with SQLite storage and X-API-Key authentication.",
    version="1.0.0",
    lifespan=lifespan,
)

# --- Auth ---
API_KEY = os.getenv("API_KEY", "dev-secret-key")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: Optional[str] = Depends(api_key_header)) -> str:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required header: 'X-API-Key'",
        )
    if not secrets.compare_digest(api_key, API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or unauthorized API key",
        )
    return api_key


# --- Clean Validation Error Handler ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        field_loc = " -> ".join(str(loc) for loc in err.get("loc", []) if loc != "body")
        errors.append(
            {
                "field": field_loc or "body",
                "message": err.get("msg"),
                "type": err.get("type"),
            }
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_type": "ValidationError",
            "status_code": 422,
            "details": errors,
        },
    )


# --- Schema ---
class TaskInput(BaseModel):
    title: str = Field(
        ..., min_length=1, max_length=100, description="Task title (1–100 chars)"
    )
    description: Optional[str] = Field(
        default=None, max_length=500, description="Optional details"
    )
    completed: bool = Field(default=False, description="Completion status")


# Positive integer path constraint for task_id
TaskID = Annotated[int, Path(gt=0, description="Positive integer ID of the task")]


# --- Endpoints ---


@app.get("/", tags=["System"])
def health_check():
    return {"status": "ok", "message": "To-Do List API is live. Visit /docs to test."}


@app.get("/tasks", tags=["Tasks"])
def list_tasks():
    tasks = storage.fetch_all_tasks()
    return {"message": "Task List Fetched!", "count": len(tasks), "tasks": tasks}


@app.get("/tasks/{task_id}", tags=["Tasks"])
def get_task(task_id: TaskID):
    task = storage.fetch_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )
    return {"message": "Task Fetched!", "task": task}


@app.post("/tasks", status_code=status.HTTP_201_CREATED, tags=["Tasks"])
def create_task(payload: TaskInput, _key: str = Depends(verify_api_key)):
    # Business rule example (400 Bad Request)
    if not payload.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task title cannot be whitespace only.",
        )
    created = storage.insert_task(
        title=payload.title.strip(),
        description=payload.description,
        completed=payload.completed,
    )
    return {"message": "Task Added!", "task": created}


@app.put("/tasks/{task_id}", tags=["Tasks"])
def update_task(
    task_id: TaskID, payload: TaskInput, _key: str = Depends(verify_api_key)
):
    if not payload.title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task title cannot be whitespace only.",
        )
    updated = storage.update_task_by_id(
        task_id=task_id,
        title=payload.title.strip(),
        description=payload.description,
        completed=payload.completed,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )
    return {"message": "Task Updated!", "task": updated}


@app.delete("/tasks/{task_id}", tags=["Tasks"])
def delete_task(task_id: TaskID, _key: str = Depends(verify_api_key)):
    deleted = storage.delete_task_by_id(task_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )
    return {"message": "Task Deleted!"}
