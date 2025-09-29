# Deployment Guide for HW4

## Problem: Git Push Failed Due to Large Files

The CSV files are too large for GitHub (30MB combined). Solution: exclude them from git, keep only `data.db`.

## Step-by-Step Fix and Deployment

### Step 1: Fix Git Repository

Run the fix script to remove CSV files from git tracking:

```bash
chmod +x fix_git.sh
./fix_git.sh
```

Or manually:
```bash
# Remove CSV files from git (keeps them locally)
git rm --cached *.csv

# Stage the updated .gitignore
git add .gitignore

# Commit
git commit -m "Remove large CSV files, keep data.db for deployment"

# Push to GitHub
git push origin main
```

### Step 2: Verify Repository Contents

Your GitHub repo should contain:
- ✅ `csv_to_sqlite.py`
- ✅ `data.db` (32MB - within GitHub limits)
- ✅ `api/county_data.py`
- ✅ `api/__init__.py`
- ✅ `requirements.txt`
- ✅ `vercel.json`
- ✅ `.gitignore`
- ✅ `README.md`
- ✅ `link.txt`
- ❌ `*.csv` files (excluded, too large)

### Step 3: Deploy to Vercel

#### Option A: Vercel CLI (Recommended)

```bash
# Install Vercel CLI (if not installed)
npm i -g vercel

# Login to Vercel
vercel login

# Deploy from project directory
cd /Users/asharma/Abstract-Data-Type-hw4
vercel --prod
```

Follow the prompts:
- Set up and deploy? **Y**
- Which scope? Select your account
- Link to existing project? **N**
- Project name? (accept default or customize)
- Directory? `.` (current directory)
- Override settings? **N**

#### Option B: Vercel Web Dashboard

1. Go to https://vercel.com
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Vercel will auto-detect the configuration
5. Click "Deploy"

### Step 4: Update link.txt

After deployment, Vercel will give you a URL like:
```
https://your-project-name.vercel.app
```

Update `link.txt` with your endpoint URL:
```
https://your-project-name.vercel.app/county_data
```

Then commit and push:
```bash
git add link.txt
git commit -m "Add deployment URL"
git push origin main
```

### Step 5: Test Your Deployed API

```bash
# Test with your actual URL
curl -X POST https://your-project-name.vercel.app/county_data \
  -H "Content-Type: application/json" \
  -d '{"zip": "02138", "measure_name": "Adult obesity"}'
```

Or use the test script:
```bash
./test_api.sh https://your-project-name.vercel.app
```

## Troubleshooting

### Issue: Vercel deployment fails with "data.db not found"

**Solution:** Ensure `data.db` is committed to git:
```bash
git add data.db
git commit -m "Add database for deployment"
git push origin main
```

### Issue: API returns 500 error

**Possible causes:**
1. `data.db` not included in deployment
2. Database path issue in code
3. Check Vercel logs: `vercel logs`

### Issue: Still can't push to GitHub

If `data.db` is also too large for your GitHub plan:

**Alternative approach:**
1. Use Git LFS (Large File Storage)
2. Or deploy without GitHub:
   ```bash
   vercel --prod
   # Vercel will deploy from local directory
   ```

## Important Notes

- ✅ CSV files stay on your local machine (needed for grading)
- ✅ `data.db` is in the repo (needed for API to work)
- ✅ Graders will run `csv_to_sqlite.py` on their own CSV files
- ✅ Your deployed API must work with the existing `data.db`

## Submission Checklist

Before submitting to Canvas:

- [ ] GitHub repo created in cs1060f25 organization as `<username>-hw4`
- [ ] All required files present (see README.md)
- [ ] `link.txt` contains actual deployment URL
- [ ] Deployment is live and accessible
- [ ] API tested with all test cases (200, 400, 404, 418)
- [ ] CSV source files available locally (for grader testing)

## Canvas Submission

Submit the GitHub repository URL to Canvas:
```
https://github.com/cs1060f25/<username>-hw4
```

The graders will:
1. Clone your repo
2. Test `csv_to_sqlite.py` with original and new CSV files
3. Test your deployed API via the URL in `link.txt`
4. Attempt SQL injection (after other tests)
