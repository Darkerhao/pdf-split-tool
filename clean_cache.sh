#!/bin/bash
# Clean Python cache files and directories

echo "Cleaning Python cache files..."

# Remove __pycache__ directories
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Remove .pyc files
find . -name "*.pyc" -delete 2>/dev/null

# Remove .pyo files
find . -name "*.pyo" -delete 2>/dev/null

# Remove .pytest_cache
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null

echo "✓ Cleaned all Python cache files"
echo "Remaining __pycache__ directories: $(find . -type d -name '__pycache__' 2>/dev/null | wc -l)"
