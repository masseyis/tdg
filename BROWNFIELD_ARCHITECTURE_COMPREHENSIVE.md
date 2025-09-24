# SpecMint Comprehensive Brownfield Architecture Document

## Introduction

This document captures the **ACTUAL CURRENT STATE** of the **SpecMint** codebase, including technical debt, workarounds, and real-world patterns. It serves as a reference for AI agents and senior developers working on bug fixes, feature additions, and testing.

### Document Scope

This documentation is a comprehensive analysis of the entire system, with a specific focus on areas relevant to the planned **monetization** enhancement and the **QA/DevOps** pipeline improvements.

### Change Log

| Date | Version | Description | Author |
| :--- | :--- | :--- | :--- |
| 2025-01-12 | 1.0 | Initial comprehensive brownfield analysis based on actual codebase | Winston (Architect Agent) |

---

## Quick Reference - Key Files and Entry Points

### Critical Files for Understanding the System

- **Main Entry**: `app/main.py` (FastAPI application with 698 lines)
- **Authentication**: `app/auth/clerk_auth.py` (Clerk integration with known issues)
- **Generation Pipeline**: `app/generation/cases.py` (core test case generation logic)
- **AI Providers**: `app/ai/hybrid_provider.py` (multi-provider AI integration)
- **Generation Service**: `app/services/generation_service.py` (priority queue management)
- **Configuration**: `app/config.py` (comprehensive settings management)
- **CI/CD Configuration**: `.github/workflows/deploy.yml` (deployment workflow)

---

## High-Level Architecture

### Technical Summary

The system is a **monolithic FastAPI application** with a **hybrid frontend approach** (Jinja2 templates + planned React). The backend is built with **Python 3.10+** using **FastAPI**, with **AI-powered test generation** as the core business logic.

### Actual Tech Stack (from requirements.txt and code analysis)

| Category | Technology | Version | Notes |
| :--- | :--- | :--- | :--- |
| Runtime | Python | 3.10+ | Primary backend language |
| Backend Framework | FastAPI | 0.116.0+ | Modern async web framework |
| Frontend | Jinja2 + React (planned) | 3.1.6+ | Currently Jinja2, React planned |
| AI Providers | OpenAI, Anthropic | Latest | Hybrid provider system |
| Queue | Thread-based Priority Queue | Custom | In-memory priority queuing |
| Storage | Local filesystem | N/A | Temporary ZIP files, no persistent storage |
| Auth | Clerk | Integration | **Critical: Known issues with authentication** |
| Deployment | Fly.io | Current | Container-based deployment |
| CI/CD | GitHub Actions | Current | **Critical: Unreliable deployment pipeline** |
| Monitoring | Sentry | Integrated | Error tracking and performance monitoring |

### Repository Structure Reality Check

- **Type**: Monorepo (single Python application)
- **Package Manager**: `pip` for Python dependencies
- **Notable**: Single FastAPI application with modular structure

---

## Source Tree and Module Organization

### Project Structure (Actual)

```text
project-root/
├── app/                           # Main application package
│   ├── __init__.py               # Package initialization
│   ├── main.py                   # FastAPI application (698 lines)
│   ├── config.py                 # Configuration management
│   ├── schemas.py                # Pydantic models (191 lines)
│   ├── websocket_manager.py      # WebSocket progress tracking
│   ├── progress.py               # Progress tracking models
│   ├── sentry.py                 # Sentry integration
│   ├── auth/                     # Authentication module
│   │   ├── clerk_auth.py         # Clerk integration (264 lines)
│   │   ├── middleware.py         # Auth middleware (247 lines)
│   │   └── routes.py             # Auth routes (436 lines)
│   ├── ai/                       # AI provider management
│   │   ├── base.py               # Base provider interface
│   │   ├── hybrid_provider.py    # Multi-provider orchestration (327 lines)
│   │   ├── openai_provider.py    # OpenAI integration
│   │   ├── anthropic_provider.py # Anthropic integration
│   │   ├── fast_provider.py      # Fast generation provider
│   │   ├── null_provider.py      # Fallback provider
│   │   └── prompts.py            # AI prompt templates
│   ├── generation/                # Test generation core
│   │   ├── cases.py              # Test case generation (330 lines)
│   │   └── renderers/            # Output format renderers
│   ├── services/                  # Business logic services
│   │   └── generation_service.py # Priority queue service (413 lines)
│   ├── utils/                     # Utility functions
│   ├── static/                    # Static assets
│   └── templates/                 # Jinja2 HTML templates
├── tests/                         # Test suite
├── requirements.txt               # Python dependencies
├── fly.toml                      # Fly.io deployment config
├── Dockerfile                    # Container configuration
└── .github/workflows/            # CI/CD workflows
    ├── test-suite.yml            # Comprehensive testing
    └── deploy.yml                # Deployment workflow
```

### Key Modules and Their Purpose

- **Authentication**: `app/auth/clerk_auth.py` - Manages user sign-in and signup. **This is a known point of failure.**
- **Generation Pipeline**: `app/generation/cases.py` - The core AI-driven logic for creating test cases and data.
- **AI Providers**: `app/ai/hybrid_provider.py` - Orchestrates multiple AI providers with fallback strategies.
- **Generation Service**: `app/services/generation_service.py` - Manages priority queuing for test generation requests.
- **WebSocket Manager**: `app/websocket_manager.py` - Handles real-time progress tracking for long-running operations.

---

## Technical Debt and Known Issues

### Critical Technical Debt

1. **Authentication System**: Clerk integration is completely non-functional, blocking user acquisition
2. **CI/CD Pipeline**: GitHub Actions workflow is unreliable, requiring manual intervention for deployments
3. **Storage Infrastructure**: No persistent storage for generated artifacts (only temporary local files)
4. **Queue Management**: In-memory priority queue without persistence or Redis integration
5. **Frontend Architecture**: Mix of Jinja2 templates and planned React, creating inconsistency

### Workarounds and Gotchas

- **Authentication Bypass**: Development mode disables authentication entirely (`DISABLE_AUTH_FOR_DEV=true`)
- **Manual Deployments**: CI/CD failures require manual deployment to production
- **Temporary Storage**: Generated ZIP files are stored locally and cleaned up, no persistence
- **Memory Management**: Manual garbage collection after generation to prevent memory leaks
- **Error Handling**: Limited error recovery, errors often result in HTTP 500 responses

### Current Authentication State

```python
# From app/config.py - Authentication is currently disabled for development
disable_auth_for_dev: bool = os.getenv("DISABLE_AUTH_FOR_DEV", "false").lower() == "true"

# From app/main.py - Authentication temporarily disabled for E2E tests
# NOTE: James chose to temporarily disable authentication for E2E tests
# Authentication temporarily disabled - will re-enable after testing
# TODO: Re-enable authentication after E2E tests are working
```

---

## API Architecture and Endpoints

### Current API Structure

#### Core Endpoints

1. **`/api/generate`** (POST) - JSON API for programmatic access
   - **Purpose**: API integrations, CI/CD, automation
   - **Input**: JSON payload with OpenAPI spec
   - **Processing**: Sync OR Async (configurable via `use_background`)
   - **Output**: ZIP file (sync) OR task_id (async)

2. **`/generate-ui`** (POST) - Web form submissions
   - **Purpose**: Web UI, file uploads, immediate download
   - **Input**: Form data with file uploads
   - **Processing**: Currently synchronous (returns ZIP file directly)
   - **Output**: ZIP file with generated artifacts

3. **`/api/download/{task_id}`** (GET) - Download completed results
   - **Purpose**: Retrieve results from async generation
   - **Input**: task_id from async generation
   - **Output**: ZIP file with generated artifacts

4. **`/ws/{task_id}`** (WebSocket) - Real-time progress updates
   - **Purpose**: Live progress tracking for long-running operations
   - **Input**: task_id connection
   - **Output**: Live progress messages

#### Supporting Endpoints

- **`/api/validate`** (POST) - OpenAPI specification validation
- **`/health`** (GET) - Health check endpoint
- **`/status`** (GET) - Service status and concurrency information
- **`/progress/{request_id}`** (GET) - Progress fallback for non-WebSocket clients

### API Design Principles

The system maintains clear separation of concerns:
- **`/api/generate`** for JSON API consumers (programmatic access)
- **`/generate-ui`** for web form submissions (user interface)
- **Never mix JSON and form data handling**
- **Always use appropriate endpoint for the use case**

---

## Generation Service Architecture

### Priority Queue System

```python
# From app/services/generation_service.py
class Priority(Enum):
    """Priority levels for generation requests"""
    LOW = 3      # Free tier, processed when resources available
    NORMAL = 2   # Standard users, normal queue
    HIGH = 1     # Premium users, immediate processing

class GenerationService:
    """Service for managing test generation with priority queuing"""
    
    def __init__(self, max_workers: int = 2, queue_size: int = 100):
        self.max_workers = max_workers
        self.queue_size = queue_size
        self.request_queue = PriorityQueue(maxsize=queue_size)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
```

### Current Limitations

- **In-Memory Queue**: No persistence, queue lost on service restart
- **Limited Workers**: Default 2 workers, configurable via environment
- **No Redis Integration**: Planned but not implemented
- **Memory Management**: Manual cleanup required to prevent memory leaks

---

## AI Provider Architecture

### Hybrid Provider System

```python
# From app/ai/hybrid_provider.py
class HybridProvider:
    """Orchestrates multiple AI providers with fallback strategies"""
    
    def __init__(self):
        self.providers = {
            'openai': OpenAIProvider(),
            'anthropic': AnthropicProvider(),
            'fast': FastProvider(),
            'null': NullProvider()  # Fallback provider
        }
```

### Provider Capabilities

- **OpenAI**: GPT-3.5-turbo, GPT-4o-mini, GPT-4o
- **Anthropic**: Claude-3-Haiku, Claude-3-Sonnet, Claude-3-Opus
- **Fast Provider**: Optimized for speed over quality
- **Null Provider**: Fallback when AI providers are unavailable

### Configuration

```python
# From app/config.py
# AI Model settings for speed/quality tradeoff
openai_model: str = "gpt-3.5-turbo"  # Options: gpt-4o-mini (fastest), gpt-3.5-turbo (balanced), gpt-4o (best quality)
anthropic_model: str = "claude-3-haiku-20240307"  # Options: claude-3-haiku-20240307 (fastest), claude-3-sonnet-20240229 (balanced), claude-3-opus-20240229 (best quality)

# AI Generation settings
ai_temperature: float = 0.7  # Lower = more consistent, faster
ai_max_tokens: int = 2000    # Lower = faster generation
ai_timeout: int = 60         # Increased timeout for better reliability
```

---

## Data Models and Schemas

### Core Request/Response Models

```python
# From app/schemas.py
class GenerateRequest(BaseModel):
    """Request schema for test generation"""
    openapi: str = Field(..., description="OpenAPI specification content or URL")
    casesPerEndpoint: int = Field(10, description="Number of test cases per endpoint")
    outputs: List[str] = Field(["junit", "python", "nodejs", "postman"], description="Output formats to generate")
    domainHint: Optional[str] = Field(None, description="Domain hint for test data")
    seed: Optional[int] = Field(None, description="Random seed for reproducible results")
    aiSpeed: str = Field("fast", description="AI generation speed preference")
    use_background: Optional[bool] = Field(False, description="Use background processing")

class UserProfile(BaseModel):
    """User profile information from Clerk"""
    user_id: str
    email: Optional[str] = None
    email_verified: bool = False
    oauth_provider: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[int] = None

class SubscriptionTier(BaseModel):
    """User subscription tier information"""
    tier: str = Field(..., description="Subscription tier: free, basic, pro, enterprise")
    name: str = Field(..., description="Human-readable tier name")
    monthly_price: Optional[float] = Field(None, description="Monthly price in USD")
    features: List[str] = Field(..., description="List of features included")
    limits: Dict[str, Any] = Field(..., description="Usage limits for this tier")
    priority: int = Field(..., description="Priority level for generation queue")
```

### Current State

- **Schemas Defined**: Comprehensive models for requests, responses, and user data
- **Not Implemented**: User management, subscription tracking, usage limits
- **Ready for Implementation**: Models are in place for monetization features

---

## Development and Deployment

### Current Build and Deployment Process

#### CI/CD Pipeline

```yaml
# From .github/workflows/deploy.yml
name: Deploy to Fly.io

# ⚠️  CRITICAL: This workflow only runs after ALL tests pass with coverage
# The comprehensive test suite must complete successfully before deployment
# This ensures the deployed service works exactly like local development

on:
  workflow_run:
    workflows: ["Comprehensive Test Suite"]
    types: [completed]
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
```

#### Deployment Configuration

```toml
# From fly.toml
app = "tdg-mvp"
primary_region = "ord"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8080"
  LOG_LEVEL = "INFO"
  PYTHONUNBUFFERED = "1"
  PYTHONDONTWRITEBYTECODE = "1"
  PYTHONOPTIMIZE = "1"
  UVICORN_WORKERS = "3"
  UVICORN_THREADS = "4"
  GENERATION_WORKERS = "2"
  GENERATION_QUEUE_SIZE = "100"

[[vm]]
  memory = "2GB"
  cpu_kind = "shared"
  cpus = 2
```

### Current Issues

1. **CI/CD Reliability**: Workflow depends on comprehensive test suite, which may be failing
2. **Manual Intervention**: Deployments often require manual intervention due to CI failures
3. **Test Dependencies**: Deployment blocked until all tests pass with coverage
4. **No Rollback Strategy**: Limited rollback capability on deployment failures

---

## Testing Infrastructure

### Current Test Coverage

- **Unit Tests**: pytest-based testing framework
- **Integration Tests**: Limited integration testing
- **E2E Tests**: Selenium-based end-to-end testing
- **Coverage Reporting**: pytest-cov with HTML and XML output
- **Test Artifacts**: Comprehensive test output and coverage reports

### Test Structure

```
tests/
├── test_ai_generation.py      # AI provider testing
├── test_ai_providers.py       # Provider integration testing
├── test_auth_basic.py         # Basic authentication testing
├── test_case_generation.py    # Test case generation testing
├── test_domain_data.py        # Domain-specific data testing
├── test_e2e_functional.py     # End-to-end functional testing
├── test_enhanced_ai.py        # Enhanced AI features testing
├── test_health.py             # Health check testing
├── test_hybrid_provider.py    # Hybrid provider testing
├── test_openapi_parsing.py    # OpenAPI parsing testing
├── test_post_deploy.py        # Post-deployment testing
└── test_renderers.py          # Output renderer testing
```

### Testing Challenges

- **Authentication Disabled**: E2E tests run with authentication bypassed
- **No Production Testing**: Limited testing of deployed service
- **Coverage Requirements**: CI/CD requires high test coverage to pass

---

## If Enhancement PRD Provided - Impact Analysis

### Files That Will Need Modification

The planned monetization enhancement will directly impact the following areas:

1. **Authentication System**: `app/auth/` - Complete overhaul or replacement of Clerk integration
2. **User Management**: New user models and database integration
3. **Billing Integration**: New billing endpoints and webhook handlers
4. **Usage Tracking**: Integration with generation service for quota enforcement
5. **Storage Infrastructure**: Persistent storage for user artifacts and billing data

### New Files/Modules Needed

- **Database Models**: User, subscription, and billing models
- **Billing Service**: Subscription management and webhook processing
- **Usage Service**: Quota tracking and enforcement
- **Storage Service**: S3-compatible storage integration
- **Redis Service**: Queue persistence and session management

### Integration Considerations

- **Authentication Middleware**: Must integrate with existing `require_auth_or_dev` dependency
- **Generation Service**: Priority queuing must respect user subscription tiers
- **WebSocket Progress**: Progress tracking must include user context
- **Error Handling**: Comprehensive error handling for billing and usage operations

---

## Technical Constraints and Limitations

### Current Limitations

1. **No Database**: Application runs without persistent database
2. **No Redis**: Queue management is in-memory only
3. **No S3 Storage**: Generated artifacts are temporary local files
4. **Authentication Disabled**: No user management or access control
5. **Memory Management**: Manual garbage collection required

### Performance Constraints

- **Concurrent Requests**: Limited to 30 concurrent HTTP requests
- **AI Concurrency**: Limited to 8 concurrent AI requests
- **Generation Workers**: Limited to 2 generation worker threads
- **Memory Usage**: 2GB VM memory limit on Fly.io

### Security Constraints

- **No User Isolation**: All users share the same generation queue
- **No Rate Limiting**: No per-user rate limiting implemented
- **No Input Validation**: Limited validation of OpenAPI specifications
- **No Audit Logging**: No tracking of user actions or data access

---

## Monitoring and Observability

### Current Monitoring

- **Sentry Integration**: Error tracking and performance monitoring
- **Health Checks**: Basic health check endpoint
- **Status Endpoint**: Service status and resource usage
- **Logging**: Structured logging with configurable levels

### Monitoring Gaps

- **No Metrics Collection**: No Prometheus or similar metrics
- **No Alerting**: No automated alerting on failures
- **No Performance Monitoring**: Limited performance insights
- **No User Analytics**: No tracking of user behavior or usage patterns

---

## Appendix - Useful Commands and Scripts

### Development Commands

```bash
# Start development server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_e2e_functional.py -v

# Run tests with verbose output
pytest -v -s

# Check code quality
flake8 app/
black --check app/
```

### Deployment Commands

```bash
# Deploy to Fly.io
flyctl deploy

# Check deployment status
flyctl status

# View logs
flyctl logs

# SSH into deployment
flyctl ssh console

# Scale deployment
flyctl scale count 2
```

### Environment Variables

```bash
# Required for production
export DISABLE_AUTH_FOR_DEV=false
export CLERK_JWT_PUBLIC_KEY="your-clerk-public-key"
export CLERK_ISSUER="https://clerk.your-domain.com"
export CLERK_SECRET_KEY="your-clerk-secret-key"
export CLERK_WEBHOOK_SECRET="your-clerk-webhook-secret"

# AI Provider Keys
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Sentry Configuration
export SENTRY_DSN="your-sentry-dsn"
export SENTRY_ENVIRONMENT="production"

# Performance Tuning
export UVICORN_WORKERS=3
export UVICORN_THREADS=4
export GENERATION_WORKERS=2
export GENERATION_QUEUE_SIZE=100
export MAX_CONCURRENT_REQUESTS=30
export AI_CONCURRENCY_LIMIT=8
```

---

## Conclusion

This comprehensive brownfield architecture document captures the **actual current state** of the SpecMint system, including:

1. **Functional Core**: Test generation engine is working and well-tested
2. **Critical Issues**: Authentication system completely broken, CI/CD pipeline unreliable
3. **Technical Debt**: Significant infrastructure gaps (no database, no Redis, no persistent storage)
4. **Architecture Strengths**: Clean API design, modular AI provider system, comprehensive testing
5. **Implementation Readiness**: Schemas and models are in place for monetization features

The system is ready for transformation from a broken brownfield state into a reliable, monetized platform, but requires significant infrastructure work and authentication system replacement.

### Next Steps

1. **Immediate**: Fix authentication system (Clerk or replacement)
2. **Short-term**: Implement basic user management and database integration
3. **Medium-term**: Add Redis and S3 storage infrastructure
4. **Long-term**: Stabilize CI/CD pipeline and add comprehensive monitoring

This document serves as the foundation for planning and implementing the enhancements outlined in the brownfield PRD.

