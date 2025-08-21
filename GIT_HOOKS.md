# Git Hooks

This repository includes Git hooks to ensure code quality and prevent broken code from being pushed to the repository.

## Available Hooks

### Pre-push Hook

**File**: `.git/hooks/pre-push`

**Purpose**: Runs the full CI test suite before allowing a push to the remote repository.

**What it does**:
- Runs `make test-ci` which includes:
  - Python tests with pytest
  - Code coverage reporting
  - Linting checks (flake8)
  - Code formatting checks (black)

**Behavior**:
- ✅ **If tests pass**: Push proceeds normally
- ❌ **If tests fail**: Push is blocked with helpful error message

## Installation

The hooks are automatically installed when you clone the repository. If you need to reinstall them:

```bash
# Make sure the hook is executable
chmod +x .git/hooks/pre-push
```

## Manual Testing

You can test the pre-push hook manually:

```bash
# Test the hook directly
.git/hooks/pre-push

# Or simulate a push (without actually pushing)
git push --dry-run
```

## Bypassing Hooks (Emergency Only)

If you absolutely need to bypass the hooks in an emergency:

```bash
# Skip pre-push hook
git push --no-verify

# Skip all hooks
git push --no-verify --no-hooks
```

⚠️ **Warning**: Only use this in emergencies. The hooks are there to maintain code quality.

## Troubleshooting

### Hook Not Running

1. Check if the hook is executable:
   ```bash
   ls -la .git/hooks/pre-push
   ```

2. Reinstall the hook:
   ```bash
   chmod +x .git/hooks/pre-push
   ```

### Tests Failing Locally

If the hook blocks your push due to failing tests:

1. Run the tests manually to see the issues:
   ```bash
   make test-ci
   ```

2. Fix the failing tests

3. Try the push again

### Linting Issues

The CI pipeline is configured to be lenient with linting issues, but you can still see them:

```bash
# Run linting only
flake8 app/ --max-line-length=88 --extend-ignore=E203,W503

# Run formatting check only
black --check app/
```

## Adding New Hooks

To add additional Git hooks:

1. Create the hook file in `.git/hooks/`
2. Make it executable: `chmod +x .git/hooks/hook-name`
3. Update this documentation

Common hook names:
- `pre-commit` - Runs before commit
- `pre-push` - Runs before push (already implemented)
- `post-merge` - Runs after merge
- `post-checkout` - Runs after checkout

## Best Practices

1. **Always run tests locally** before pushing
2. **Don't bypass hooks** unless absolutely necessary
3. **Fix failing tests** rather than disabling hooks
4. **Keep hooks lightweight** - they should run quickly
5. **Provide clear error messages** when hooks fail
