#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CERT_DIR="${APP_DIR}/nginx/certs"
LOG_FILE="${APP_DIR}/logs/cert-renew.log"
COMPOSE_FILE="${APP_DIR}/docker-compose.yml"
mkdir -p "${CERT_DIR}" "$(dirname "${LOG_FILE}")"

DOMAINS=(
  oohdi.org
  www.oohdi.org
  example-media-owner.oohdi.org
  example-registry.oohdi.org
)

CERTBOT_EMAIL="${CERTBOT_EMAIL:-admin@oohdi.org}"

if [ ! -f "${COMPOSE_FILE}" ]; then
  echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Missing docker-compose.yml at ${COMPOSE_FILE}; aborting" >> "${LOG_FILE}"
  exit 1
fi

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

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Requesting certificate for: ${DOMAINS[*]}" >> "${LOG_FILE}"

if command -v docker >/dev/null 2>&1; then
  docker compose -f "${COMPOSE_FILE}" stop nginx >/dev/null 2>&1 || true
fi

CERTBOT_ARGS=(
  certonly
  --non-interactive
  --agree-tos
  --email "${CERTBOT_EMAIL}"
  --keep-until-expiring
  --standalone
)

for domain in "${DOMAINS[@]}"; do
  CERTBOT_ARGS+=( -d "${domain}" )
done

CERTBOT_ARGS+=(
  --deploy-hook "cp /etc/letsencrypt/live/oohdi.org/fullchain.pem ${CERT_DIR}/oohdi.crt; cp /etc/letsencrypt/live/oohdi.org/privkey.pem ${CERT_DIR}/oohdi.key"
)

certbot "${CERTBOT_ARGS[@]}"

if command -v docker >/dev/null 2>&1; then
  docker compose -f "${COMPOSE_FILE}" up -d nginx >/dev/null 2>&1 || true
fi

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Certificate renewal check completed" >> "${LOG_FILE}"
