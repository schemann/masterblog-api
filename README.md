# Masterblog API

A JSON API for blog posts built with Flask (Masterschool exercise), plus a small JavaScript
frontend that talks to it. Posts are stored in `backend/posts.json`.

## Run

```
pip3 install -r requirements.txt
python3 backend/backend_app.py     # API on http://localhost:5002
python3 frontend/frontend_app.py   # frontend on http://localhost:5001
```

Open the frontend and enter the API base URL (for example `http://127.0.0.1:5002/api`).
API documentation (Swagger UI): http://localhost:5002/api/docs

## Endpoints

All endpoints are available under `/api` and, versioned, under `/api/v1`.

| Method | Path | What it does |
|---|---|---|
| GET | `/api/posts` | All posts; optional `sort` (title, content, author, date, likes), `direction` (asc, desc), `page`, `limit` |
| POST | `/api/posts` | Adds a post; `title` and `content` required, `author` (default Anonymous) and `date` (YYYY-MM-DD, default today) optional |
| PUT | `/api/posts/<id>` | Updates title, content, author and/or date; fields left out keep their value |
| DELETE | `/api/posts/<id>` | Deletes a post |
| POST | `/api/posts/<id>/like` | Adds one like |
| GET | `/api/posts/search` | Posts where `title`, `content`, `author` or `date` contain the given term; `page` and `limit` work here too |

Errors come back as JSON with a matching status code (400, 404, 405, 429, 500).
Each client may send 100 requests per minute; paginated answers carry the total number of
matching posts in the `X-Total-Count` header.
