# Clerk Authentication Integration

## Overview

This document describes the integration of Clerk authentication with the Test Data Generator MVP, enabling user management, subscription tiers, and usage tracking.

## Features

### 🔐 Authentication Methods
- **GitHub OAuth**: Sign in with GitHub account
- **Google OAuth**: Sign in with Google account  
- **Apple OAuth**: Sign in with Apple ID
- **JWT Token Verification**: Secure API access
- **Session Management**: User session tracking

### 💳 Subscription Tiers
- **Free**: 5 generations/month, basic features
- **Basic ($9.99/month)**: 50 generations/month, enhanced features
- **Professional ($29.99/month)**: Unlimited generations, priority queue
- **Enterprise ($99.99/month)**: Custom solutions, SLA guarantees

### 📊 Usage Tracking
- Generation count per month
- Download count per month
- Endpoint processing limits
- Storage usage tracking
- Priority queue management

## Architecture

### Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Clerk Auth     │    │   Backend       │
│                 │    │                  │    │                 │
│ • OAuth Buttons │───▶│ • JWT Tokens     │───▶│ • Auth Routes   │
│ • User Profile  │    │ • User Data      │    │ • Middleware    │
│ • Usage Stats   │    │ • Webhooks       │    │ • Priority      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### File Structure

```
app/
├── auth/
│   ├── __init__.py
│   ├── clerk_auth.py      # Clerk JWT verification
│   ├── middleware.py      # Auth middleware
│   └── routes.py          # Auth endpoints
├── templates/
│   ├── auth.html          # Login/signup page
│   └── pricing.html       # Subscription tiers
└── schemas.py             # User & subscription models
```

## Setup Instructions

### 1. Clerk Dashboard Configuration

1. **Create Clerk Application**
   - Go to [clerk.com](https://clerk.com)
   - Create new application
   - Note your `Publishable Key` and `Secret Key`

2. **Configure OAuth Providers**
   - GitHub: Add GitHub OAuth app credentials
   - Google: Add Google OAuth app credentials
   - Apple: Add Apple Sign-In credentials

3. **Set Environment Variables**
   ```bash
   CLERK_JWT_PUBLIC_KEY=your_public_key
   CLERK_ISSUER=https://clerk.your-domain.com
   CLERK_SECRET_KEY=your_secret_key
   ```

### 2. Webhook Configuration

1. **Configure Webhook Endpoint**
   - URL: `https://your-domain.com/auth/webhook/clerk`
   - Events: `user.created`, `user.updated`, `user.deleted`

2. **Verify Webhook Signature**
   - Clerk sends webhook signature for verification
   - Implement signature verification in production

### 3. Frontend Integration

1. **Include Clerk Script**
   ```html
   <script src="https://cdn.clerk.com/clerk.js"></script>
   ```

2. **Initialize Clerk**
   ```javascript
   Clerk.init({
     publishableKey: 'your_publishable_key'
   });
   ```

3. **Handle Authentication**
   ```javascript
   Clerk.addListener(({ user }) => {
     if (user) {
       // User is signed in
       showUserProfile(user);
     } else {
       // User is signed out
       showLoginForm();
     }
   });
   ```

## API Endpoints

### Authentication Routes

| Endpoint | Method | Description |
|-----------|--------|-------------|
| `/auth/login` | POST | Login with JWT token |
| `/auth/logout` | POST | Logout and invalidate session |
| `/auth/me` | GET | Get current user info |
| `/auth/subscription` | GET | Get user subscription |
| `/auth/usage` | GET | Get usage metrics |
| `/auth/tiers` | GET | Get available tiers |
| `/auth/webhook/clerk` | POST | Clerk webhook handler |

### Protected Routes

| Endpoint | Method | Auth Required | Description |
|-----------|--------|---------------|-------------|
| `/api/generate` | POST | Optional | Generate test cases |
| `/api/download/{task_id}` | GET | Yes | Download results |
| `/generate-ui` | POST | Optional | Web UI generation |

## Usage Examples

### 1. User Authentication

```python
from app.auth.middleware import require_auth, get_user_subscription
from app.schemas import UserProfile

@app.get("/protected")
async def protected_route(current_user: UserProfile = Depends(require_auth)):
    subscription = await get_user_subscription(current_user)
    return {"user": current_user, "tier": subscription.tier}
```

### 2. Usage Limit Checking

```python
from app.auth.middleware import check_generation_limit

@app.post("/generate")
async def generate_tests(
    current_user: UserProfile = Depends(require_auth),
    usage_check: bool = Depends(check_generation_limit)
):
    # User has passed usage limits
    return {"message": "Generation started"}
```

### 3. Priority-Based Generation

```python
from app.services.generation_service import get_generation_service, Priority

def get_user_priority(user: UserProfile) -> Priority:
    if user.subscription.tier == "pro":
        return Priority.HIGH
    elif user.subscription.tier == "basic":
        return Priority.NORMAL
    else:
        return Priority.LOW

# Submit to generation service with user priority
service = get_generation_service()
service.submit_request(
    request_data=data,
    priority=get_user_priority(user),
    task_id=task_id
)
```

## Subscription Tiers

### Free Tier
- **Price**: $0/month
- **Generations**: 5/month
- **Endpoints**: Up to 20
- **Priority**: Low (3)
- **Support**: Community

### Basic Tier
- **Price**: $9.99/month
- **Generations**: 50/month
- **Endpoints**: Up to 100
- **Priority**: Normal (2)
- **Support**: Email

### Professional Tier
- **Price**: $29.99/month
- **Generations**: Unlimited
- **Endpoints**: Unlimited
- **Priority**: High (1)
- **Support**: Priority

### Enterprise Tier
- **Price**: $99.99/month
- **Generations**: Unlimited
- **Endpoints**: Unlimited
- **Priority**: High (1)
- **Support**: Dedicated

## Security Considerations

### 1. JWT Verification
- Verify token signature using Clerk's public keys
- Check token expiration
- Validate issuer and audience claims

### 2. Rate Limiting
- Implement rate limiting per user
- Track usage across billing periods
- Prevent abuse of free tier

### 3. Webhook Security
- Verify webhook signatures
- Validate webhook payloads
- Handle webhook failures gracefully

### 4. Session Management
- Secure session storage
- Implement session expiration
- Clean up expired sessions

## Monitoring & Analytics

### 1. User Metrics
- Active users per tier
- Conversion rates
- Churn analysis

### 2. Usage Analytics
- Generations per user
- Popular output formats
- Peak usage times

### 3. Business Metrics
- Monthly recurring revenue
- Average revenue per user
- Tier distribution

## Future Enhancements

### 1. Payment Integration
- Stripe integration for subscriptions
- Automated billing
- Invoice generation

### 2. Advanced Analytics
- User behavior tracking
- A/B testing for pricing
- Predictive analytics

### 3. Enterprise Features
- SSO integration
- Custom branding
- API rate limiting

### 4. Team Management
- Team accounts
- Role-based access
- Usage sharing

## Troubleshooting

### Common Issues

1. **JWT Verification Failed**
   - Check Clerk public key configuration
   - Verify token expiration
   - Validate issuer URL

2. **Webhook Not Receiving Events**
   - Check webhook URL configuration
   - Verify webhook signature
   - Check server logs for errors

3. **User Limits Not Enforced**
   - Verify usage tracking implementation
   - Check subscription tier assignment
   - Validate middleware configuration

### Debug Commands

```bash
# Check Clerk configuration
curl -H "Authorization: Bearer YOUR_TOKEN" /auth/me

# Verify webhook endpoint
curl -X POST /auth/webhook/clerk -d '{"type":"test"}'

# Check user subscription
curl -H "Authorization: Bearer YOUR_TOKEN" /auth/subscription
```

## Support

For issues related to:
- **Clerk Integration**: Check Clerk documentation and support
- **Authentication**: Review logs and middleware configuration
- **Subscription Management**: Verify tier configuration and limits
- **Usage Tracking**: Check database and analytics implementation

## Resources

- [Clerk Documentation](https://clerk.com/docs)
- [JWT.io](https://jwt.io) - JWT token debugging
- [OAuth 2.0 Guide](https://oauth.net/2/) - OAuth implementation
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/) - FastAPI security features
