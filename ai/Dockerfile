FROM python:3

WORKDIR /app
COPY ./ai/requirements.txt /app/
RUN apt update
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
