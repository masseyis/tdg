#!/bin/bash

# Install Git hooks for the Test Data Generator project
# This script sets up pre-push hooks to ensure code quality

set -e

echo "🔧 Installing Git hooks..."

# Get the repository root directory
REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

# Create hooks directory if it doesn't exist
mkdir -p "$HOOKS_DIR"

# Install pre-push hook
cat > "$HOOKS_DIR/pre-push" << 'EOF'
#!/bin/bash

# Git pre-push hook to run tests before pushing
# This ensures code quality is maintained locally

echo "🔍 Running pre-push checks..."

# Change to the repository root directory
cd "$(git rev-parse --show-toplevel)"

# Run the CI test suite
echo "🧪 Running test suite..."
if ! make test-ci; then
    echo ""
    echo "❌ Pre-push checks failed!"
    echo "   Please fix the failing tests before pushing."
    echo "   Run 'make test-ci' locally to see the issues."
    echo ""
    exit 1
fi

echo ""
echo "✅ Pre-push checks passed!"
echo "   Ready to push to remote repository."
echo ""
exit 0
EOF

# Make the hook executable
chmod +x "$HOOKS_DIR/pre-push"

echo "✅ Pre-push hook installed successfully!"
echo ""
echo "The hook will now run 'make test-ci' before every push."
echo "If tests fail, the push will be blocked."
echo ""
echo "To test the hook manually:"
echo "  .git/hooks/pre-push"
echo ""
echo "To bypass the hook in emergencies:"
echo "  git push --no-verify"
echo ""
echo "See GIT_HOOKS.md for more information."
