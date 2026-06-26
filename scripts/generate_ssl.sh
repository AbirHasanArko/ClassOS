#!/bin/bash

# Define paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
SSL_DIR="$ROOT_DIR/nginx/ssl"

# Create SSL directory if it doesn't exist
mkdir -p "$SSL_DIR"

echo "Generating self-signed SSL certificates in $SSL_DIR..."

# Generate the certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$SSL_DIR/key.pem" \
  -out "$SSL_DIR/cert.pem" \
  -subj "/C=US/ST=State/L=City/O=ClassOS/OU=IT/CN=classos.local"

echo "Certificates generated successfully:"
echo "- $SSL_DIR/cert.pem"
echo "- $SSL_DIR/key.pem"
