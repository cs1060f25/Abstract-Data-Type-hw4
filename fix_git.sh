#!/bin/bash
# Script to fix git repository by removing large CSV files
# Attribution: Created with AI assistance (Cascade)

echo "Removing large CSV files from git tracking..."

# Remove CSV files from git cache (but keep them locally)
git rm --cached *.csv

# Add the updated .gitignore
git add .gitignore

# Commit the changes
git commit -m "Remove large CSV files from repo, keep data.db for deployment"

echo ""
echo "Done! Now you can push to GitHub:"
echo "  git push origin main"
echo ""
echo "Note: CSV files are still on your local disk, just not tracked by git."
