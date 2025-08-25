# Sentry Error Tracking Setup

This project now includes Sentry integration for comprehensive error tracking and monitoring on both frontend and backend.

## Features

- **Backend Error Tracking**: Captures Python exceptions with context
- **Frontend Error Tracking**: Captures JavaScript errors and unhandled promise rejections
- **Performance Monitoring**: Tracks API response times and user interactions
- **Session Replay**: Records user sessions for debugging (configurable)
- **Environment Separation**: Different configurations for development, staging, and production

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Sentry settings for error tracking and monitoring
# Get your DSN from https://sentry.io/settings/projects/your-project/keys/
SENTRY_DSN=https://your-sentry-dsn-here@sentry.io/your-project-id
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
```

### Setting up a Sentry Project

1. **Create a Sentry Account**: Go to [sentry.io](https://sentry.io) and create an account
2. **Create a New Project**: 
   - Choose "FastAPI" for the backend
   - Choose "JavaScript" for the frontend
3. **Get Your DSN**: Copy the DSN from your project settings
4. **Configure Environment**: Set `SENTRY_ENVIRONMENT` to match your deployment (development, staging, production)

## Backend Integration

### Automatic Error Capture

The backend automatically captures:
- Unhandled exceptions in API endpoints
- Validation errors (filtered out by default)
- HTTP exceptions (filtered out by default)
- Custom context for generation errors

### Manual Error Reporting

```python
from app.sentry import capture_exception, capture_message, set_tag

# Capture an exception with context
try:
    # Your code here
    pass
except Exception as e:
    capture_exception(e, {
        "user_id": "123",
        "operation": "file_upload",
        "file_size": file_size
    })

# Capture a message
capture_message("User uploaded large file", level="info", context={
    "file_size": file_size,
    "user_id": user_id
})

# Set tags for filtering
set_tag("user_type", "premium")
set_tag("feature", "bulk_upload")
```

### Testing Sentry Integration

To test that Sentry is working correctly, use the test endpoint:

```bash
# Test Sentry error capture
curl http://localhost:8000/sentry-debug
```

This endpoint:
- Intentionally triggers a division by zero error
- Captures the error in Sentry with context
- Returns a 500 error with message "Sentry test error triggered successfully"
- Useful for verifying Sentry integration is working correctly

## Frontend Integration

### Automatic Error Capture

The frontend automatically captures:
- JavaScript errors
- Unhandled promise rejections
- Network request failures
- User interactions (with session replay)

### Manual Error Reporting

```javascript
// Capture an exception
try {
    // Your code here
} catch (error) {
    Sentry.captureException(error, {
        tags: {
            component: 'file-upload',
            user_type: 'premium'
        },
        extra: {
            file_size: fileSize,
            file_type: fileType
        }
    });
}

// Capture a message
Sentry.captureMessage('User started file upload', 'info');

// Set user context
Sentry.setUser({
    id: '123',
    email: 'user@example.com',
    username: 'john_doe'
});

// Set tags
Sentry.setTag('feature', 'bulk-upload');
```

## Performance Monitoring

Sentry automatically tracks:
- API response times
- Database query performance
- Frontend page load times
- User interactions

## Session Replay

Session replay is enabled by default but can be configured:
- `maskAllText: false` - Shows text content for debugging
- `blockAllMedia: false` - Shows images and media
- Adjust these settings based on your privacy requirements

## Error Filtering

### Backend Filtering

The backend filters out common expected errors:
- `ValidationError` - Form validation errors
- `HTTPException` - HTTP status errors

### Frontend Filtering

The frontend filters out:
- `ValidationError` - Form validation errors
- `TypeError` - Common JavaScript type errors

## Deployment Considerations

### Production

```bash
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of requests
SENTRY_PROFILES_SAMPLE_RATE=0.1  # 10% of profiles
```

### Development

```bash
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=1.0  # 100% of requests for debugging
SENTRY_PROFILES_SAMPLE_RATE=1.0  # 100% of profiles for debugging
```

### Staging

```bash
SENTRY_ENVIRONMENT=staging
SENTRY_TRACES_SAMPLE_RATE=0.5  # 50% of requests
SENTRY_PROFILES_SAMPLE_RATE=0.5  # 50% of profiles
```

## Privacy and Security

- **Data Masking**: Sensitive data is automatically masked
- **Session Replay**: Can be disabled or configured for privacy
- **Error Filtering**: Prevents noise from expected errors
- **Environment Separation**: Keeps development errors separate from production

## Monitoring Dashboard

Once configured, you can monitor:
- Error rates and trends
- Performance metrics
- User experience issues
- Release health
- Session replays for debugging

## Troubleshooting

### Common Issues

1. **Sentry not capturing errors**: Check your DSN is correct
2. **Too many errors**: Adjust filtering in `before_send` functions
3. **Performance impact**: Reduce sample rates for high-traffic applications
4. **Privacy concerns**: Configure session replay settings appropriately

### Testing Sentry

```python
# Test backend error capture
from app.sentry import capture_message
capture_message("Test message from backend", level="info")
```

```javascript
// Test frontend error capture
Sentry.captureMessage("Test message from frontend", "info");
```

## Support

For Sentry-specific issues, refer to:
- [Sentry Documentation](https://docs.sentry.io/)
- [FastAPI Integration Guide](https://docs.sentry.io/platforms/python/fastapi/)
- [JavaScript Integration Guide](https://docs.sentry.io/platforms/javascript/)
