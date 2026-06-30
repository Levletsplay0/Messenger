from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    username: str
    password: str
    email: EmailStr
    name: str
    last_name: str

class UserLogin(BaseModel):
    username: str
    password: str
