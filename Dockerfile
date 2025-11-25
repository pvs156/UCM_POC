# ---------- Stage 1: Build the React frontend ----------
FROM node:20-alpine AS frontend-builder
WORKDIR /src/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build   # creates ./dist

# ---------- Stage 2: Install Python dependencies ----------
FROM python:3.11-slim AS backend-builder
WORKDIR /src
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Stage 3: Final runtime image ----------
FROM python:3.11-slim
WORKDIR /app

# copy backend source
COPY backend/ ./backend

# copy built static files
COPY --from=frontend-builder /src/frontend/dist ./frontend/dist

# copy installed Python packages (includes uvicorn)
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# expose the port Railway/Azure will assign
ENV PORT=8000
EXPOSE 8000

# start FastAPI
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "$PORT"]
