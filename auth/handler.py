from fastapi import HTTPException, status

from sqlalchemy.orm import Session

from auth import config

from typing import TypeVar, Generic, Optional

from passlib import hash

from . import models, schemas

import time
import jwt
import email_validator
import re
import os

T = TypeVar('T')

JWT_SECRET = os.getenv('JWT_SECRET')
ALGORITHM = "HS256"

# initialization, do not use this, no migration feature from fastapi itself, use alembic instead
def init_migrate():
    return config.Base.metadata.create_all(bind=config.engine)

# Dependency
def get_db():
    db = config.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_with_context_manager():
    with config.SessionLocal() as db:
        yield db



class DBUtils:

    @staticmethod
    def retrieve_all(db: Session, model: Generic[T]):
        return db.query(model).all()

    @staticmethod
    def retrieve_all_service(db: Session, model: Generic[T] = models.Service):
        return db.query(model).all()

    @staticmethod
    def retrieve_by_id(db: Session, model: Generic[T], id: int):
        return db.query(model).filter(model.id == id).all()

    @staticmethod
    def retrieve_by_service_name(db: Session, service_name: str, model: Generic[T] = models.Service):
        return db.query(model).filter(model.service_name == service_name).first()

    @staticmethod
    def retrieve_by_user_email(db: Session, email: str, model: Generic[T] = models.User):
        return db.query(model).filter(model.email == email).first()  # return class / kalau di django queryset

    @staticmethod
    def insert(db: Session, model: Generic[T]):
        db.add(model)
        db.commit()
        db.refresh(model)

    @staticmethod
    def update(db: Session, model: Generic[T]):
        db.commit()
        db.refresh(model)

    @staticmethod
    def delete(db: Session, model: Generic[T]):
        db.delete(model)
        db.commit()


async def create_user(db: Session, user: schemas.UserCreate):
    # check if email is valid
    try:
        valid = email_validator.validate_email(email=user.email)
        email = valid.email
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not valid, enter a valid email !"
        )
    hashed_password = hash.bcrypt.hash(user.password)
    user_obj = models.User(email=email, hashed_password=hashed_password) # balikannya instance User dan cukup 2 aja sisanya sudah ada default value
    DBUtils.insert(db=db, model=user_obj)
    return user_obj


def add_new_service(db: Session, service: str, labels: dict):
    service_obj = models.Service(service_name=service, label_type=labels.get('type'), label_lang=labels.get('lang'))
    DBUtils.insert(db=db, model=service_obj)
    return service_obj


def assign_user(db: Session, payload: schemas.ServiceAdder):
    # check if email is valid
    try:
        valid_email = email_validator.validate_email(email=payload.email).email # email <str>
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not valid, enter a valid email !"
        )

    user = DBUtils.retrieve_by_user_email(db=db, email=valid_email) # instance dari User models 
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User with that email doesn't exists! Please create user first !"
        )

    # validate list of services
    all_services = DBUtils.retrieve_all_service(db=db)
    all_service_name = [service.service_name for service in DBUtils.retrieve_all_service(db=db)]
    
    for svc in payload.services:
        if not re.fullmatch("^[\w-]+$", str(svc)):

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="service name can only contain letters (A-Z), numbers (0-9), dashes (-), and underscores (_)"
            )

        if svc not in all_service_name:
            detail = {
                "error": "please input the correct service list !",
                "available_services": [all_service_name]
                }
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail
            )
    # def any(__iterable: Iterable[object]) -> bool: ...
    if any([user_svc for user_svc in user.service if user_svc.service_name in payload.services]):
        anu = [user_svc.service_name for user_svc in user.service if user_svc.service_name in payload.services]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Service(s) {anu} sudah terdapat pada user!"
        )
    else:
        for svc_object in all_services:
            if svc_object.service_name in payload.services:
                # print(f"{svc_obj.service_name} masuk")
                user.service.append(svc_object)
                db.commit()

    return {"detail": f"Berhasil menambahkan service ke user {user.email}"}



# Crete JWT from instance User model (default_payload : 'email')
def create_token(user: models.User):
    user_schema_obj = schemas.User.from_orm(user) 
    # email='user@email.com' id=1 is_active=True date_created=datetime.datetime(2022, 9, 28, 18, 25, 13, 857118) 
    # type(user_schema_obj) -> <class 'auth.schemas.User'>
    user_dict = user_schema_obj.dict()
    del user_dict["date_created"]
    del user_dict["is_active"]
    del user_dict["id"]
    user_dict["exp"] = time.time() + 259200
    token = jwt.encode(user_dict, JWT_SECRET, algorithm=ALGORITHM)
    return dict(access_token=token)


async def decode_token(token: str):
    try:
        decode_token = jwt.decode(token, JWT_SECRET, algorithms=ALGORITHM)
        return decode_token if decode_token['exp'] >= time.time() else None
    except:
        return {"error": "unknown error"}


def authenticate_user(email: str, password: str, db: Session):
    user = DBUtils.retrieve_by_user_email(email=email, db=db)

    if not user:
        return False
    
    if not user.verify_password(password=password):
        return False
    
    return user
