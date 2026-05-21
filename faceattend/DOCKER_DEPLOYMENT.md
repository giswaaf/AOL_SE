# Docker Deployment Guide

This guide explains how to deploy the Smart Attendance System using Docker Compose for both development and production environments.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed
- [Docker Compose](https://docs.docker.com/compose/install/) installed
- Make (optional, for using the Makefile commands)

## Project Structure

The project services are defined in `docker-compose.yml`:

- **mongodb**: MongoDB database service (Port 27017)
- **backend-api**: FastAPI backend service (Port 8000)
- **ml-service**: Machine Learning service for face recognition (Port 8001)
- **frontend**: React frontend application (Port 5173 for Dev, 80 for Prod)

## Configuration

Before starting the services, ensure you have the necessary environment variables set up.

1. **Backend API**: Check `server/backend-api/.env` 
2. **ML Service**: Check `server/ml-service/.env`
3. **Frontend**: Check `frontend/.env`

Ensure your `.env` files contain the correct credentials for services like Cloudinary, Google OAuth, and Email (SMTP).

In `docker-compose.yml`, the backend API service expects the following variables to be available in your shell or `.env` file when running docker-compose:
- `JWT_SECRET`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

You can also rely on the `env_file` directive in `docker-compose.yml` which loads from `./server/backend-api/.env`.

## Development Environment

To start the application in development mode with hot-reloading:

### Using Makefile
```bash
make dev
```

### Using Docker Compose
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

This will run:
- Frontend at http://localhost:5173
- Backend API at http://localhost:8000
- ML Service at http://localhost:8001
- MongoDB at localhost:27017

## Production Deployment

To start the application in production mode:

### Using Makefile
```bash
make prod
```

### Using Docker Compose
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

In production:
- The frontend is served via Nginx.
- The backend runs with Gunicorn workers.
- Services are configured to restart automatically.

## Common Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start development environment |
| `make prod` | Start production environment |
| `make stop` | Stop all running containers |
| `make clean` | Stop containers and remove volumes (database data will be lost) |
| `make logs` | View logs from all services |
| `make build` | Rebuild Docker images |

## Troubleshooting

### Database Connection Issues
If the backend fails to connect to MongoDB, check the logs:
```bash
docker-compose logs backend-api
```
Ensure the `mongodb` service is healthy.

### Hot Reload Not Working
If changes in code are not reflecting:
- Ensure you are running in dev mode.
- Check volume mounts in `docker-compose.dev.yml`.
- On Windows/Mac, ensure file sharing is enabled for the project directory.

### ML Service Health Check Fails
The ML service requires significant resources. If it fails to start:
- Check if you have allocated enough memory to Docker.
- Check logs: `docker-compose logs ml-service`.
