#!/bin/sh
set -eu

OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://ollama:11434}"
SESSIONS_DIR="${SESSIONS_DIR:-/app/app/storage/sessions}"

echo "Waiting for Ollama at ${OLLAMA_BASE_URL}..."
until curl -fsS "${OLLAMA_BASE_URL}/api/tags" >/dev/null 2>&1; do
  sleep 2
done

mkdir -p "${SESSIONS_DIR}"

echo "Ollama is ready. Starting Interview Mentor API..."
exec "$@"