#!/bin/bash
# Fix git history by removing API key from old commit

echo "🔧 Fixing git history to remove API key..."

# Backup current branch
git branch backup-$(date +%Y%m%d) 2>/dev/null || true

# Use filter-branch to replace the API key in ALL commits
git filter-branch --force --tree-filter '
  if [ -f .env.example ]; then
    sed -i "s/your-cohere-api-key-here/your-cohere-api-key-here/g" .env.example
  fi
  if [ -f COHERE_MIGRATION_SUMMARY.md ]; then
    sed -i "s/your-cohere-api-key-here/your-cohere-api-key-here/g" COHERE_MIGRATION_SUMMARY.md
  fi
  if [ -f COHERE_SETUP.md ]; then
    sed -i "s/your-cohere-api-key-here/your-cohere-api-key-here/g" COHERE_SETUP.md
  fi
  if [ -f QUICKSTART.md ]; then
    sed -i "s/your-cohere-api-key-here/your-cohere-api-key-here/g" QUICKSTART.md
  fi
  if [ -f START_HERE.md ]; then
    sed -i "s/your-cohere-api-key-here/your-cohere-api-key-here/g" START_HERE.md
  fi
' -- --all

echo "✅ History rewritten"
echo "⚠️  WARNING: This rewrote git history"
echo "💡 To push: git push --force"
