#!/usr/bin/env bash
# Smoke test for the running stack. Requires only bash and curl.
# Reusable from GitHub Actions, Jenkins, Travis CI, etc.
#
# Proves API <-> database communication with a real round trip:
#   1. GET  /health      -> the API reaches PostgreSQL (SELECT 1)
#   2. POST /categories  -> a row is written to PostgreSQL
#   3. GET  /categories  -> the same row is read back from PostgreSQL
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:${API_PORT:-8000}}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-30}"
SLEEP_SECONDS="${SLEEP_SECONDS:-2}"

# Unique per run, so the script can be re-run against the same database
# without hitting the duplicate-name rule (409).
RUN_ID="$(date +%s)-$$"

# Status and body of the last request (set by http_request). No temp files:
# keeps the script portable to Git Bash on Windows, where native curl.exe
# does not understand MSYS paths such as /tmp.
RESPONSE_STATUS=""
RESPONSE_BODY=""

log() {
  echo "[smoke] $*"
}

fail() {
  echo "[smoke] FAIL: $*" >&2
  exit 1
}

# http_request METHOD PATH [JSON_BODY]
http_request() {
  local method="$1" path="$2" body="${3:-}" response
  local -a args=(-s --connect-timeout 3 --max-time 10 -X "$method" -w $'\n%{http_code}')
  if [[ -n "$body" ]]; then
    args+=(-H "Content-Type: application/json" --data "$body")
  fi
  response="$(curl "${args[@]}" "$BASE_URL$path" || true)"
  RESPONSE_STATUS="${response##*$'\n'}"
  RESPONSE_BODY="${response%$'\n'*}"
}

# expect_status EXPECTED CONTEXT
expect_status() {
  if [[ "$RESPONSE_STATUS" != "$1" ]]; then
    fail "$2: expected HTTP $1, got ${RESPONSE_STATUS:-none} (body: ${RESPONSE_BODY:-<empty>})"
  fi
}

# expect_body_contains FRAGMENT CONTEXT
expect_body_contains() {
  if [[ "$RESPONSE_BODY" != *"$1"* ]]; then
    fail "$2: response does not contain $1 (body: ${RESPONSE_BODY:-<empty>})"
  fi
}

wait_for_health() {
  local attempt
  for ((attempt = 1; attempt <= MAX_ATTEMPTS; attempt++)); do
    http_request GET /health
    if [[ "$RESPONSE_STATUS" == "200" ]]; then
      log "Health endpoint answered 200 (attempt $attempt)"
      return 0
    fi
    log "Waiting for $BASE_URL/health (attempt $attempt/$MAX_ATTEMPTS, status: ${RESPONSE_STATUS:-none})"
    sleep "$SLEEP_SECONDS"
  done
  fail "Health endpoint did not return 200 after $MAX_ATTEMPTS attempts (last status: ${RESPONSE_STATUS:-none}, last body: ${RESPONSE_BODY:-<empty>})"
}

check_health_body() {
  local expected='{"status":"ok","database":"ok"}'
  local actual
  actual="$(tr -d '[:space:]' <<< "$RESPONSE_BODY")"
  if [[ "$actual" != "$expected" ]]; then
    fail "Unexpected health body: $actual (expected $expected)"
  fi
  log "Health body OK: $actual"
}

check_category_round_trip() {
  local name="Smoke ${RUN_ID}"

  http_request POST /categories "{\"name\": \"${name}\", \"monthly_budget\": \"150.00\"}"
  expect_status 201 "Create category"
  expect_body_contains "\"name\":\"${name}\"" "Create category"
  log "Created category: $RESPONSE_BODY"

  http_request POST /categories "{\"name\": \"${name^^}\", \"monthly_budget\": \"10.00\"}"
  expect_status 409 "Duplicate category (case-insensitive)"
  log "Duplicate name rejected with 409: $RESPONSE_BODY"

  # Assumes fewer than 500 categories (always true in CI, which starts from
  # an empty volume). Run "docker compose down -v" locally to reset.
  http_request GET "/categories?limit=500"
  expect_status 200 "List categories"
  expect_body_contains "\"name\":\"${name}\"" "List categories"
  log "Category read back from the database"
}

wait_for_health
check_health_body
check_category_round_trip

# Expense round-trip checks are added in the expenses feature.

echo "Smoke test passed"
