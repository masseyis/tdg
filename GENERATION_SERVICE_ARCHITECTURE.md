# Generation Service Architecture

## Overview

The Generation Service is a priority-based queuing system that separates test generation from the main web server threads, preventing thread starvation and enabling tiered pricing based on priority levels.

## Architecture Components

### 1. Generation Service (`app/services/generation_service.py`)

**Purpose**: Manages test generation requests with priority queuing using a separate thread pool.

**Key Features**:
- **Priority Queue**: Handles HIGH, NORMAL, and LOW priority requests
- **Separate Thread Pool**: Dedicated workers for generation tasks
- **Progress Tracking**: Real-time progress updates via WebSocket
- **Statistics**: Comprehensive monitoring and metrics

**Priority Levels**:
- `HIGH` (1): Premium users, immediate processing
- `NORMAL` (2): Standard users, normal queue
- `LOW` (3): Free tier, processed when resources available

### 2. Thread Management

**Configuration**:
```python
# Uvicorn settings (web server)
uvicorn_workers: int = 2      # Number of worker processes
uvicorn_threads: int = 4      # Threads per worker

# Generation service settings
generation_workers: int = 2   # Dedicated generation threads
generation_queue_size: int = 100  # Maximum queued requests
```

**Thread Allocation**:
- **Web Server**: 2 processes × 4 threads = 8 threads for HTTP requests
- **Generation Service**: 2 dedicated threads for test generation
- **Total**: 10 threads available, with clear separation of concerns

### 3. Request Flow

```
1. HTTP Request → Uvicorn Worker Thread
2. Background Task → Generation Service Queue
3. Generation Worker → Process Request
4. Progress Updates → WebSocket → Frontend
5. Result → ZIP File → Download
```

## Configuration

### Environment Variables

```bash
# Uvicorn settings
UVICORN_WORKERS=2
UVICORN_THREADS=4

# Generation service settings
GENERATION_WORKERS=2
GENERATION_QUEUE_SIZE=100
```

### Fly.io Configuration

```toml
[[vm]]
  memory = "2GB"      # Increased from 1GB
  cpu_kind = "shared"
  cpus = 2           # Increased from 1

[env]
  UVICORN_WORKERS = "2"
  UVICORN_THREADS = "4"
  GENERATION_WORKERS = "2"
  GENERATION_QUEUE_SIZE = "100"
```

## Benefits

### 1. Thread Starvation Prevention
- **Before**: Generation blocked all web server threads
- **After**: Dedicated generation threads, web requests always served

### 2. Scalable Priority System
- **Future**: Tiered pricing based on priority levels
- **Current**: All requests use NORMAL priority
- **Flexible**: Easy to add user-based priority assignment

### 3. Better Resource Utilization
- **Memory**: Increased to 2GB for better performance
- **CPU**: 2 cores for parallel processing
- **Threads**: Optimal allocation for web + generation

### 4. Monitoring & Observability
- **Status Endpoint**: `/status` shows thread usage and service stats
- **WebSocket Progress**: Real-time generation progress
- **Error Tracking**: Sentry integration for all components

## Implementation Details

### Service Lifecycle

```python
# Startup
@app.on_event("startup")
async def startup_event():
    get_generation_service()  # Initialize service

# Shutdown
@app.on_event("shutdown")
async def shutdown_event():
    shutdown_generation_service()  # Clean shutdown
```

### Request Processing

```python
# Submit request to service
service.submit_request(
    request_data=request_data,
    progress_callback=progress_callback,
    priority=Priority.NORMAL,
    task_id=task_id
)
```

### Progress Updates

```python
# Async progress callback
async def progress_callback(stage: str, progress: int, message: str):
    await update_progress(task_id, stage, progress, message)
```

## Monitoring

### Status Endpoint (`/status`)

Returns comprehensive system status:
```json
{
  "status": "healthy",
  "concurrent_requests": 5,
  "max_concurrent_requests": 30,
  "uvicorn_workers": 2,
  "uvicorn_threads": 4,
  "generation_service": {
    "total_requests": 10,
    "completed_requests": 8,
    "failed_requests": 0,
    "queue_size": 2,
    "active_workers": 1,
    "running": true
  }
}
```

### Health Checks

- **Web Server**: Always responds to `/health`
- **Generation Service**: Monitored via `/status`
- **Fly.io**: Automatic health checks every 15s

## Future Enhancements

### 1. Tiered Pricing
```python
# User-based priority assignment
if user.tier == "premium":
    priority = Priority.HIGH
elif user.tier == "standard":
    priority = Priority.NORMAL
else:
    priority = Priority.LOW
```

### 2. Dynamic Scaling
- Auto-scale generation workers based on queue size
- Load-based priority adjustment
- Resource usage optimization

### 3. Advanced Queuing
- Queue position estimation
- Estimated wait times
- Priority bumping for long waits

## Troubleshooting

### Common Issues

1. **Queue Full**: Increase `GENERATION_QUEUE_SIZE`
2. **Slow Processing**: Increase `GENERATION_WORKERS`
3. **Web Server Slow**: Increase `UVICORN_WORKERS` or `UVICORN_THREADS`
4. **Memory Issues**: Increase Fly.io memory allocation

### Debugging

```bash
# Check service status
curl https://your-app.fly.dev/status

# Monitor logs
fly logs

# Check resource usage
fly status
```

## Performance Characteristics

### Thread Allocation
- **Web Requests**: 8 threads (2 workers × 4 threads)
- **Generation**: 2 dedicated threads
- **Total**: 10 concurrent operations

### Memory Usage
- **Base**: ~200MB for FastAPI + dependencies
- **Generation**: ~100-500MB per active generation
- **Total**: 2GB allocation provides headroom

### Scalability
- **Horizontal**: Add more Fly.io machines
- **Vertical**: Increase CPU/memory allocation
- **Queue**: Handle burst traffic with priority queuing
