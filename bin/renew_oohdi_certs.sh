#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CERT_DIR="${APP_DIR}/nginx/certs"
LOG_FILE="${APP_DIR}/logs/cert-renew.log"
mkdir -p "${CERT_DIR}" "$(dirname "${LOG_FILE}")"

DOMAINS=(
  oohdi.org
  www.oohdi.org
  example-media-owner.oohdi.org
  example-registry.oohdi.org
)

DOMAIN_LIST="$(printf '%s ' "${DOMAINS[@]}")"
DOMAIN_LIST="${DOMAIN_LIST% }"

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Starting certificate renewal check" >> "${LOG_FILE}"

if ! command -v certbot >/dev/null 2>&1; then
  echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] certbot not installed; skipping renewal" >> "${LOG_FILE}"
  exit 0
fi

if [ -f "${CERT_DIR}/oohdi.crt" ] && [ -f "${CERT_DIR}/oohdi.key" ]; then
  if openssl x509 -in "${CERT_DIR}/oohdi.crt" -noout -checkend 604800 >/dev/null 2>&1; then
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Existing certificate still valid for more than 7 days; nothing to do" >> "${LOG_FILE}"
    exit 0
  fi
fi

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Requesting certificate for: ${DOMAIN_LIST}" >> "${LOG_FILE}"

certbot certonly \
  --standalone \
  --non-interactive \
  --agree-tos \
  --email admin@oohdi.org \
  --domains "${DOMAIN_LIST}" \
  --deploy-hook "cp /etc/letsencrypt/live/oohdi.org/fullchain.pem ${CERT_DIR}/oohdi.crt; cp /etc/letsencrypt/live/oohdi.org/privkey.pem ${CERT_DIR}/oohdi.key; docker compose -f ${APP_DIR}/docker-compose.yml restart nginx" \
  --keep-until-expiring

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Certificate renewal check completed" >> "${LOG_FILE}"
