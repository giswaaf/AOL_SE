# Smart Attendance System - Microservices Architecture

This directory contains the separated microservices architecture for the Smart Attendance System.

> **✅ Separation Verified**: See [SEPARATION_VERIFICATION.md](./SEPARATION_VERIFICATION.md) for complete verification details and running instructions.

## Architecture

The system is split into two independent services:

1. **Backend API** - Handles business logic, authentication, and database operations
2. **ML Service** - Handles face recognition and machine learning operations

```
Frontend → Backend API → ML Service
              ↓
           MongoDB
              ↓
          Cloudinary
```

## Services

### [Backend API](./backend-api/)
- Port: 8000
- User authentication & authorization
- Student/Teacher management
- Attendance record management
- Subject/Class management
- Email notifications
- Orchestrates ML service calls

**Tech Stack:** FastAPI, MongoDB, JWT, Cloudinary, httpx

### [ML Service](./ml-service/)
- Port: 8001
- Face detection
- Face encoding/embedding generation
- Face matching and recognition
- Stateless ML operations

**Tech Stack:** FastAPI, face_recognition, OpenCV, NumPy

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services will be available at:
- Backend API: http://localhost:8000
- ML Service: http://localhost:8001
- MongoDB: localhost:27017

### Manual Setup

**1. Start MongoDB**
```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or install locally
# macOS: brew install mongodb-community
# Ubuntu: sudo apt-get install mongodb
```

**2. Start ML Service**
```bash
cd ml-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.main
```

**3. Start Backend API**
```bash
cd backend-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
python -m app.main
```

## Configuration

### Backend API

Create `backend-api/.env`:

```env
# Database
MONGO_URI=mongodb://localhost:27017/smart_attendance

# JWT
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256

# ML Service
ML_SERVICE_URL=http://localhost:8001
ML_SERVICE_TIMEOUT=30
ML_SERVICE_MAX_RETRIES=3

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
```

### ML Service

Create `ml-service/.env`:

```env
HOST=0.0.0.0
PORT=8001
LOG_LEVEL=info
ML_MODEL=hog
```

## API Documentation

Once running, visit:

- Backend API Docs: http://localhost:8000/docs
- ML Service Docs: http://localhost:8001/docs

## Testing

### Health Checks

```bash
# Backend API
curl http://localhost:8000/

# ML Service
curl http://localhost:8001/health
```

### Integration Test

```bash
# Mark attendance (requires auth token)
curl -X POST http://localhost:8000/api/attendance/mark \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,/9j/4AAQ...",
    "subject_id": "507f1f77bcf86cd799439011"
  }'
```

## Deployment

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for detailed deployment instructions including:

- Local development setup
- Docker deployment
- Cloud deployment (AWS, GCP, Azure)
- Serverless deployment
- Load balancing configuration
- Monitoring and logging

## Scaling

### Horizontal Scaling

```bash
# Scale ML service to 3 instances
docker-compose up -d --scale ml-service=3

# Scale backend to 2 instances
docker-compose up -d --scale backend-api=2
```

For production, use a load balancer (Nginx, HAProxy, or cloud load balancer).

### Vertical Scaling

Adjust resources in `docker-compose.yml`:

```yaml
ml-service:
  deploy:
    resources:
      limits:
        cpus: '4.0'
        memory: 4G
```

## Architecture Benefits

### Separation of Concerns
- ML logic completely isolated from business logic
- Independent development and testing
- Clear API contracts

### Scalability
- Scale ML service separately based on load
- Backend can use cheaper instances
- ML service can use GPU instances

### Maintainability
- Update ML models without touching backend
- Easier debugging and testing
- Smaller, focused codebases

### Deployment
- Independent deployment cycles
- Zero-downtime updates
- Easy rollback per service

### Cost Optimization
- ML service can auto-scale or run serverless
- Backend can use spot instances
- Pay only for what you use

## Monitoring

### Metrics to Track

**Backend API:**
- Request latency
- Error rate
- Active connections
- Database query time

**ML Service:**
- Face detection time
- Encoding time
- Match accuracy
- Queue depth

### Logging

Both services output structured logs to stdout:

```json
{
  "timestamp": "2024-01-20T10:30:00Z",
  "level": "INFO",
  "service": "backend-api",
  "endpoint": "/api/attendance/mark",
  "duration_ms": 2500
}
```

Use log aggregation tools like:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Datadog
- CloudWatch
- Stackdriver

## Troubleshooting

### ML Service Not Responding

```bash
# Check if ML service is running
curl http://localhost:8001/health

# Check logs
docker-compose logs ml-service

# Restart service
docker-compose restart ml-service
```

### Backend Can't Connect to ML Service

1. Verify `ML_SERVICE_URL` in backend `.env`
2. Check if ML service is healthy
3. Verify network connectivity
4. Check firewall rules

### Slow Performance

1. Check ML service resources (CPU, Memory)
2. Scale ML service horizontally
3. Use HOG model instead of CNN
4. Reduce `num_jitters` parameter
5. Implement caching

## Development

### Project Structure

```
server/
├── backend-api/          # Backend API service
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── core/        # Configuration
│   │   ├── db/          # Database models
│   │   ├── services/    # Business logic
│   │   ├── schemas/     # Pydantic models
│   │   └── main.py      # App entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
│
├── ml-service/          # ML Service
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── core/        # Configuration
│   │   ├── ml/          # ML logic
│   │   ├── schemas/     # Pydantic models
│   │   └── main.py      # App entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
│
├── docker-compose.yml   # Docker Compose config
├── DEPLOYMENT_GUIDE.md  # Deployment guide
└── README.md           # This file
```

### Adding New Features

**Backend Feature:**
1. Add route in `backend-api/app/api/routes/`
2. Add business logic in `backend-api/app/services/`
3. Update schemas if needed
4. Test endpoint

**ML Feature:**
1. Add ML logic in `ml-service/app/ml/`
2. Add endpoint in `ml-service/app/api/routes/`
3. Update schemas
4. Update ML client in backend

## Security

### Best Practices

- Use HTTPS in production
- Set strong JWT secrets
- Restrict ML service to private network
- Implement rate limiting
- Validate all inputs
- Use environment variables for secrets
- Regular security updates

### Network Security

```yaml
# docker-compose.yml
networks:
  frontend:
    # Exposed to internet
  backend:
    # Internal only
    internal: true

services:
  ml-service:
    networks:
      - backend  # Not exposed
```

## Contributing

1. Create feature branch
2. Make changes
3. Write tests
4. Run linter
5. Submit pull request

## License

See main repository LICENSE

## Support

- Documentation: See service READMEs
- Issues: GitHub Issues
- Deployment: See DEPLOYMENT_GUIDE.md
- **Separation Verification**: See [SEPARATION_VERIFICATION.md](./SEPARATION_VERIFICATION.md)

---

**Version**: 1.0  
**Last Updated**: 2026-01-20  
**Separation Status**: ✅ Verified
