FROM python:3.11.10-alpine3.20

ARG PROD_MODE="false"

# Create user
RUN addgroup app && adduser -S -G app app

# Create dir for logs
RUN mkdir /var/log/app/ && chown app:app /var/log/app/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LOGS_DIR="/var/log/app/"

WORKDIR /app

RUN apk update

# Required to install application dependencies
RUN apk add gcc python3-dev musl-dev linux-headers

# Install ffmpeg
RUN apk add ffmpeg

# Install pipenv
RUN pip install --upgrade pip 
RUN pip install pipenv

# Install application dependencies
COPY Pipfile Pipfile.lock /app/ 
RUN if [ "$PROD_MODE" = "true" ] ; \
    then \
    pipenv install --system --deploy ; \
    else \
    pipenv install --system --dev ; \
    fi

USER app

# Copy application code
COPY . /app/

EXPOSE 8000