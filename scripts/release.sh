#!/bin/bash
# Release script for HVX CLI
# Usage: ./scripts/release.sh <version>

set -e

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "❌ Error: Version number required"
    echo "Usage: ./scripts/release.sh <version>"
    echo "Example: ./scripts/release.sh 0.2.0"
    exit 1
fi

# Validate version format (semantic versioning)
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Error: Invalid version format. Use semantic versioning (e.g., 0.2.0)"
    exit 1
fi

echo "🚀 Starting release process for version $VERSION"

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "⚠️  Warning: Not on main branch (current: $CURRENT_BRANCH)"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo "❌ Error: Uncommitted changes detected. Please commit or stash them first."
    git status -s
    exit 1
fi

# Update version in setup.py
echo "📝 Updating version in setup.py..."
sed -i.bak "s/version='[^']*'/version='$VERSION'/" setup.py && rm setup.py.bak

# Update version in __init__.py
echo "📝 Updating version in src/__init__.py..."
if [ ! -f src/__init__.py ]; then
    echo "__version__ = '$VERSION'" > src/__init__.py
else
    if grep -q "__version__" src/__init__.py; then
        sed -i.bak "s/__version__ = '[^']*'/__version__ = '$VERSION'/" src/__init__.py && rm src/__init__.py.bak
    else
        echo "__version__ = '$VERSION'" >> src/__init__.py
    fi
fi

# Run tests if they exist
if [ -f "tests/test_hvx_workflow.sh" ]; then
    echo "🧪 Running tests..."
    bash tests/test_hvx_workflow.sh || {
        echo "❌ Tests failed. Aborting release."
        git checkout setup.py src/__init__.py
        exit 1
    }
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Build package
echo "📦 Building package..."
python -m build || {
    echo "❌ Build failed. Aborting release."
    git checkout setup.py src/__init__.py
    exit 1
}

# Check distribution
echo "✅ Checking distribution..."
python -m twine check dist/* || {
    echo "❌ Distribution check failed. Aborting release."
    git checkout setup.py src/__init__.py
    exit 1
}

# Show what will be released
echo ""
echo "📋 Release Summary:"
echo "  Version: $VERSION"
echo "  Tag: v$VERSION"
echo "  Files to upload:"
ls -lh dist/
echo ""

# Confirm release
read -p "Ready to release? This will commit, tag, and upload to PyPI. (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Release cancelled."
    git checkout setup.py src/__init__.py
    exit 1
fi

# Commit version changes
echo "💾 Committing version changes..."
git add setup.py src/__init__.py
git commit -m "Bump version to $VERSION"

# Create and push tag
echo "🏷️  Creating tag v$VERSION..."
git tag "v$VERSION"

# Upload to PyPI
echo "📤 Uploading to PyPI..."
python -m twine upload dist/* || {
    echo "❌ PyPI upload failed."
    echo "⚠️  Tag and commit created but not pushed."
    echo "To retry: python -m twine upload dist/*"
    exit 1
}

# Push to GitHub (this will trigger the GitHub Action)
echo "🚀 Pushing to GitHub..."
git push origin main
git push origin "v$VERSION"

echo ""
echo "✅ Release complete!"
echo ""
echo "📦 Package published to PyPI: https://pypi.org/project/hvx/$VERSION/"
echo "🏷️  GitHub tag: https://github.com/bruadam/hvx/releases/tag/v$VERSION"
echo ""
echo "Next steps:"
echo "  1. Wait a few minutes for GitHub Actions to complete"
echo "  2. Check GitHub releases for the automated release notes"
echo "  3. If you have a Homebrew tap, the formula will be auto-updated"
echo "  4. Test installation: pip install --upgrade hvx"
echo ""
