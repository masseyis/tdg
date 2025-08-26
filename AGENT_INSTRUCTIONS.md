# AI Agent Instructions

## 🧪 Testing Requirements

### ALWAYS Keep Test Functions Complete
- **NEVER disable or skip tests** - if a test is failing, fix the underlying issue
- **NEVER comment out test code** - tests are critical for validation
- **NEVER use `@pytest.mark.skip`** - tests must run and pass
- **NEVER use `# TODO: fix test`** - fix the test immediately

### Favor Selenium Tests for UI Changes
- **UI functionality MUST be tested with Selenium** - no exceptions
- **E2E tests are the most important** - they validate the complete user experience
- **Selenium tests drive the UI** - don't bypass UI by calling APIs directly
- **Test the actual user workflow** - not just individual components

### Test-Driven Development
- **Write tests FIRST** before implementing features
- **Use tests to validate changes** - run tests after every change
- **Tests must pass before committing** - no exceptions
- **If tests fail, fix them immediately** - don't proceed without passing tests

### Test Coverage Requirements
- **E2E tests for all user workflows** - complete user journeys
- **Unit tests for business logic** - core functionality
- **Integration tests for API endpoints** - backend functionality
- **Visual regression tests** - UI appearance and behavior

## 📋 Pre-Push Requirements

### Git Diff Analysis
Before every `git push`, perform these steps:

1. **Run `git diff`** to review all changes
2. **Identify architectural changes** - look for:
   - New files or major file modifications
   - Changes to core functionality
   - Database schema changes
   - API endpoint modifications
   - Frontend architecture changes
   - Configuration changes

3. **Document architectural changes** in `ARCHITECTURAL_CHANGES.md`:
   - Summary of what changed
   - Why the change was made
   - Pros and cons of the approach
   - Impact on existing functionality
   - Migration considerations

### Test Suite Validation
Before every `git push`:

1. **Run the complete test suite** - all tests must pass
2. **Run E2E tests** - validate complete user workflows
3. **Check test coverage** - ensure adequate coverage
4. **Validate CI/CD pipeline** - ensure tests will pass in CI

## 🏗️ Architectural Documentation

### Document Major Changes
For any significant architectural change:

1. **Create/update `ARCHITECTURAL_CHANGES.md`**
2. **Include change summary**:
   - What was changed
   - Why it was changed
   - How it was implemented
   - Impact on existing code

3. **Document pros and cons**:
   - Benefits of the new approach
   - Potential drawbacks or risks
   - Performance implications
   - Maintenance considerations

4. **Update relevant documentation**:
   - README files
   - API documentation
   - Deployment guides
   - User guides

## 🔄 Workflow Requirements

### Before Making Changes
1. **Understand the current architecture**
2. **Identify what needs to be tested**
3. **Plan the testing approach**
4. **Consider impact on existing functionality**

### During Development
1. **Write tests first** (TDD approach)
2. **Run tests frequently** - after every significant change
3. **Validate with E2E tests** - ensure UI works end-to-end
4. **Document architectural decisions** - as you make them

### Before Committing
1. **Run complete test suite** - all tests must pass
2. **Review git diff** - understand all changes
3. **Document architectural changes** - if any
4. **Update documentation** - if needed

### Before Pushing
1. **Final test run** - ensure everything works
2. **Architectural review** - document major changes
3. **Documentation update** - ensure docs are current
4. **CI/CD validation** - ensure pipeline will succeed

## 🚨 Critical Rules

### NEVER
- Disable or skip tests
- Bypass UI testing for UI features
- Push code without running tests
- Make architectural changes without documentation
- Ignore test failures

### ALWAYS
- Keep tests complete and passing
- Use Selenium for UI testing
- Document architectural changes
- Run tests before pushing
- Validate end-to-end functionality

## 📝 Documentation Standards

### Architectural Changes
- Clear summary of what changed
- Rationale for the change
- Pros and cons analysis
- Impact assessment
- Migration notes (if applicable)

### Test Documentation
- Clear test descriptions
- Expected behavior documentation
- Test data requirements
- Setup and teardown procedures

### Code Comments
- Explain complex logic
- Document business rules
- Note important assumptions
- Reference related issues or requirements

## 🎯 Success Metrics

### Testing Success
- All tests pass consistently
- E2E tests validate complete workflows
- Test coverage meets requirements
- No test failures in CI/CD

### Documentation Success
- Architectural changes are documented
- Pros and cons are clearly stated
- Impact is well understood
- Migration paths are clear

### Code Quality Success
- Changes are well-tested
- Architecture is well-documented
- Code is maintainable
- Performance is acceptable

---

**Remember**: Tests are not optional - they are the foundation of reliable software. Always favor comprehensive testing over quick fixes, and always document architectural decisions for future reference.
