# Guía de evidencias

Guion ordenado de capturas para el PDF de evidencias de la entrega 1 ("Docker con dos contenedores comunicados"). Cada punto indica el criterio de la rúbrica que respalda, los comandos a ejecutar (bash; en Windows usar Git Bash) y lo que debe verse en la captura.

Rúbrica: repositorio (15), contenedor de la API (20), contenedor de PostgreSQL (15), Docker Compose (20), comunicación (35), buenas prácticas y seguridad (15), CI (15), PDF de evidencias (15).

## Antes de empezar

Ejecutar desde la raíz del repositorio:

```bash
cp .env.example .env        # omitir si .env ya existe
docker compose down -v      # estado limpio: sin contenedores ni volumen
```

Consejo: usar una terminal lo bastante ancha para que las líneas largas no se corten, e incluir el comando en cada captura.

## 1. Estructura del repositorio e historial de commits (Repositorio, 15)

- Abrir <https://github.com/Ander0907/personal-expenses-ci> y capturar el árbol de archivos: `api/`, `scripts/`, `docs/`, `.github/`, `docker-compose.yml`, `.env.example`, `README.md`. No debe existir ningún archivo `.env`.
- Capturar el historial de commits (página Commits) con mensajes claros en formato Conventional Commits.
- Capturar el README con la sección "Inicio rápido" visible.

## 2. Construir la imagen de la API (Contenedor de la API, 20)

```bash
docker compose build api
```

Visible: las etapas del build (builder y runtime, imagen base `python:3.12.16-slim-bookworm`) terminando sin errores.

## 3. Lista de imágenes (Contenedor de la API, 20)

```bash
docker image ls personal-expenses-api
```

Visible: la imagen `personal-expenses-api:local` y su tamaño.

## 4. Dockerfile (Contenedor de la API, 20)

```bash
cat api/Dockerfile
```

Visible: `FROM python:3.12.16-slim-bookworm` con versión fija (sin `latest`), la instalación de dependencias, `USER app`, `EXPOSE 8000` y el `CMD` (`alembic upgrade head && exec uvicorn ...`). Capturar en dos partes si no cabe en una pantalla.

## 5. Levantar el stack (Docker Compose, 20; Contenedor de PostgreSQL, 15)

```bash
docker compose up -d
docker compose ps
```

Visible: los servicios `db` y `api` en ejecución con estado `healthy` (volver a ejecutar `docker compose ps` tras unos 30 segundos si aún aparece `starting`), y el mapeo de puertos `127.0.0.1:8000->8000/tcp` solo para `api`.

## 6. Archivo de Compose (Docker Compose, 20; Contenedor de PostgreSQL, 15)

```bash
cat docker-compose.yml
```

Visible: los servicios `api` y `db`, la imagen fija `postgres:17.11-bookworm`, las variables `POSTGRES_*`, el volumen `expenses-db-data`, la red `expenses-net`, `depends_on` con `condition: service_healthy`, los healthchecks y la ausencia de `ports` en `db`.

## 7. Red (Docker Compose, 20; Comunicación, 35)

```bash
docker network inspect expenses-net
```

Visible: la sección `Containers` lista los contenedores `api` y `db` conectados a `expenses-net`.

## 8. Volumen (Contenedor de PostgreSQL, 15)

```bash
docker volume ls
docker volume inspect expenses-db-data
```

Visible: el volumen `expenses-db-data` en la lista y la salida de inspect (driver `local`, mountpoint).

## 9. Resolución por nombre de servicio (Comunicación, 35)

```bash
docker compose exec api getent hosts db
docker compose exec api env | grep DATABASE_HOST
```

Visible: `db` resolviendo a una dirección IP de la red de Docker, y `DATABASE_HOST=db` (no `localhost` ni una IP). La contraseña no debe aparecer.

## 10. Health check a través de la base de datos (Comunicación, 35)

```bash
curl -i http://localhost:8000/health
docker compose logs api | head -n 6
```

Visible: `HTTP/1.1 200 OK` y el cuerpo `{"status":"ok","database":"ok"}`; en los logs, `Running upgrade  -> 0001` (Alembic creó las tablas en `db` usando el nombre del servicio) antes de `Application startup complete`.

## 11. Ida y vuelta de escritura y lectura a través de la API (Comunicación, 35)

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

Capturar cada respuesta (o una captura por cada par). Visible: `201` con la categoría creada, `201` con el gasto creado y `"over_budget":false`, `200` listando el mismo gasto leído de vuelta desde PostgreSQL, y `200` con el reporte (`total_spent` `"20.00"`, `percent_used` `"13.33"`). El `id` de la categoría es 1 solo con una base de datos recién creada; en otro caso, usar el `id` devuelto.

## 12. Leer los datos desde dentro del contenedor de la base de datos (Comunicación, 35)

```bash
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT id, name, monthly_budget FROM categories;"'
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT id, category_id, amount, description, spent_at FROM expenses;"'
```

Las comillas simples externas hacen que las variables se expandan dentro del contenedor `db`, donde están definidas. Visible: las filas creadas a través de la API. Esto demuestra que los datos realmente viven en PostgreSQL, accedidos con el rol propio definido en `.env` en lugar del rol por defecto `postgres`.

## 13. Persistencia de datos (Contenedor de PostgreSQL, 15)

```bash
docker compose down
docker compose up -d --wait
curl http://localhost:8000/categories
```

Visible: tras el reinicio, la categoría creada en el paso 11 sigue apareciendo (el volumen sobrevivió).

Luego mostrar el reinicio desde cero:

```bash
docker compose down -v
docker compose up -d --wait
curl http://localhost:8000/categories
```

Visible: una lista vacía `[]` (el volumen fue eliminado).

## 14. Base de datos no publicada (Buenas prácticas y seguridad, 15)

```bash
docker compose port db 5432
docker compose ps
```

Visible: `docker compose port db 5432` imprime `:0` (no hay puerto del host asociado), y la fila de `db` en `docker compose ps` muestra solo `5432/tcp`, sin mapeo `127.0.0.1:...->`, a diferencia de `api`.

## 15. Manejo de secretos (Buenas prácticas y seguridad, 15)

```bash
git check-ignore -v .env
cat .env.example
git ls-files | grep -E '^\.env'
```

Visible: la regla de `.gitignore` que ignora `.env`; `.env.example` con valores falsos; `git ls-files` listando solo `.env.example`.

## 16. .dockerignore (Buenas prácticas y seguridad, 15)

```bash
cat api/.dockerignore
```

Visible: `.env`, `.env.*`, `.venv`, `tests` y las cachés excluidos.

## 17. Contenedor sin root (Buenas prácticas y seguridad, 15)

```bash
docker compose exec api id
```

Visible: `uid=10001(app) gid=10001(app)`.

## 18. Ejecución de GitHub Actions (CI, 15)

En <https://github.com/Ander0907/personal-expenses-ci/actions>:

- Capturar la lista de ejecuciones del workflow con checks en verde.
- Abrir una ejecución y capturar el resumen con ambos jobs en verde: "Lint & unit tests" y "Build image & smoke test".
- Abrir el job "Build image & smoke test" y capturar el log expandido del paso "Smoke test" (líneas que empiezan con `[smoke]` y terminan con `Smoke test passed`).
- Capturar una ejecución disparada por un evento `pull_request` (el nombre del evento aparece en el encabezado de la ejecución) y el check verde en la página del pull request.
- Capturar el job "Lint & unit tests" con los pasos de `ruff` y `pytest` y la tabla de cobertura.

## 19. Diagrama de arquitectura (PDF de evidencias, 15)

Abrir el README del repositorio en GitHub y capturar los diagramas Mermaid renderizados (diagrama de arquitectura y modelo de datos).

## Limpieza

```bash
docker compose down -v                         # elimina contenedores, red y el volumen de la base de datos
docker image rm personal-expenses-api:local    # opcional: elimina la imagen construida
```
