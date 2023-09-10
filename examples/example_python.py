

import os
import json

from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()

name = f"projects/{os.getenv('PROJECT_ID')}/secrets/app-nama-service/versions/latest"

response = client.access_secret_version(request={"name": name})

json_string_data = response.payload.data.decode("UTF-8")

json_data = json.loads(json_string_data)


for key, value in json_data.items():
    print(key + '=' + str(value))
