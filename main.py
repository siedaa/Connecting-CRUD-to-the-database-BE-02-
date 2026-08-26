import sqlite3

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


def get_db_connection():
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tasks "
        "(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0)"
    )
    if conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [("Buy groceries", 0), ("Read a book", 1), ("Write code", 0)],
        )
    conn.commit()
    conn.close()


@app.on_event("startup")
def startup():
    init_db()


class Task(BaseModel):
    id: int
    title: str
    done: bool = False


class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: str
    done: bool


tasks: list[Task] = [
    Task(id=1, title="Buy groceries", done=False),
    Task(id=2, title="Read a book", done=True),
    Task(id=3, title="Write code", done=False),
]

next_id = 4


@app.get("/tasks", response_model=list[Task])
def get_tasks():
    return tasks


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    for task in tasks:
        if task.id == task_id:
            return task
    raise HTTPException(status_code=404, detail={"error": "Task not found"})


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(payload: TaskCreate):
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    global next_id
    task = Task(id=next_id, title=payload.title.strip())
    next_id += 1
    tasks.append(task)
    return task


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, payload: TaskUpdate):
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title is required")
    for task in tasks:
        if task.id == task_id:
            task.title = payload.title
            task.done = payload.done
            return task
    raise HTTPException(status_code=404, detail={"error": "Task not found"})


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    for i, task in enumerate(tasks):
        if task.id == task_id:
            tasks.pop(i)
            return
    raise HTTPException(status_code=404, detail={"error": "Task not found"})
