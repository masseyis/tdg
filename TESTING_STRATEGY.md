# 🧪 Testing Strategy & Deployment Requirements

## ⚠️ CRITICAL REQUIREMENTS

**ALL TESTS MUST RUN WITH COVERAGE AND PASS BEFORE DEPLOYMENT**

### 🎯 Most Important Tests

1. **E2E Test** (`test_complete_user_experience`) - **CRITICAL**
   - Validates the complete user journey through the UI
   - Tests: File upload → Generation → Download → Test execution
   - Must pass on every push and before deployment
   - Runs locally with full browser automation

2. **Post-Deploy Test** (`test_deployed_service_complete_user_experience`) - **CRITICAL**
   - Reuses the same code as the e2e test but runs against the live deployed site
   - Target: https://tdg-mvp.fly.dev
   - Validates deployed service works exactly like local development
   - Must always run against the deployed site, never locally
   - **IMPORTANT**: Uses same WebUIDriver and test logic as e2e test - no duplicate code to maintain

## 🔄 Workflow Overview

### 1. Comprehensive Test Suite (Runs on every push)
```
comprehensive-test-suite → e2e-functional-test → integration-tests → coverage-analysis
```

**comprehensive-test-suite:**
- Runs ALL tests with coverage (excluding post-deploy tests)
- Coverage must be >=20%
- Includes linting and code quality checks
- Must pass before any other jobs run
- Uses pytest marker `-m "not post_deploy"` to exclude post-deployment tests

**e2e-functional-test:**
- Runs the critical e2e test
- Validates complete user journey
- Must pass before deployment

**integration-tests:**
- Tests against local server
- Validates API endpoints work correctly

**coverage-analysis:**
- Generates coverage reports and trends
- Uploads artifacts for historical analysis

### 2. Deployment (Only after tests pass)
```
Deploy to Fly.io → Post-deployment validation
```

**Deploy to Fly.io:**
- Only runs after comprehensive test suite passes
- Deploys to https://tdg-mvp.fly.dev
- Runs health check

**Post-deployment validation:**
- Runs the post-deploy test against live site
- Validates deployed service works correctly
- Must mimic e2e test behavior exactly

## 🧪 Test Types & Coverage

### Unit Tests
- **Coverage**: Must be >=20%
- **Scope**: All app modules
- **Purpose**: Validate individual components work correctly

### Integration Tests
- **Scope**: API endpoints, server startup
- **Purpose**: Validate components work together
- **Environment**: Local test server

### E2E Tests
- **Scope**: Complete user journey
- **Purpose**: Validate the entire application works
- **Environment**: Local with browser automation

### Post-Deploy Tests
- **Scope**: Live deployed service
- **Purpose**: Validate production deployment works
- **Environment**: https://tdg-mvp.fly.dev
- **Marker**: `@pytest.mark.post_deploy`
- **Execution**: Only runs after successful deployment, never in pre-deploy test suite
- **Code Reuse**: Uses same WebUIDriver and test logic as e2e test - single source of truth

## 📊 Coverage Requirements

### Current Thresholds
- **Minimum Coverage**: 20%
- **Target Coverage**: 40%
- **Long-term Goal**: 60%

### Coverage Reports
- **XML**: For CI/CD integration
- **HTML**: For detailed analysis
- **Term**: For console output
- **Historical**: For trend analysis

## 🚀 Deployment Process

### Pre-Deployment Checklist
- [ ] All tests pass with coverage >=20%
- [ ] E2E test passes (validates user journey)
- [ ] Integration tests pass (validates API)
- [ ] Code quality checks pass (linting, formatting)

### Deployment Steps
1. **Push to main branch**
2. **Comprehensive test suite runs**
3. **All tests must pass with coverage**
4. **Deployment to Fly.io**
5. **Post-deployment validation**
6. **Health check confirms deployment**

### Post-Deployment Validation
- **Health check**: Service responds correctly
- **Post-deploy test**: Live site works like local development
- **User experience**: Complete journey works on deployed service

## 🔧 Local Development

### Running Tests Locally
```bash
# Run all tests with coverage
python -m pytest tests/ -v --cov=app --cov-report=html

# Run specific test
python -m pytest tests/test_e2e_functional.py::test_complete_user_experience -v -s

# Run post-deploy test (against live site)
python -m pytest tests/test_post_deploy.py::test_deployed_service_complete_user_experience -v -s
```

### Pre-Push Checklist
- [ ] All tests pass locally
- [ ] Coverage >=20%
- [ ] E2E test passes
- [ ] Code quality checks pass

## 📋 Important Notes

### For Developers
- **Never skip tests** - they validate critical functionality
- **E2E test is most important** - it validates user experience
- **Coverage must be maintained** - ensures code quality
- **Post-deploy test must run** - validates production deployment

### For CI/CD
- **All tests must pass** before deployment
- **Coverage must be >=20%** for deployment
- **E2E test must pass** before deployment
- **Post-deploy validation** must run after deployment

### For Deployment
- **Only deploy after tests pass** with coverage
- **Validate deployed service** with post-deploy test
- **Ensure user experience** matches local development
- **Monitor health** of deployed service

## 🎯 Success Criteria

### Test Suite Success
- ✅ All unit tests pass
- ✅ Integration tests pass
- ✅ E2E test passes
- ✅ Coverage >=20%
- ✅ Code quality checks pass

### Deployment Success
- ✅ Service deploys to Fly.io
- ✅ Health check passes
- ✅ Post-deploy test passes
- ✅ User experience works correctly
- ✅ Service is stable and responsive

## 🚨 Failure Scenarios

### Test Failures
- **Unit test failure**: Fix the specific component
- **Integration test failure**: Fix API/server issues
- **E2E test failure**: Fix user experience issues
- **Coverage below threshold**: Add more tests

### Deployment Failures
- **Deployment fails**: Check Fly.io configuration
- **Health check fails**: Check service startup
- **Post-deploy test fails**: Check deployed service
- **User experience broken**: Rollback and investigate

## 📚 Resources

### Documentation
- [GitHub Actions Workflows](.github/workflows/)
- [Test Files](tests/)
- [Coverage Reports](htmlcov/)

### Monitoring
- [Fly.io Dashboard](https://fly.io/apps/tdg-mvp)
- [GitHub Actions](https://github.com/masseyis/tdg/actions)
- [Codecov Coverage](https://codecov.io/gh/masseyis/tdg)

---

**Remember: The e2e test validates the complete user journey and is the most important test. Never deploy without it passing.**
