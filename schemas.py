from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import date

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        return v.strip()

    @field_validator('name', 'last_name')
    @classmethod
    def clean_names(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip().title()
        return v


class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=1)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        return v.strip()

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None

    @field_validator('name', 'last_name')
    @classmethod
    def clean_names(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip().title()
        return v

    @field_validator('date_of_birth')
    @classmethod
    def validate_date(cls, v: Optional[date]) -> Optional[date]:
        if v and v > date.today():
            raise ValueError('Дата рождения не может быть в будущем')
        if v and v.year < 1900:
            raise ValueError('Некорректный год рождения')
        return v