from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    username: str
    password: str
    email: EmailStr

class UserLogin(BaseModel):
    username: str
    password: str



class Task(BaseModel):
    token: str
    name: str
    project_id: int


class TaskStatusUpdate(BaseModel):
    is_completed: bool

class TaskCreate(BaseModel):
    name: str