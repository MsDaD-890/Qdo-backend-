from dotenv import load_dotenv
load_dotenv("dotenv.env")

import os
SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret")

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from fastapi.encoders import jsonable_encoder

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from crud import get_user, create_user, verify_password

from database import engine, session_local, get_db
from models import Base, Note, Todo
from schemas import NoteResponse, NoteCreate, NoteWithMessage, TodoCreate, TodoResponse, TodoWithMessage, UserCreate, Token, WelcomeMessage


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/",response_model=WelcomeMessage, tags=["Main"])
def root():
    return{"success": True, "message": "Hello from FastAPI", "note": "Welcome to the Qdo API!"}

    

# Note


@app.get("/notes/", response_model=List[NoteResponse], tags=["Notes📝"])
async def get_notes(db: Session = Depends(get_db)):
    notes = db.query(Note).all()
    return jsonable_encoder([NoteResponse.from_orm(note) for note in notes])


@app.post("/note/", response_model=NoteWithMessage, tags=["Notes📝"])
async def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    db_note = Note(title=note.title, body=note.body)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)

    response = NoteWithMessage(
        note=NoteResponse(id=db_note.id, title=db_note.title, body=db_note.body, created_at=db_note.created_at.isoformat()),
        success=True,
        message="Note created successfully"
    )

    return jsonable_encoder(response)


@app.put("/note/{note_id}", response_model=NoteWithMessage, tags=["Notes📝"])
async def update_note(note_id: int, note: NoteCreate, db: Session = Depends(get_db)):
    db_note = db.query(Note).filter(Note.id == note_id).first()
    if db_note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    db_note.title = note.title
    db_note.body = note.body
    db.commit()
    db.refresh(db_note)

    response = NoteWithMessage(
        note=NoteResponse(id=db_note.id, title=db_note.title, body=db_note.body, created_at=db_note.created_at.isoformat()),
        success=True,
        message="Note updated successfully"
    )

    return jsonable_encoder(response)


@app.delete("/note/{note_id}", response_model=NoteWithMessage, tags=["Notes📝"])
async def delete_note(note_id: int, db: Session = Depends(get_db)):
    db_note = db.query(Note).filter(Note.id == note_id).first()
    if db_note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    db.delete(db_note)
    db.commit()

    response = NoteWithMessage(
        note=NoteResponse(id=db_note.id, title=db_note.title, body=db_note.body, created_at=db_note.created_at.isoformat()),
        success=True,
        message="Note deleted successfully"
    )

    return jsonable_encoder(response)


@app.get("/note/search/", response_model=List[NoteResponse], tags=["Notes📝"])
async def search_notes(query: str = Query(..., min_length=1, max_length=255), skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    result = db.query(Note).filter(
        (Note.title.ilike(f"%{query}%")) | 
        (Note.body.ilike(f"%{query}%"))
    ).offset(skip).limit(limit).all()

    return result


# ToDo


@app.post("/todos/", response_model=TodoWithMessage, tags=["Qdo List🧾"])
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    db_todo = Todo(task=todo.task)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)

    response = TodoWithMessage(
        todo=TodoResponse(id=db_todo.id, task=db_todo.task, completed=db_todo.completed),
        success=True,
        message="You created successfully"
    )

    return jsonable_encoder(response)


@app.get("/todos/", response_model=List[TodoResponse], tags=["Qdo List🧾"])
def get_todos(db: Session = Depends(get_db)):
    todos = db.query(Todo).all()
    return todos


@app.put("/todos/{todo_id}", response_model=TodoResponse, tags=["Qdo List🧾"])
def update_todo(todo_id: int, todo: TodoCreate, db: Session = Depends(get_db)):
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if db_todo is None:
        raise HTTPException(status_code=404, detail="To-Do not found")
    db_todo.task = todo.task
    db.commit()
    db.refresh(db_todo)
    return db_todo


@app.delete("/todos/{todo_id}", response_model=TodoResponse, tags=["Qdo List🧾"])
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if db_todo is None:
        raise HTTPException(status_code=404, detail="To-Do not found")
    db.delete(db_todo)
    db.commit()
    return db_todo


@app.put("/todos/{todo_id}/complete", response_model=TodoResponse, tags=["Qdo List🧾"])
def toggle_todo_complete(todo_id: int, db: Session = Depends(get_db)):
    db_todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if db_todo is None:
        raise HTTPException(status_code=404, detail="To-Do not found")
    
    db_todo.completed = not db_todo.completed
    db.commit()
    db.refresh(db_todo)
    return db_todo




oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

# Entrance and registration

@app.post("/token", response_model=Token, tags=["Registration®️"])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register/", tags=["Registration®️"])
def register(user: UserCreate, db: Session = Depends(get_db)):
    if get_user(db, user.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    create_user(db, user.username, user.password)
    return {"message": "User registered"}

# Protected route
@app.get("/protected/", tags=["Registration®️"])
def protected_route(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=401,
                detail={"error": "Invalid token", "message": "Please log in again"}
            )
        return {"message": f"Hello, {username}!"}
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail={"error": "Invalid token", "message": "Token is expired or invalid"}
        )

