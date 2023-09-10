
![Logo](https://images.saymedia-content.com/.image/c_limit%2Ccs_srgb%2Cq_auto:eco%2Cw_379/MTc2Mjg3MjUxODM0MDg2NTcz/the-goddess-iris-in-greek-mythology.webp)


#
# Ἴρις App ( Iris ) 
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)

[![python3.x](https://img.shields.io/badge/3.8-blue.svg?style=for-the-badge&logo=python&label=Python&logoColor=white)](https://www.python.org/downloads/release/python-3815/)

[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://docs.docker.com/engine/install/)

[ ![Google Cloud](https://img.shields.io/badge/GoogleCloud-%234285F4.svg?style=for-the-badge&logo=google-cloud&logoColor=white)](https://cloud.google.com/)


> #### [ This repository is for archiving the source code of internal software that i made for my previous company to manage envvars&secrets with [Google Secret Manager](https://cloud.google.com/secret-manager) ]
#
A Simple API Endpoints - Tools to create and manage secret & environment 
variables for your applications (Google Cloud Platform) using [Google Secret Manager](https://cloud.google.com/secret-manager) (GSM).


## Authors

- [fhmlsml](https://www.github.com/fhmlsml)
#

## API Reference

### Docs ( Swagger UI & ReDoc )

Access the Swagger UI & Redoc


- http://localhost:8000/v1/docs

- http://localhost:8000/v1/redoc


#
## Usage / Examples (v1)
### [ Users ] 
#### Register User & Generate Token (If token expired)

```http
  POST /v1/register

  POST /v1/generate
```

#### Curl

```curl
curl -X 'POST' \
  'http://{base_url}/v1/register' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{                    
  "email": "me@fhmisml.moe",
  "password": "yourpersonalsecretpassword"
}'
```
```curl
curl -X 'POST' \
  'http://{base_url}/v1/generate' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "email": "me@fhmisml.moe",
  "password": "yourpersonalsecretpassword"
}'
```

#
### [ Services ]
#### List, Get, and Update Secret & Environment Variables
```http
  GET /v1/list?lang={lang}

  GET /v1/get?service={service_name}

  POST /v1/update?service={service_name}
```

#### Curl

```curl
curl -X 'GET' \
  'http://{base_url}/v1/list?lang={lang}' \
  -H 'accept: application/json'
```
```curl
curl -X 'GET' \
  'http://{base_url}/v1/get?service={service_name}' \
  -H 'accept: application/json' \
  -H 'token: your-jwt-token'
```
```curl
curl -X 'POST' \
  'http://{base_url}/v1/update?service={service_name}' \
  -H 'accept: application/json' \
  -H 'token: your-jwt-token' \
  -H 'Content-Type: application/json' \
  -d '{
  "data1": "val1",
  "data2": "val2",
  "data3": "val3"
}'
```


#

| Parameter             | Name              | Type     | Description                |
| :-------- | :-------- | :-------          | :------------------------- |
| `query`   | `lang`    | `string`          | **Required**.  |
| `query & header`      | `service & token` | `string` | **Required**. Service Name & JWT |
| `query & header`      | `service & token` | `string` | **Required**. Service Name & JWT |

#
### Ops Team
#### Operations Team Only
```http
  POST /v1/ops/assign

  POST /v1/ops/new-secret

  PUT /v1/ops/metadata

  DELETE /v1/ops/delete

  GET /v1/synchronize


```

| Parameter | Name                      | Type     | Description                |
| :-------- | :------------------------ | :------- | :-------------------- |
| `-`       | `-`                       | `-`      | **-**                 |
| `query`   | `label_type & label_lang` | `string` | **Required**.  label_type  & label_lang |
| `query`   | `service & token` | `string` | **Required**. Service Name & JWT |
| `query`   | `lang`   | `string` | **Required**.  |
| `query`   | `lang`   | `string` | **Required**.  |



##

## Implementation
After adding new env or secret in _irisapp_ or [Google Secret Manager](https://cloud.google.com/secret-manager) directly, 
your applications or services need to access the secret that you have added.\
\
To do that, you need to use [Google Secret Manager Library](https://cloud.google.com/secret-manager/docs/reference/libraries), for example in python :

### --> _**For further information, check [this link](https://cloud.google.com/secret-manager/docs/samples/secretmanager-access-secret-version), choose your preferred language, and follow the instructions**_

```python
import os
import json

from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()

name = f"projects/{os.getenv('PROJECT_ID')}/secrets/app-your-service-name/versions/latest"

# Access the secret version.
response = client.access_secret_version(request={"name": name})

# the json_string_data will be -> {"data1": "val1", "data2": "val2", "data3": 1234}
json_string_data = response.payload.data.decode("UTF-8")    # -> if this is not decoded, json_string_data is a BYTE type

# json_string_data is a STRING, convert to json (or actually dict in python)
json_data = json.loads(json_string_data)    # -> json_data variable is a JSON

# loop the json_data and set the environment variables
for key, value in json_data.items():
    # set the env vars
    os.environ[key] = str(value)
```

No need to worry about permissions, all apps/services that have been deployed have an ability/permissions to access env/secret data that you passed in _irisapp_ or [Google Secret Manager](https://cloud.google.com/secret-manager) directly and they have a `PROJECT_ID` environment variable. The `PROJECT_ID` environment variable is dynamic based on where the app is deployed. 
\
_*If you are wondering how all apps / services have permission to access secret, the answer is [secretmanager.secretAccessor](https://cloud.google.com/secret-manager/docs/access-control#secretmanager.secretAccessor) roles is attached to the resources._

The `PROJECT_ID` environment variable on each services is set by kubernetes configmap yaml manifest from each service repository and the value in the configmap will be substituted by Jenkinsfile in CI/CD workflow. It would be nice if it uses [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity). \
\
*side notes:\
By enabling workload-identity at the cluster level has downtime to the control plane (no editing of the cluster possible but existing workloads are unaffected)\
By enabling workload-identity at the [Node Pool](https://cloud.google.com/kubernetes-engine/docs/concepts/node-pools) level recreates nodes (gke automatically cordons and recreates nodes).


##


## Contributing & Run Locally

In order to run this app locally & for development purposes, you need to use your own [Google Cloud Platform](https://cloud.google.com/) account for development and generate the JSON key from [Service Account](https://cloud.google.com/iam/docs/service-accounts). 

#


### Requirements to run this app locally & development :
- [Google Cloud Platform](https://cloud.google.com/) 
- [Docker](https://www.docker.com/) __( version 20+ is recommended )__
- [Docker Compose](https://docs.docker.com/compose/install/) 
- [Linux shell / Bash](https://www.gnu.org/software/bash/) ( if you're using windows or other os)
#

### Generate Secret Manager Service Account Key
One of the methods to grant access your local machine to GCP **_in order to run this app_** is you need to generate [Service Account](https://cloud.google.com/iam/docs/service-accounts) key with [Secret Manager Admin](https://cloud.google.com/secret-manager/docs/access-control#secretmanager.admin) roles permission.

If you don't really know how it works, learn [how to generate SA JSON key in GCP](https://cloud.google.com/iam/docs/creating-managing-service-account-keys) or you can ask DevOps / Ops team to generate it.

#

### Clone the project

```bash
  $ git clone https://github.com/fhmlsml/iris-engine
  
  or

  $ git clone git@github.com:fhmlsml/iris-engine.git
```

### Edit deploy-local.sh and copy & rename your service-acc.json and copy to SA directory

Remember, you need to edit `deploy-local.sh` this will deploy standalone database in your local system as docker container and after editing those values in `deploy-local.sh` follow the steps below :
```bash
  $ cd iris-engine

  # edit deploy-local.sh
  # copy and rename your service account to SA directory, json key filename must be "sa.json" or you can change from docker-compose-local.yaml file
  $ mv /your/path/to/your/serviceaccount.json ./SA/sa.json
```

### Substitute env var with [envsubst](https://www.gnu.org/software/gettext/manual/html_node/envsubst-Invocation.html) and run iris with docker-compose

```bash
  $ source deploy-local.sh

  ## run from stdin
  $ envsubst < docker-compose-local.yaml | docker-compose -f - up --build -d

  ## After the db and app containers are running, you need to run database migration for the first time and one time only
  ## Since from docker-compose-local.yaml already mount the volume (./alembic/versions:/app/alembic/versions)
  $ alembic upgrade head
```


### Stop the service

```bash
  $ docker-compose -f docker-compose-local.yaml down

  # no need to worry, your volume / persistent data still exist
  # you can check it with `docker volume ls`
```

#

## Database Migration
If you are modifying the `auth/models.py` file, you need to run migration with [Alembic](https://alembic.sqlalchemy.org/) 
since FastAPI uses [SQLAlchemy](https://www.sqlalchemy.org/). Please keep track of these migrations file in `alembic/versions` directory to persist the current users and service in _irisapp_.
\
\
After you modify the `auth/models.py` you have to commit your changes with alembic autogenerate (you have to do this command inside the irisapp container since it's already mounted from docker-compose, the migration file will persist to your local system and ready to push in repository):
```bash
$ alembic revision --autogenerate -m "your commit messages"
```

Then apply the changes :
```bash
$ alembic upgrade head
```

if you encounter any issues, do a rollback :
```bash
$ alembic downgrade -1

# or

$ alembic downgrade <identifier> # randomly generated unique identifier, you can check with `alembic history`
```



## CI/CD

This project uses 1 main branch, it will trigger [Cloud Build](https://cloud.google.com/build) pipeline if create a new tag and it will deploy to dev, stg, and production environment, no need to worry about failure or something. \
The image repository for this project is [Artifact Registry](https://cloud.google.com/artifact-registry) and the cloud build worker currently managed in `x-project`.



## License

[-- license --](https://choosealicense.com)

