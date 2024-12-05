FROM python:3

WORKDIR /app
COPY ./ai/requirements.txt /app/
RUN apt-get update && apt-get install -y \
    postgresql \
    postgresql-contrib \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
