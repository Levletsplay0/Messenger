from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import date
import re

class UserRegister(BaseModel):
    username: str
    password: str
    email: EmailStr
    name: str = Field(None, min_length=1, max_length=50)
    last_name: str = Field(None, min_length=1, max_length=50)

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None

    @field_validator('date_of_birth')
    @classmethod
    def validate_date(cls, v: Optional[date]) -> Optional[date]:
        if v and v > date.today():
            raise ValueError('Дата рождения не может быть в будущем')
        if v and v.year < 1900:
            raise ValueError('Некорректный год рождения')
        return v