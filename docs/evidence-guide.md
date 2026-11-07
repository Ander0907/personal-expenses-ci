# Evidence guide

Ordered capture script for the evidence PDF of deliverable 1 ("Docker with two communicating containers"). Each item lists the rubric criterion it supports, the commands to run (bash; use Git Bash on Windows) and what must be visible in the screenshot.

Rubric: repository (15), API container (20), PostgreSQL container (15), Docker Compose (20), communication (35), good practices and security (15), CI (15), evidence PDF (15).

## Before you start

Run from the repository root:

```bash
cp .env.example .env        # skip if .env already exists
docker compose down -v      # clean state: no containers, no volume
```

Tip: use a terminal wide enough that long lines do not wrap, and include the command in every capture.

## 1. Repository structure and commit history (Repository, 15)

- Open <https://github.com/Ander0907/personal-expenses-ci> and capture the file tree: `api/`, `scripts/`, `docs/`, `.github/`, `docker-compose.yml`, `.env.example`, `README.md`. There must be no `.env` file.
- Capture the commit history (Commits page) showing clear, Conventional Commit messages.
- Capture the README with the "Quick start" section visible.

## 2. Build the API image (API container, 20)

```bash
docker compose build api
```

Visible: the build stages (builder and runtime, base image `python:3.12.16-slim-bookworm`) finishing without errors.

## 3. Image list (API container, 20)

```bash
docker image ls personal-expenses-api
```

Visible: the image `personal-expenses-api:local` and its size.

## 4. Dockerfile (API container, 20)

```bash
cat api/Dockerfile
```

Visible: pinned `FROM python:3.12.16-slim-bookworm` (no `latest`), dependency installation, `USER app`, `EXPOSE 8000` and the `CMD` (`alembic upgrade head && exec uvicorn ...`). Capture in two parts if it does not fit one screen.

## 5. Start the stack (Docker Compose, 20; PostgreSQL container, 15)

```bash
docker compose up -d
docker compose ps
```

Visible: services `db` and `api` both running with status `healthy` (re-run `docker compose ps` after about 30 seconds if still `starting`), and the port mapping `127.0.0.1:8000->8000/tcp` for `api` only.

## 6. Compose file (Docker Compose, 20; PostgreSQL container, 15)

```bash
cat docker-compose.yml
```

Visible: services `api` and `db`, pinned image `postgres:17.11-bookworm`, `POSTGRES_*` variables, volume `expenses-db-data`, network `expenses-net`, `depends_on` with `condition: service_healthy`, healthchecks, and no `ports` on `db`.

## 7. Network (Docker Compose, 20; communication, 35)

```bash
docker network inspect expenses-net
```

Visible: the `Containers` section lists both the `api` and `db` containers attached to `expenses-net`.

## 8. Volume (PostgreSQL container, 15)

```bash
docker volume ls
docker volume inspect expenses-db-data
```

Visible: volume `expenses-db-data` in the list and its inspect output (driver `local`, mountpoint).

## 9. Service-name resolution (communication, 35)

```bash
docker compose exec api getent hosts db
docker compose exec api env | grep DATABASE_HOST
```

Visible: `db` resolving to an IP address on the Docker network, and `DATABASE_HOST=db` (not `localhost` or an IP). The password must not appear.

## 10. Health check through the database (communication, 35)

```bash
curl -i http://localhost:8000/health
docker compose logs api | head -n 6
```

Visible: `HTTP/1.1 200 OK` and body `{"status":"ok","database":"ok"}`; in the logs, `Running upgrade  -> 0001` (Alembic created the tables in `db` through the service name) before `Application startup complete`.

## 11. Write and read round trip through the API (communication, 35)

```bash
curl -i -X POST http://localhost:8000/categories \
  -H 'Content-Type: application/json' \
  -d '{"name": "Food", "monthly_budget": "150.00"}'

curl -i -X POST http://localhost:8000/expenses \
  -H 'Content-Type: application/json' \
  -d "{\"category_id\": 1, \"amount\": \"20.00\", \"description\": \"Lunch\", \"spent_at\": \"$(date -u +%Y-%m-%d)\"}"

curl -i "http://localhost:8000/expenses?category_id=1"

curl -i "http://localhost:8000/reports/monthly?year=$(date -u +%Y)&month=$((10#$(date -u +%m)))"
```

Capture each response (or one capture per pair). Visible: `201` with the created category, `201` with the created expense and `"over_budget":false`, `200` listing the same expense read back from PostgreSQL, and `200` with the report (`total_spent` `"20.00"`, `percent_used` `"13.33"`). The category `id` is 1 only on a fresh database; use the returned `id` otherwise.

## 12. Read the data from inside the database container (communication, 35)

```bash
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT id, name, monthly_budget FROM categories;"'
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT id, category_id, amount, description, spent_at FROM expenses;"'
```

The outer single quotes make the variables expand inside the `db` container, where they are defined. Visible: the rows created through the API. This proves the data really lives in PostgreSQL, accessed with the custom role from `.env` instead of the default `postgres` role.

## 13. Data persistence (PostgreSQL container, 15)

```bash
docker compose down
docker compose up -d --wait
curl http://localhost:8000/categories
```

Visible: after the restart the category created in step 11 is still returned (the volume survived).

Then show the reset:

```bash
docker compose down -v
docker compose up -d --wait
curl http://localhost:8000/categories
```

Visible: an empty list `[]` (the volume was deleted).

## 14. Database not published (good practices and security, 15)

```bash
docker compose port db 5432
docker compose ps
```

Visible: `docker compose port db 5432` prints `:0` (no host port is bound), and the `db` row in `docker compose ps` shows only `5432/tcp` with no `127.0.0.1:...->` mapping, unlike `api`.

## 15. Secrets handling (good practices and security, 15)

```bash
git check-ignore -v .env
cat .env.example
git ls-files | grep -E '^\.env'
```

Visible: the `.gitignore` rule that ignores `.env`; `.env.example` with fake values; `git ls-files` listing only `.env.example`.

## 16. .dockerignore (good practices and security, 15)

```bash
cat api/.dockerignore
```

Visible: `.env`, `.env.*`, `.venv`, `tests` and caches excluded.

## 17. Non-root container (good practices and security, 15)

```bash
docker compose exec api id
```

Visible: `uid=10001(app) gid=10001(app)`.

## 18. GitHub Actions run (CI, 15)

On <https://github.com/Ander0907/personal-expenses-ci/actions>:

- Capture the workflow runs list with green checks.
- Open one run and capture the summary showing both jobs green: "Lint & unit tests" and "Build image & smoke test".
- Open the "Build image & smoke test" job and capture the expanded "Smoke test" step log (lines starting with `[smoke]`, ending with `Smoke test passed`).
- Capture a run triggered by a `pull_request` event (the event name is shown in the run header) and the green check on the pull request page.
- Capture the "Lint & unit tests" job with the `ruff` and `pytest` steps and the coverage table.

## 19. Architecture diagram (evidence PDF, 15)

Open the repository README on GitHub and capture the rendered Mermaid diagrams (architecture flowchart and data model).

## Cleanup

```bash
docker compose down -v                         # remove containers, network and the database volume
docker image rm personal-expenses-api:local    # optional: remove the built image
```
