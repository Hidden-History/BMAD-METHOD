#!/bin/bash
# Quick setup script for BMAD memory system environment

echo "Setting up BMAD Memory System environment..."
echo ""

# Copy .env.example to .env
if [ ! -f "src/.env" ]; then
    cp src/.env.example src/.env
    echo "✅ Created src/.env from src/.env.example"
else
    echo "ℹ️  src/.env already exists"
fi

# Verify configuration
echo ""
echo "Current configuration:"
cat src/.env | grep QDRANT_URL

echo ""
echo "✅ Setup complete!"
echo ""
echo "Database dashboard: http://localhost:16350/dashboard#/collections"
echo ""
echo "Ready to run PM agent workflow!"
