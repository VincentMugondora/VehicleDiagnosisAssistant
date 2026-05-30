# Fix Git Push - Remove API Key from History

## The Problem
Old commit `f00e081` contains your API key in documentation files. GitHub won't let you push.

## SOLUTION 1: Use GitHub's Allow Feature (Try This First!)

1. **Open this link in your browser:**
   ```
   https://github.com/VincentMugondora/VehicleDiagnosisAssistant/security/secret-scanning/unblock-secret/3ER4IJzWL7QOZVvNFG9TO6pDf17
   ```

2. **Click "Allow secret" button**

3. **Run in terminal:**
   ```bash
   git push
   ```

That's it! ✅

---

## SOLUTION 2: If Link Doesn't Work - Rewrite History

### Windows PowerShell Commands:

```powershell
# Step 1: Create backup
git branch backup-before-fix

# Step 2: Use git filter-repo (better than filter-branch)
# Install git-filter-repo first:
pip install git-filter-repo

# Step 3: Create replacements file
@"
your-cohere-api-key-here==>your-cohere-api-key-here
"@ | Out-File -Encoding utf8 replacements.txt

# Step 4: Run filter-repo
git filter-repo --replace-text replacements.txt --force

# Step 5: Force push
git push --force origin master
```

---

## SOLUTION 3: Quick & Dirty - Squash and Restart

If both above fail, start fresh (keeps all current code):

```powershell
# Backup current work
cd ..
cp -r VehicleDiagnosisAssistant VehicleDiagnosisAssistant-backup

# Go back
cd VehicleDiagnosisAssistant

# Delete .git and restart
rm -r -fo .git
git init
git add .
git commit -m "Initial commit with auto-learn feature"
git branch -M master
git remote add origin https://github.com/VincentMugondora/VehicleDiagnosisAssistant.git
git push -f origin master
```

---

## Which One Should I Use?

1. **Try Solution 1 first** (click GitHub link)
2. If that fails, **use Solution 3** (quickest for Windows)
3. Solution 2 only if you need to preserve exact git history

---

## After Fixing

Make sure `.env` is in `.gitignore`:
```bash
echo ".env" >> .gitignore
git add .gitignore
git commit -m "chore: ensure .env is ignored"
git push
```

✅ Done!
