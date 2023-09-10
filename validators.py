from datetime import timedelta

from fastapi import HTTPException, Request, Security, status
from fastapi.security.api_key import APIKeyHeader
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from fastapi_sqlalchemy import db as _db

from sqlalchemy.orm import Session

from auth.handler import DBUtils
from auth import handler

import jwt
import os



secret_key = os.getenv('OPS_SECRET_KEY')

descr = 'Key that used by operation teams to access some endpoints'
ops_secret_key = APIKeyHeader(name='secret_key', description=descr, auto_error=False)


async def ops_key_validator(key: str = Security(ops_secret_key)):
    if key != secret_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Invalid keys"
        )
    return key



async def verify_token(token: str):
    valid_data = await handler.decode_token(token)
    if valid_data is None or 'email' not in valid_data:
        raise HTTPException(
            status_code=400,
            detail="Invalid Token"
        )
    # https://stackoverflow.com/questions/65982681/how-to-access-the-database-from-unit-test-in-fast-api
    # When you get the error AttributeError: 'generator' object has no attribute 'query' 
    # python is telling you that the result of get_db() is not an sqlalchemy session object 
    # but rather a generator that yields a session object.
    # Try calling next() on your generator to get a session out of the generator.
    user = DBUtils.retrieve_by_user_email(db=next(handler.get_db_with_context_manager()), email=valid_data.get('email'))
    return user

# def validators(token, label):
#     if token == TEMP_TOKEN_ENVS
#       return token

async def service_and_user_validation(service: str, token: str, db: Session):
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
    user = await verify_token(token)
    current_user_service = [user_svc.service_name for user_svc in user.service]
    if service not in current_user_service:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,                                    
            detail='You are prohibited to access this service ! Contact Operation Team to enable access'
        )
    
    return True



class JWTBearer(HTTPBearer):

    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)

        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=403, detail="Invalid authentication sheme.")
            if self.verfity_jwt(credentials.credentials):
                raise HTTPException(
                    status_code=403, detail="Invalid token or expiredd token.")
            return credentials.credentials
        else:
            raise HTTPException(
                status=403, detail="Invalid authorization code.")

    def verfity_jwt(Self, jwttoken: str):
        isTokenValid: bool = False

        try:
            payload = jwt.decode(jwttoken, SECRET_KEY='test')
        except:
            payload = None

        if payload:
            isTokenValid = True
        return isTokenValid

# class JTWHandler():

#     def generate_token(data: dict, expires_delta: Optional[timedelta] = None):
#         to_encode = data.copy()
#         if expires_delta:
#             expire = datetime.utcnow() + expires_delta
#         else:
#             expire = datetime.utcnow() + timedelta(minutes=15)
#         to_encode.update({"exp": expire})
#         encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
#         return encode_jwt

#     def decode_token(token: str):
#         try:
#             decode_token = jwt.decode(token, SECRET_KEY, algorithm=[ALGORITHM])
#             return decode_token if decode_token["expires"] >= datetime.time() else None
#         except:
#             return{}


# class DynamicEnum(Enum):
#     pass

# def service_enum(func):
#     class NewEnum(Enum): 
#         pass
    
#     global DynamicEnum
#     new_enum = NewEnum(
#         'DynamicEnum', 
#         {
#            **{i.service_name: i.service_name for i in handler.get_all_services(db=handler.get_db_with_return())}
#         }
#     )
#     DynamicEnum._member_map_ = new_enum._member_map_
#     DynamicEnum._member_names_ = new_enum._member_names_
#     DynamicEnum._value2member_map_ = new_enum._value2member_map_

#     print("===== new enum svc =====")
#     print(dir(new_enum))
#     return DynamicEnum._member_map_

# service_enum()