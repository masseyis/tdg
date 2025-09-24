# SpecMint Brownfield Product Requirements Document (PRD)

## Executive Summary

**SpecMint** is a test data generation platform that transforms OpenAPI specifications into comprehensive test suites. This PRD addresses the current brownfield state of the system and outlines the path forward for critical improvements in monetization, authentication, and QA/DevOps infrastructure.

### Current State Assessment
- **Functional Core**: Test generation engine is working and well-tested
- **Critical Issues**: Authentication system (Clerk) is broken, CI/CD pipeline unreliable
- **Technical Debt**: Significant infrastructure and deployment challenges
- **Business Impact**: User acquisition blocked, deployment process manual and error-prone

### Strategic Priorities
1. **Fix Authentication System** - Unblock user acquisition
2. **Implement Monetization** - Enable revenue generation
3. **Stabilize CI/CD Pipeline** - Ensure reliable deployments
4. **Enhance Testing Infrastructure** - Prevent production regressions

---

## 1. Product Overview

### 1.1 Product Vision
Transform OpenAPI specifications into production-ready test suites with AI-powered test case generation, enabling developers to ship faster with confidence.

### 1.2 Current Product Capabilities
- **OpenAPI Processing**: Parse and normalize OpenAPI 3.x specifications
- **AI-Powered Generation**: Generate test cases using OpenAI/Anthropic models
- **Multi-Format Output**: Support for Python, JavaScript, Postman, SQL, and more
- **Real-time Progress**: WebSocket-based progress tracking for long-running operations
- **API & Web Interface**: Both programmatic and web-based access patterns

### 1.3 Target Users
- **Primary**: Development teams needing comprehensive test coverage
- **Secondary**: QA engineers, DevOps teams, API developers
- **Use Cases**: API testing, integration testing, CI/CD pipeline testing

---

## 2. Current Architecture Analysis

### 2.1 Technical Stack
```
Backend: FastAPI (Python 3.10+)
Frontend: React + Jinja2 templates
Queue: Redis (planned, not fully implemented)
Storage: S3-compatible (planned)
Auth: Clerk (currently broken)
Deployment: Fly.io with unreliable CI/CD
```

### 2.2 Architecture Strengths
- **Clean API Design**: Well-separated JSON API and web form endpoints
- **Modular Generation**: Pluggable test case generators and renderers
- **Progress Tracking**: WebSocket infrastructure for real-time updates
- **Comprehensive Testing**: Good test coverage with pytest

### 2.3 Critical Weaknesses
- **Authentication System**: Clerk integration completely non-functional
- **CI/CD Pipeline**: GitHub Actions workflow unreliable, manual deployments required
- **Infrastructure**: Redis queue and S3 storage not fully implemented
- **Error Handling**: Limited production error monitoring and recovery

---

## 3. Problem Statement

### 3.1 Primary Problems
1. **User Acquisition Blocked**: Authentication system prevents new user signups
2. **Revenue Generation Impossible**: No monetization infrastructure in place
3. **Deployment Unreliable**: CI/CD failures require manual intervention
4. **Production Stability**: Functionality breaks in production due to testing gaps

### 3.2 Business Impact
- **Lost Revenue**: Unable to charge for premium features
- **User Churn**: Existing users may leave due to instability
- **Development Velocity**: Manual deployment process slows feature delivery
- **Technical Debt**: Accumulating issues making future development harder

---

## 4. Solution Requirements

### 4.1 Authentication System Fix (Priority: Critical)

#### 4.1.1 Requirements
- **Fix Clerk Integration**: Resolve current authentication failures
- **Fallback Plan**: Implement alternative auth provider if Clerk cannot be fixed
- **User Management**: Basic user registration, login, and session management
- **Security**: JWT-based authentication with proper token validation

#### 4.1.2 Success Criteria
- Users can successfully register and login
- Authentication middleware works for protected endpoints
- Session management handles concurrent users properly
- Security vulnerabilities are addressed

#### 4.1.3 Implementation Plan
1. **Week 1-2**: Debug and fix Clerk integration
2. **Week 3**: Implement fallback auth provider if needed
3. **Week 4**: Test authentication flow end-to-end
4. **Week 5**: Deploy and monitor authentication system

### 4.2 Monetization Implementation (Priority: High)

#### 4.2.1 Requirements
- **Subscription Plans**: Free, Pro, Enterprise tiers
- **Usage Limits**: API call quotas, generation limits per plan
- **Billing Integration**: Stripe or Lemon Squeezy webhook handling
- **User Entitlements**: Plan-based feature access and limits

#### 4.2.2 Plan Structure
```
Free Tier:
- 5 API generations per month
- Basic test case generation
- Standard output formats

Pro Tier ($29/month):
- 100 API generations per month
- AI-enhanced test cases
- All output formats
- Priority support

Enterprise Tier ($99/month):
- Unlimited generations
- Custom AI models
- White-label options
- Dedicated support
```

#### 4.2.3 Success Criteria
- Users can subscribe to paid plans
- Usage limits are enforced per plan
- Billing webhooks are processed correctly
- Revenue tracking and analytics are in place

#### 4.2.4 Implementation Plan
1. **Week 1-2**: Design billing schema and API endpoints
2. **Week 3-4**: Implement subscription management
3. **Week 5-6**: Integrate billing provider webhooks
4. **Week 7-8**: Test monetization flow end-to-end

### 4.3 CI/CD Pipeline Stabilization (Priority: High)

#### 4.3.1 Requirements
- **Reliable Builds**: Fix GitHub Actions workflow failures
- **Automated Testing**: Ensure all tests pass before deployment
- **Deployment Automation**: Reliable deployment to Fly.io
- **Rollback Capability**: Quick rollback on deployment failures

#### 4.3.2 Success Criteria
- CI/CD pipeline runs successfully 95%+ of the time
- All tests pass before deployment
- Deployments are fully automated
- Rollback process works within 5 minutes

#### 4.3.3 Implementation Plan
1. **Week 1**: Audit and fix GitHub Actions workflow
2. **Week 2**: Implement comprehensive testing in CI
3. **Week 3**: Add deployment automation and monitoring
4. **Week 4**: Test and validate CI/CD pipeline

### 4.4 Testing Infrastructure Enhancement (Priority: Medium)

#### 4.4.1 Requirements
- **End-to-End Testing**: UI-based testing with Selenium
- **Performance Testing**: Load testing for generation endpoints
- **Integration Testing**: Test complete user workflows
- **Monitoring**: Production error tracking and alerting

#### 4.4.2 Success Criteria
- E2E tests cover critical user journeys
- Performance meets SLA requirements
- Production errors are caught and reported
- Test coverage remains above 80%

---

## 5. Technical Implementation

### 5.1 Authentication Implementation

#### 5.1.1 Clerk Integration Fix
```python
# Current broken implementation in app/auth/clerk.py
# Needs debugging and potential replacement

# Alternative: Simple JWT-based auth
from app.auth.jwt_auth import JWTManager
from app.auth.models import User

# User registration and login endpoints
@app.post("/api/auth/register")
@app.post("/api/auth/login")
@app.post("/api/auth/logout")
```

#### 5.1.2 User Management
- **Database Schema**: User table with plan, usage, and billing info
- **Session Management**: Redis-based session storage
- **Security**: Password hashing, rate limiting, CSRF protection

### 5.2 Monetization Implementation

#### 5.2.1 Billing Schema
```python
# app/schemas.py additions
class SubscriptionPlan(BaseModel):
    id: str
    name: str
    price: float
    monthly_generations: int
    features: List[str]

class UserSubscription(BaseModel):
    user_id: str
    plan_id: str
    status: str  # active, canceled, past_due
    current_period_start: datetime
    current_period_end: datetime
    usage_count: int
```

#### 5.2.2 Usage Tracking
- **Redis Counters**: Track daily/monthly usage per user
- **Middleware**: Enforce limits before generation requests
- **Webhooks**: Process billing provider events

### 5.3 Infrastructure Improvements

#### 5.3.1 Redis Implementation
```python
# app/services/redis_service.py
import redis
from app.config import settings

redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=0,
    decode_responses=True
)

async def track_user_usage(user_id: str, plan_id: str):
    key = f"usage:{user_id}:{plan_id}:{datetime.now().strftime('%Y-%m')}"
    current_usage = redis_client.incr(key)
    return current_usage
```

#### 5.3.2 S3 Storage
```python
# app/services/storage_service.py
import boto3
from app.config import settings

s3_client = boto3.client(
    's3',
    endpoint_url=settings.s3_endpoint,
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key
)
```

---

## 6. Success Metrics

### 6.1 Authentication Metrics
- **Signup Success Rate**: >95%
- **Login Success Rate**: >99%
- **Session Stability**: <1% unexpected logouts

### 6.2 Monetization Metrics
- **Conversion Rate**: Free to paid >5%
- **Monthly Recurring Revenue**: Track growth month-over-month
- **Churn Rate**: <5% monthly churn
- **Average Revenue Per User**: Track ARPU growth

### 6.3 Technical Metrics
- **CI/CD Success Rate**: >95%
- **Deployment Frequency**: Daily deployments
- **Test Coverage**: Maintain >80%
- **Production Uptime**: >99.5%

---

## 7. Risk Assessment

### 7.1 High-Risk Items
- **Authentication System**: Complete failure blocks all user access
- **Billing Integration**: Incorrect implementation could lose revenue
- **CI/CD Pipeline**: Unreliable deployments risk production stability

### 7.2 Mitigation Strategies
- **Authentication**: Implement fallback auth provider
- **Billing**: Thorough testing with billing provider sandbox
- **CI/CD**: Manual deployment capability as backup

### 7.3 Contingency Plans
- **Week 1-2**: If Clerk cannot be fixed, implement alternative auth
- **Week 3-4**: If billing integration fails, implement usage tracking first
- **Week 5-6**: If CI/CD issues persist, establish manual deployment process

---

## 8. Implementation Timeline

### Phase 1: Foundation (Weeks 1-4)
- **Week 1-2**: Fix authentication system
- **Week 3-4**: Implement basic user management

### Phase 2: Monetization (Weeks 5-12)
- **Week 5-6**: Design and implement billing schema
- **Week 7-8**: Integrate billing provider
- **Week 9-10**: Implement usage tracking and limits
- **Week 11-12**: Test and validate monetization flow

### Phase 3: Infrastructure (Weeks 13-16)
- **Week 13-14**: Stabilize CI/CD pipeline
- **Week 15-16**: Implement Redis and S3 infrastructure

### Phase 4: Testing & Launch (Weeks 17-20)
- **Week 17-18**: Comprehensive testing and bug fixes
- **Week 19-20**: Production deployment and monitoring

---

## 9. Resource Requirements

### 9.1 Development Team
- **Backend Developer**: 1 FTE (Python/FastAPI)
- **Frontend Developer**: 0.5 FTE (React/UI)
- **DevOps Engineer**: 0.5 FTE (CI/CD, infrastructure)
- **QA Engineer**: 0.5 FTE (testing, automation)

### 9.2 Infrastructure Costs
- **Fly.io**: ~$50/month (current)
- **Redis**: ~$20/month (Redis Cloud)
- **S3 Storage**: ~$10/month (estimated)
- **Monitoring**: ~$30/month (Sentry, logging)

### 9.3 Third-Party Services
- **Authentication**: Clerk (current) or Auth0 alternative
- **Billing**: Stripe or Lemon Squeezy
- **Monitoring**: Sentry (current)

---

## 10. Conclusion

The SpecMint brownfield PRD addresses critical system failures while building a foundation for sustainable growth. The three-phase approach ensures that:

1. **User acquisition is unblocked** through authentication fixes
2. **Revenue generation begins** with monetization implementation
3. **System stability improves** through infrastructure enhancements
4. **Development velocity increases** with reliable CI/CD

Success depends on prioritizing authentication fixes first, then building monetization on a stable foundation. The 20-week timeline provides realistic milestones while addressing the most critical business blockers.

### Next Steps
1. **Immediate**: Begin authentication system debugging
2. **Week 1**: Establish development team and environment
3. **Week 2**: Start authentication implementation
4. **Ongoing**: Regular progress reviews and risk assessment

This PRD serves as the roadmap for transforming SpecMint from a broken brownfield system into a reliable, monetized platform ready for growth.

