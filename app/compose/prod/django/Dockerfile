###########
# BUILDER #
###########

# Pull official base image
FROM python:3.11.4-slim-bookworm AS builder

# Set work directory
WORKDIR /usr/src/app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip and install linting tools
RUN pip install --upgrade pip && \
    pip install flake8==6.0.0

# Copy source code for linting
COPY . /usr/src/app/
RUN flake8 --ignore=E501,F401,W503,F811,E402,F403,F405,F841,E203 .

# Install Python dependencies
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt


#########
# FINAL #
#########

# Pull official base image
FROM python:3.11.4-slim-bookworm

# Add labels for metadata
LABEL maintainer="Sea-Saw Team"
LABEL description="Sea-Saw CRM Production Django Application"

# Create the app user and group
RUN addgroup --system app && \
    adduser --system --group app

# Create directory structure
RUN mkdir -p /home/app/web/staticfiles /home/app/sh

# Set environment variables
ENV HOME=/home/app \
    APP_HOME=/home/app/web \
    SHELL_DIR=/home/app/sh \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR $APP_HOME

# Install runtime dependencies (netcat-openbsd is the modern replacement for netcat in Debian Bookworm)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        netcat-openbsd \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Copy Python wheels and install dependencies
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache /wheels/*

# Copy scripts
COPY ./compose/prod/django/entrypoint.sh $SHELL_DIR/entrypoint.sh
COPY ./compose/prod/django/start.sh $SHELL_DIR/start.sh
COPY ./compose/prod/django/celery/worker/start.sh $SHELL_DIR/start-celeryworker.sh
COPY ./compose/prod/django/celery/beat/start.sh $SHELL_DIR/start-celerybeat.sh
COPY ./compose/prod/django/celery/flower/start.sh $SHELL_DIR/start-flower.sh

# Remove Windows line endings and make scripts executable
RUN sed -i 's/\r$//g' $SHELL_DIR/*.sh && \
    chmod +x $SHELL_DIR/*.sh

# Copy the project files
COPY . $APP_HOME

# Change ownership of the app files to the app user
RUN chown -R app:app $APP_HOME

# Switch to the app user
USER app

# Run entrypoint script
ENTRYPOINT ["/home/app/sh/entrypoint.sh"]
