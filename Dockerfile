# Use an official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.12-slim

RUN pip install --upgrade pip

ENV APP_HOME=/app
WORKDIR $APP_HOME

# Service must listen to $PORT environment variable.
# This default value facilitates local development.
ARG PORT
EXPOSE 8080
ENV TZ="America/Bogota"

# Run updates and install psycopg2 dependencies
RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install psycopg2
RUN apt-get install ffmpeg libsm6 libxext6  -y

# Setting this ensures print statements and log messages
# promptly appear in Cloud Logging.
ENV PYTHONUNBUFFERED=TRUE

# Copy and execute requirements file
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy local code to the container image.
COPY . .

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
CMD exec uvicorn main:app --host 0.0.0.0 --port 8080