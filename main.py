from fastapi import Body, Depends, Path, Request, FastAPI, Form, Security, HTTPException, Header, status, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi_versioning import VersionedFastAPI, version
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.security.api_key import APIKeyHeader, APIKey

from fastapi_sqlalchemy import DBSessionMiddleware  # middleware helper

from starlette.responses import RedirectResponse

from collections import defaultdict
from logging import exception

from typing import Any, Dict, Union
from enum import Enum
from sqlalchemy.orm import Session

from schemas import InsertEnvVars, InsertService, NamespaceList, CreateSecretData, LangEnum, TypeEnum

from auth import handler, config, models
from auth.handler import DBUtils
from auth.schemas import UserCreate, ServiceAdder

from gcp.utils import GSMController

import validators

import json
import os
import re


desc = """
A Simple API Endpoints - Tools to create&manage environment variables & secret for your services with Google Secret Manager.\n
Bug report / feedback - contact ops team \n
or find <a href=/me/discord> me </a> on discord.
"""

app = FastAPI(
        title=f"Ἴ\u03c1\u03b9ς API ( {os.getenv('TITLE_ENV')} )", 
        version="1.0.0", 
        description=desc, 
        redoc_url=None, 
        openapi_url=None
    )

# app.add_middleware(DBSessionMiddleware, db_url=config.DATABASE_URL)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/generate")

# ============================================================ < Users > ============================================================ #

@app.post("/register", status_code=status.HTTP_201_CREATED, tags=["Users"])
@version(1)
async def create_user(user: UserCreate, db: Session = Depends(handler.get_db)):
    user_get = DBUtils.retrieve_by_user_email(email=user.email, db=db) 
    # user_get instance dari User models balikan dari get_user_by_email()
    if user_get:
        raise HTTPException(
            status_code=400,
            detail="User with that email already exists"
        )
    _user = await handler.create_user(user=user, db=db) # instance dari User models balikan dari create_user()

    # generate jwt with email only payload and return jwt
    # after this, should be add service to this user
    return handler.create_token(user=_user)


@app.post("/generate", status_code=status.HTTP_200_OK, tags=["Users"])
@version(1)
async def generate_token(user: UserCreate, db: Session = Depends(handler.get_db)):
    user = handler.authenticate_user(
        email=user.email, 
        password=user.password, 
        db=db
    ) # <auth.models.User object at memory>

    if not user:
        raise HTTPException(
            status_code=401, 
            detail="Invalid Credentials"
        )

    return handler.create_token(user=user)

# ============================================================ < Users > ============================================================ #



# ============================================================ < Services > ============================================================ #

@app.get("/list", status_code=status.HTTP_200_OK, tags=["Services"])
@version(1)
async def get_service_list(lang: LangEnum, db: Session = Depends(handler.get_db)):
    all_data = [ service.service_name for service in DBUtils.retrieve_all_service(db=db) if service.label_lang == lang.value ]
    return { 
        lang.value: {
            'env': [ data for data in all_data if 'secret' not in data ],
            'secret': [ data for data in all_data if 'secret' in data ]
        }
    }



# @service_enum
@app.get("/get", status_code=status.HTTP_200_OK, tags=["Services"])
@version(1)
async def get_current_env_vars(service: str, token: str = Header(title='User JWT\'s'), db: Session = Depends(handler.get_db)):
    await validators.service_and_user_validation(service=service, token=token, db=db)
    try:
        data = GSMController(service).access_secret_payload()
        jsonable = json.loads(data) # convert from byte
        return jsonable
    except Exception as error:
        print(error)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,                                    
            detail=f'Secret {service} not found or has no versions.'
        )



@app.post("/update", status_code=status.HTTP_201_CREATED, tags=["Services"])
@version(1)
async def update_service_env(
    request: Request, 
    service: str, 
    payload: InsertEnvVars, 
    token: str = Header(title='JWT Token'), 
    db: Session = Depends(handler.get_db)
):
    await validators.service_and_user_validation(service=service, token=token, db=db)
    payloads = await request.json() # bisa diganti jg dengan payload
    try:
        response = GSMController(service).update_current_secret(payloads)
        return response
    except Exception as error:
        print(error)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,                                    
            detail=f"Secret '{service}' Not found in GCP, if service '{service}' is available in /list endpoint and you get this error, try to use /synchronize endpoint or manually create '{service}' from /ops/new-secret endpoint"
        )

# ============================================================ < Services > ============================================================ #


# ============================================================ < Ops Team > ============================================================ #

@app.post("/ops/assign", status_code=status.HTTP_201_CREATED, tags=["Ops Team"])
@version(1)
async def add_services_to_user(
        payload: ServiceAdder, 
        key: APIKey = Depends(validators.ops_key_validator), 
        db: Session = Depends(handler.get_db)
    ):
    return handler.assign_user(db=db, payload=payload)



@app.post("/ops/new-secret", status_code=status.HTTP_201_CREATED, tags=["Ops Team"])
@version(1)
async def create_new_gcp_secret(label_type: TypeEnum, label_lang: LangEnum, payload: InsertService = Body(...), key: APIKey = Depends(validators.ops_key_validator), db: Session = Depends(handler.get_db)):
    service = payload.service_name
    labels = dict(type=label_type.value, lang=label_lang.value)
    if not re.fullmatch("^[\w-]+$", str(service)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="service name can only contain letters (A-Z), numbers (0-9), dashes (-), and underscores (_)"
        )
    svc_instance = DBUtils.retrieve_by_service_name(db=db, service_name=service)
     # This try and if statement below is for validation purposes, it will check is it already in db or not and vice versa
    try:
        # if service not in gcp, create new service
        new = GSMController(service).create_new_secret(labels=labels)
        
        # Add service to database after adding to gcp
        # check if service alreay in db or not

        # if not, add it to db
        if not svc_instance:
            handler.add_new_service(db=db, service=service, labels=labels)

        # if the service not in gcp but already in db
        # and if the service labels in db are different with the input, delete and change it
        elif svc_instance.label_type != labels.get('type') or svc_instance.label_lang != labels.get('lang'):
            DBUtils.delete(db=db, model=svc_instance)
            handler.add_new_service(db=db, service=service, labels=labels)

    # if service already in gcp or another error occured
    except Exception as error:
        print(error)
        res = GSMController(service).get_single_secret()
        # if not in db, it will write the service to service table
        if 'already exists' in str(error):

            # if the service already in gcp but not in db, insert to db
            if not svc_instance:
                handler.add_new_service(db=db, service=service, labels=labels)

                 # change labels -> sesuaikan dengan yg diinput jika berbeda
                
            #     raise HTTPException(
            #         status_code=status.HTTP_409_CONFLICT,
            #         detail=f'Secret {service} already exists. Successfully added to /list'
            # )
            # if the service already in gcp and db, validate the labels
            if res.labels.get('type') != labels.get('type') or res.labels.get('lang') != labels.get('lang'):
                update_metadata = GSMController(service).update_secret_metadata(labels=labels)
                svc_instance = DBUtils.retrieve_by_service_name(db=db, service_name=service)
                svc_instance.label_type = labels.get('type')
                svc_instance.label_lang = labels.get('lang')
                DBUtils.update(db=db, model=svc_instance)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f'Secret {service} already exists. Metadata (labels) updated.'
                )

            # elif svc_instance:
            #     DBUtils.delete(db=db, model=svc_instance)
            #     # get the existing labels from gcp, not from the input and update it to db
            #     res = GSMController(service).get_single_secret()
            #     existing_labels_gcp = dict(lang=res.labels.get('lang'), type=res.labels.get('type'))
            #     handler.add_new_service(db=db, service=service, labels=existing_labels_gcp)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f'Secret {service} already exists.'
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )

    return {
        "success": {
            "secret_name": f"Success create secret {service}"
            }
        }

@app.put("/ops/metadata", status_code=status.HTTP_200_OK, tags=["Ops Team"])
@version(1)
async def edit_secret_label_metadata(service: str, label_type: TypeEnum, label_lang: LangEnum, key: APIKey = Depends(validators.ops_key_validator), db: Session = Depends(handler.get_db)):
    labels = dict(type=label_type.value, lang=label_lang.value)
    all_service_name = [service.service_name for service in DBUtils.retrieve_all_service(db=db)]
    if service not in all_service_name:
        detail = {
            "error": "please input the correct service list !",
            "available_services": [all_service_name]
            }
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,                                    
            detail=detail
        )
    try:
        svc_instance = DBUtils.retrieve_by_service_name(db=db, service_name=service)
        GSMController(service).update_secret_metadata(labels=labels)
        svc_instance.label_type = labels.get('type')
        svc_instance.label_lang = labels.get('lang')
        DBUtils.update(db=db, model=svc_instance)
    except Exception as error:
        print(error)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"{error}"}
        )
    return {"detail": f"Success update {service} labels"}



@app.delete("/ops/delete", status_code=status.HTTP_200_OK, tags=["Ops Team"])
@version(1)
async def delete_secret(service: str, key: APIKey = Depends(validators.ops_key_validator), db: Session = Depends(handler.get_db)):
    svc_instance = DBUtils.retrieve_by_service_name(db=db, service_name=service)
    try:
        # delete from the gcp first
        deletion = GSMController(service).delete_secret()
        if svc_instance:
            DBUtils.delete(db=db, model=svc_instance)
            
            # if delete is None:
            #     db.delete()
        return {"detail": f"Success delete secret {service}"}
    except Exception as error:
        print(error)
        # if not in gcp but exist in db
        if svc_instance:
            DBUtils.delete(db=db, model=svc_instance)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Secret {service} not found or something went wrong.'
        )



@app.get("/synchronize", status_code=status.HTTP_200_OK, tags=["Ops Team"])
@version(1)
def synchronize_db_and_gcp_secret(
        key: APIKey = Depends(validators.ops_key_validator), 
        db: Session = Depends(handler.get_db)
    ):
    list_in_gcp_secret = GSMController.list_current_secrets_name()
    list_in_db_by_name = [ svc.service_name for svc in DBUtils.retrieve_all_service(db=db) ]

    try:
        # patokannya adalah gcp, jika di gcp gk ada , di db jg hapus
        # already in db but not in gcp, delete yg di db
        for svc_instance in DBUtils.retrieve_all_service(db=db):
            if svc_instance.service_name not in list_in_gcp_secret:
                DBUtils.delete(db=db, model=svc_instance)
                # new = GSMController(svc_instance.service_name).create_new_secret(
                #     labels=dict(
                #         type=svc_instance.label_type, 
                #         lang=svc_instance.label_lang
                #     )
                # )
        
        # already in gcp but not in db
        for gcp_secret in GSMController.list_current_secrets():
            secret_name = gcp_secret.name.split("/")[-1]
            if secret_name not in list_in_db_by_name and secret_name.startswith('app'):
                handler.add_new_service(
                    db=db, 
                    service=secret_name, 
                    labels=dict(
                        type=gcp_secret.labels.get('type'), 
                        lang=gcp_secret.labels.get('lang')
                    )
                )
        for gcp_secret in GSMController.list_current_secrets():
            parsed_name = gcp_secret.name.split("/")[-1]
            for svc_instance in DBUtils.retrieve_all_service(db=db):
                if parsed_name == svc_instance.service_name:
                    if gcp_secret.labels.get('type') != svc_instance.label_type or gcp_secret.labels.get('lang') != svc_instance.label_lang:
                        svc_instance.label_type = gcp_secret.labels.get('type')
                        svc_instance.label_lang = gcp_secret.labels.get('lang')
                        DBUtils.update(db=db, model=svc_instance)

        return {"detail": f"Success synchronize secret & metadata"}
    except Exception as error:
        print(error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,                                    
            detail=str(error)
        )


@app.get("/me/discord", include_in_schema=False)
async def discordz():
  return RedirectResponse("https://discordapp.com/users/407955743233540098")


# @app.get("/listzz", status_code=status.HTTP_200_OK, tags=["Services"])
# @version(1)
# def get_service_list(db: Session = Depends(handler.get_db)):
#     val = gcp.list_current_secrets()
#     # exist = DBUtils.retrieve_all_service(db=db)
#     _list = []
#     _seclist = []
#     for data in val:
#         _list.append(data.name)
#         _seclist.append(data.labels.popitem())
#     return {"service_list": _list, "label_list": _seclist}



app = VersionedFastAPI(app, version_format='{major}', prefix_format='/v{major}')