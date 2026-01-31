#!/bin/bash
# Generate secure secrets for Sea-Saw CRM deployment
# Usage: ./scripts/generate_secrets.sh

set -e

echo "=========================================="
echo "Sea-Saw CRM Security Secrets Generator"
echo "=========================================="
echo ""

# Check if Python is available
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "Error: Python is not installed. Please install Python first."
    exit 1
fi

PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "Generating Django SECRET_KEY..."
echo "----------------------------------------"
SECRET_KEY=$($PYTHON_CMD -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
echo "SECRET_KEY=$SECRET_KEY"
echo ""

echo "Generating PostgreSQL password..."
echo "----------------------------------------"
if command -v openssl &> /dev/null; then
    DB_PASSWORD=$(openssl rand -base64 32)
    echo "SQL_PASSWORD=$DB_PASSWORD"
    echo "POSTGRES_PASSWORD=$DB_PASSWORD  # Use this in .env/.prod.db"
else
    echo "Warning: openssl not found. Using Python random generation."
    DB_PASSWORD=$($PYTHON_CMD -c 'import secrets; print(secrets.token_urlsafe(32))')
    echo "SQL_PASSWORD=$DB_PASSWORD"
    echo "POSTGRES_PASSWORD=$DB_PASSWORD  # Use this in .env/.prod.db"
fi
echo ""

echo "=========================================="
echo "IMPORTANT: Save these secrets securely!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Copy the SECRET_KEY to your .env/.prod file"
echo "2. Copy the SQL_PASSWORD to your .env/.prod file"
echo "3. Copy the POSTGRES_PASSWORD to your .env/.prod.db file"
echo "4. NEVER commit these secrets to version control"
echo "5. Store them in a secure password manager"
echo ""
echo "Example .env/.prod configuration:"
echo "----------------------------------------"
echo "SECRET_KEY=$SECRET_KEY"
echo "SQL_USER=sea_saw_prod_user"
echo "SQL_PASSWORD=$DB_PASSWORD"
echo ""
echo "Example .env/.prod.db configuration:"
echo "----------------------------------------"
echo "POSTGRES_DB=sea_saw_prod"
echo "POSTGRES_USER=sea_saw_prod_user"
echo "POSTGRES_PASSWORD=$DB_PASSWORD"
echo ""
echo "=========================================="
echo "Security reminders:"
echo "- Rotate these secrets every 90 days"
echo "- Use different secrets for development/production"
echo "- Never reuse secrets across projects"
echo "=========================================="
