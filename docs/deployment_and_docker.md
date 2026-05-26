# Dockerization & Production Deployment

This phase establishes production-grade containerization and server orchestrations.

---

## 1. Concept & Importance

### Containerization (Docker)
To guarantee that the application runs identically on development machines, staging servers, and production clusters, we containerize the environment.
* **Why it's needed:** Different OS systems might have distinct Python environments, file systems, or missing C++ compiler libraries (e.g. `libgomp1` which FAISS depends on). A Docker container bundles the exact dependencies, OS packages, and code together.
* **Security & Health Checks:** The container includes a `HEALTHCHECK` directive that queries the `/health` endpoint every 30 seconds. Orchestrators (like Docker Compose, Kubernetes, or ECS) use this to monitor container health and automatically restart unhealthy containers.

### Orchestration & Persistence (Docker Compose)
Running a docker container often requires setting environment variables and persistent volumes.
* **Why it's needed:** If the container restarts, any files uploaded or vector indices built will be deleted (containers are ephemeral).
* **Storage Mounts:** We define host-volume mappings (`./data:/code/data`) in `docker-compose.yml` to bind the container's storage folder directly to the host machine. The indices persist even if the container is rebuilt.

---

## 2. File Roles & Descriptions

* [Dockerfile](file:///c:/Users/lenovo/Desktop/RAG_System/Dockerfile): Production multi-step configuration using `python:3.11-slim` base, installing native packages (`libgomp1`), setting up folders, and enabling health checks.
* [docker-compose.yml](file:///c:/Users/lenovo/Desktop/RAG_System/docker-compose.yml): Coordinates build context, maps port 8000, mounts data volumes, and binds configuration variables from `.env`.
* [.dockerignore](file:///c:/Users/lenovo/Desktop/RAG_System/.dockerignore): Dictates which local directories (like `.venv/` or cached database binaries) should be skipped during the image copy.
* [README.md](file:///c:/Users/lenovo/Desktop/RAG_System/README.md): Serves as the master developer guide containing execution scripts, configuration keys, and API descriptions.

---

## 3. Best Practices & Common Mistakes

### Best Practices
1. **Caching Optimization**: Always copy and run `pip install` on the `requirements.txt` *before* copying the application source code. This allows Docker to cache the dependencies layer, accelerating subsequent builds when only source files change.
2. **Explicit User Permissions**: For production environments, run processes as non-root users to limit privilege escalation exploits.
3. **Persisted Volumes**: Never store database indexes (like FAISS files) inside transient container layers. Always mount a host-managed volume.

### Common Mistakes
1. **Missing .dockerignore**: Forgetting to ignore the local `.venv/` folder. Copying local Windows Python binaries into a Linux container causes module load errors and crashes the container.
2. **Fat Base Images**: Using heavy developer base images (like standard `python:3.11` which includes complete compilation toolkits) instead of optimized runtimes (like `python:3.11-slim`), which bloats the image size to over 1GB.

---

## 4. Run the Containerized System

Build and run using Docker Compose:
```bash
docker-compose up --build -d
```
Verify container status:
```bash
docker ps
```
Inspect logs to ensure everything booted:
```bash
docker logs -f rag_assistant_api
```
Access the Swagger documentation at: `http://localhost:8000/docs`
