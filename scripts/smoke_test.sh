#!/usr/bin/env bash
# Smoke test for the running stack. Requires only bash and curl.
# Reusable from GitHub Actions, Jenkins, Travis CI, etc.
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:${API_PORT:-8000}}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-30}"
SLEEP_SECONDS="${SLEEP_SECONDS:-2}"

# Body of the last health response (set by wait_for_health). No temp files:
# keeps the script portable to Git Bash on Windows, where native curl.exe
# does not understand MSYS paths such as /tmp.
HEALTH_BODY=""

log() {
  echo "[smoke] $*"
}

fail() {
  echo "[smoke] FAIL: $*" >&2
  exit 1
}

wait_for_health() {
  local attempt response status
  for ((attempt = 1; attempt <= MAX_ATTEMPTS; attempt++)); do
    response="$(curl -s --connect-timeout 3 --max-time 10 -w '
%{http_code}' "$BASE_URL/health" || true)"
    status="${response##*$'
'}"
    HEALTH_BODY="${response%$'
'*}"
    if [[ "$status" == "200" ]]; then
      log "Health endpoint answered 200 (attempt $attempt)"
      return 0
    fi
    log "Waiting for $BASE_URL/health (attempt $attempt/$MAX_ATTEMPTS, status: ${status:-none})"
    sleep "$SLEEP_SECONDS"
  done
  fail "Health endpoint did not return 200 after $MAX_ATTEMPTS attempts (last status: ${status:-none}, last body: ${HEALTH_BODY:-<empty>})"
}

assert_health_body() {
  local expected='{"status":"ok","database":"ok"}'
  local actual
  actual="$(tr -d '[:space:]' <<< "$HEALTH_BODY")"
  if ! grep -qxF -- "$expected" <<< "$actual"; then
    fail "Unexpected health body: $actual (expected $expected)"
  fi
  log "Health body OK: $actual"
}

wait_for_health
assert_health_body

# Round-trip checks (categories/expenses) are added in later features.

echo "Smoke test passed"
