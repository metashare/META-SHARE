#!/bin/sh

SERVER=http://localhost:8000/metashare
USER=syncuser
PASSWORD=secret

# Obtain the CSRF token:
data=$(curl -s -c cookies.txt $SERVER/login/ | grep -o "name=['\"]csrfmiddlewaretoken['\"] value=['\"][^'\"]*" | sed -e "s/name='//" -e "s/' value='/=/")\&username=$USER\&password=$PASSWORD

# Log in:
curl -b cookies.txt -c cookies.txt -d $data -X POST -H 'Content-Type: application/x-www-form-urlencoded' $SERVER/login/

# Get inventory:
curl -b cookies.txt $SERVER/sync/ -o inventory.zip && echo "Inventory saved to inventory.zip"
