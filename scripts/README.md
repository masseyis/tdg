# Scripts Directory

This directory contains utility scripts for development, testing, and deployment.

## Pre-Push Analysis Script

### `pre_push_analysis.py`

**Purpose**: Performs comprehensive analysis of git changes before pushing to ensure code quality and proper documentation.

**Features**:
- 🔍 **Git Diff Analysis**: Analyzes all staged changes
- 🏗️ **Architectural Change Detection**: Identifies significant code changes
- 📝 **Auto-Documentation**: Updates `ARCHITECTURAL_CHANGES.md`
- 🧪 **Test Validation**: Runs test suite to ensure changes work
- 📋 **Change Summary**: Provides detailed summary of modifications

**Usage**:
```bash
python scripts/pre_push_analysis.py
```

**What it does**:
1. **Analyzes git diff** for architectural changes
2. **Identifies patterns** in code modifications
3. **Updates documentation** with change summaries
4. **Runs test suite** to validate changes
5. **Provides feedback** on what needs manual review

**Auto-detected Changes**:
- New API endpoints
- Database schema changes
- Frontend modifications
- Configuration updates
- Test additions
- Documentation changes

**Output**:
- Updates `ARCHITECTURAL_CHANGES.md` with new entries
- Provides console summary of changes
- Runs tests and reports results
- Gives guidance on what to review manually

## Git Hooks

### Pre-Push Hook

**Location**: `.git/hooks/pre-push`

**Purpose**: Automatically runs pre-push analysis before every `git push`

**What it does**:
- Runs `pre_push_analysis.py` automatically
- Prevents push if analysis fails
- Ensures code quality and documentation standards

**Setup**:
```bash
# Make sure the hook is executable
chmod +x .git/hooks/pre-push
```

## Manual Usage

### Running Analysis Manually

If you want to run the analysis without pushing:

```bash
# Run analysis on current changes
python scripts/pre_push_analysis.py

# Check what would be documented
python scripts/pre_push_analysis.py --dry-run
```

### Bypassing Analysis (Not Recommended)

If you absolutely need to bypass the analysis:

```bash
# Skip the pre-push hook (use with caution)
git push --no-verify
```

**Warning**: Only use `--no-verify` in emergencies. The analysis helps maintain code quality and documentation standards.

## Configuration

### Customizing Analysis

You can modify `pre_push_analysis.py` to:

- **Add new file patterns** to detect
- **Customize change categories**
- **Modify test commands**
- **Adjust documentation format**

### Adding New Scripts

When adding new scripts:

1. **Document the purpose** in this README
2. **Add usage examples**
3. **Include error handling**
4. **Make scripts executable**
5. **Test thoroughly**

## Best Practices

### For Developers

1. **Run analysis frequently** during development
2. **Review auto-generated documentation**
3. **Fill in missing details** in architectural changes
4. **Fix test failures** before pushing
5. **Update documentation** as needed

### For Code Review

1. **Check architectural changes** are documented
2. **Verify tests pass** consistently
3. **Review change summaries** for accuracy
4. **Ensure proper categorization** of changes
5. **Validate migration steps** if applicable

## Troubleshooting

### Common Issues

**Script not executable**:
```bash
chmod +x scripts/pre_push_analysis.py
```

**Git hook not working**:
```bash
chmod +x .git/hooks/pre-push
```

**Tests failing**:
- Fix the failing tests
- Ensure all dependencies are installed
- Check test configuration

**Documentation not updating**:
- Ensure `ARCHITECTURAL_CHANGES.md` exists
- Check file permissions
- Verify script has write access

### Getting Help

If you encounter issues:

1. **Check the script output** for error messages
2. **Review the git diff** manually
3. **Run tests individually** to isolate issues
4. **Check file permissions** and paths
5. **Consult the main README** for project setup

---

**Remember**: These scripts help maintain code quality and documentation standards. Use them regularly and keep them updated as the project evolves.
