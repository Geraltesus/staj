#!/bin/sh
set -eu

OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.2:1b}"

# The official ollama image does not always include curl/wget, so readiness is
# checked through the ollama CLI itself. OLLAMA_HOST is provided by compose.
echo "Waiting for Ollama API at ${OLLAMA_HOST:-http://ollama:11434}..."
until ollama list >/dev/null 2>&1; do
  sleep 2
done

if ollama list | awk '{print $1}' | grep -qx "${OLLAMA_MODEL}"; then
  echo "Model ${OLLAMA_MODEL} already exists."
else
  echo "Pulling model ${OLLAMA_MODEL}..."
  ollama pull "${OLLAMA_MODEL}"
fi

echo "Ollama model initialization completed."