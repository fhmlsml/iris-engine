from typing import Optional, Union, Dict, Any, List

from enum import Enum

from pydantic import BaseModel

import json


class CreateSecretData(BaseModel):
    label: Dict[Any, Any]



class NamespaceList(str, Enum):
    callback_dashboard  = "callback_dashboard"
    aegis_engine        = "aegis_engine"
    hestia_engine       = "hestia_engine"
    var_baru            = "var_baru"
    var_baru_lagi       = "var_baru_lagi"


# Need to be dynamic, but not possible for Swagger UI (?) need to implement frontend app
class LangEnum(str, Enum):
    java = "java"
    golang = "golang"
    javascript = "javascript"
    php = "php"
    python = "python"



class TypeEnum(str, Enum):
    env = "env"
    secret = "secret"



class InsertService(BaseModel):
    service_name : str = "app-service-name"


class InsertEnvVars(BaseModel):
    data_pertama : Optional[Union[str, Any]] = "valuenya"
    data_kedua : Optional[Union[str, Any]] = "lalalayeyeye"
    dan_seterusnya : Optional[Union[str, Any]] = "123456"


# class NamespaceList(str, Enum):

    # def __init__(self):    
    #     for data in google.list_current_secret():
    #         # print(data)
    #         setattr(self, data, data)
    
#     @classmethod
#     def testing(cls):
#         for data in google.list_current_secret():
#             # print(data)
#             setattr(cls, data, data)


# if __name__ == '__main__':
#     print(NamespaceList.testing())
#     print(getattr(NamespaceList, 'fhmisml'))
