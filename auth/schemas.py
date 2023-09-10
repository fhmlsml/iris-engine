from datetime import datetime

from typing import Any, Dict, List

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr = 'me@fhmisml.moe'



class UserCreate(UserBase):
    password: str = 'yourpersonalsecretpassword'

    class Config:
        orm_mode = True



class User(UserBase):
    id: int
    is_active: bool
    date_created: datetime

    class Config:
        orm_mode = True



class ServiceAdder(BaseModel):
    email: EmailStr = 'me@fhmisml.moe'
    services: List[Any] = ["service1", "service2"]
    
    class Config:
        orm_mode = True