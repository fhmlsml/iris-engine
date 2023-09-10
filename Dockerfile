FROM python:3.8

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR 1

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir --upgrade -r requirements.txt


EXPOSE 8000