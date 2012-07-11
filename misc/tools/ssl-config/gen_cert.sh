#!/bin/bash

SSL_DIR=/home/metashare/current/META-SHARE/misc/tools/ssl-config/cert
PRIV_KEY=$SSL_DIR/metashare.key
PRIV_KEY_ORIG=$SSL_DIR/metashare.key.orig
CSR=$SSL_DIR/metashare.csr
CRT=$SSL_DIR/metashare.crt
PEM=$SSL_DIR/metashare.pem
CONF=$SSL_DIR/metashare.conf
PRIV_PASS=metashare

mkdir -p "$SSL_DIR"

cat > "$CONF" << EOF
[ req ]
distinguished_name = req_distinguished_name
prompt = no

[ req_distinguished_name ]
CN=Metashare
ST=Italy
L=Pisa
O=IIT
OU=CNR
C=IT
emailAddress=someone@somewhere.org
EOF

# Generate private key
echo "Generating private key."
openssl genrsa -des3 -passout pass:$PRIV_PASS -out "$PRIV_KEY" 1024

# Generate a CSR (Certificate Signing Request)
echo "Generating Certificate Signing Request"
openssl req -new -config "$CONF" -passin pass:$PRIV_PASS -key "$PRIV_KEY" -out "$CSR"

# Remove passphrase from key.
# Avoids server asking for it when starting.
cp "$PRIV_KEY" "$PRIV_KEY_ORIG"
openssl rsa -passin pass:$PRIV_PASS -in "$PRIV_KEY_ORIG" -out "$PRIV_KEY"

# Generate Self-Signed Certificate
echo "Generating Self-Signed Certificate"
openssl x509 -req -days 365 -in "$CSR" -signkey "$PRIV_KEY" -out "$CRT"

# Prepare Certificate for Lighttpd
cat "$PRIV_KEY" "$CRT" > "$PEM"

