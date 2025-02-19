###########
# BUILDER #
###########

# Pull official base image
FROM python:3.11.4-slim-buster as builder

# Set work directory
WORKDIR /usr/src/app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*  # Clean up to reduce image size

# Linting
RUN pip install --upgrade pip flake8==6.0.0

# Copy source code for linting
COPY .. /usr/src/app/
RUN flake8 --ignore=E501,F401,W503,F811,E402 .

# Install Python dependencies
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt


#########
# FINAL #
#########

# Pull official base image
FROM python:3.11.4-slim-buster

# Create directory for the app user and necessary subdirectories
RUN mkdir -p /home/app /home/app/web /home/app/web/staticfiles /home/app/sh

# Create the app user
RUN addgroup --system app && adduser --system --group app

# Set environment variables
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
ENV SHELL_DIR=/home/app/sh

WORKDIR $APP_HOME

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends netcat && \
    rm -rf /var/lib/apt/lists/*  # Clean up to reduce image size

# Copy Python wheels and install dependencies
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache /wheels/*

# Copy scripts and set execute permissions
COPY ./compose/prod/django/entrypoint.sh $SHELL_DIR/entrypoint.sh
COPY ./compose/prod/django/start.sh $SHELL_DIR/start.sh
COPY ./compose/prod/django/celery/worker/start.sh $SHELL_DIR/start-celeryworker.sh
COPY ./compose/prod/django/celery/beat/start.sh $SHELL_DIR/start-celerybeat.sh
COPY ./compose/prod/django/celery/flower/start.sh $SHELL_DIR/start-flower.sh

# Remove Windows line endings and make scripts executable
RUN sed -i 's/\r$//g' $SHELL_DIR/*.sh && \
    chmod +x $SHELL_DIR/*.sh

# Copy the project files
COPY .. $APP_HOME

# Change ownership of the app files to the app user
RUN chown -R app:app $APP_HOME

# Switch to the app user
USER app

# Run entrypoint script
ENTRYPOINT ["/home/app/sh/entrypoint.sh"]
