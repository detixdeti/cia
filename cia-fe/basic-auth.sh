#!/bin/sh
# Turns on password protection when BASIC_AUTH_PASSWORD is set (e.g. on Render).
# Locally the variable is empty and the app stays open.
set -e

if [ -n "$BASIC_AUTH_PASSWORD" ]; then
    printf '%s:%s\n' "${BASIC_AUTH_USER:-studie}" "$(openssl passwd -apr1 "$BASIC_AUTH_PASSWORD")" > /etc/nginx/htpasswd
    printf 'auth_basic "CIA-Prototyp";\nauth_basic_user_file /etc/nginx/htpasswd;\n' > /etc/nginx/basic-auth.conf
    echo "basic-auth.sh: password protection on"
else
    : > /etc/nginx/basic-auth.conf
    echo "basic-auth.sh: no password set, password protection off"
fi
