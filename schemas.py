from pydantic import BaseModel
from typing import Optional
from datetime import datetime



class TodoBase(BaseModel):
    task: str
    completed: bool = False


class TodoCreate(TodoBase):
    pass


class TodoResponse(BaseModel):
    id: int
    task: str
    completed: bool

    class Config:
        orm_mode = True


class TodoWithMessage(BaseModel):
    todo: TodoResponse
    success: bool
    message: str





class WelcomeMessage(BaseModel):
    success: bool
    message: str
    note: str


class NoteBase(BaseModel):
    title: str
    body: str


class NoteCreate(NoteBase):
    pass


class NoteResponse(BaseModel):
    id: int
    title: str
    body: str
    created_at: datetime

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            title=obj.title,
            body=obj.body,
            created_at=obj.created_at 
        )

    class Config:
        from_attributes = True


class NoteWithMessage(BaseModel):
    note: NoteResponse
    success: bool
    message: str






class UserCreate(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


