from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    username: str
    password: str
    email: EmailStr

class UserLogin(BaseModel):
    username: str
    password: str
