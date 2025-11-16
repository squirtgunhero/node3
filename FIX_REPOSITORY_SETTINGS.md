# Fix Repository Settings for GitHub Actions

The workflow keeps failing with "Resource not accessible by integration" despite having `permissions: contents: write`. This means the repository settings might be restricting workflow permissions.

## Step 1: Check Repository Settings (CRITICAL)

Go to your repository settings and verify workflow permissions:

### URL to Check:
```
https://github.com/squirtgunhero/node3/settings/actions
```

### What to Look For:

1. **Scroll to "Workflow permissions" section**
2. **Select "Read and write permissions"** (NOT "Read repository contents and packages permissions")
3. **Check the box**: ☑️ "Allow GitHub Actions to create and approve pull requests"
4. **Click "Save"**

### Screenshot Guide:

```
Workflow permissions
○ Read repository contents and packages permissions (default)
● Read and write permissions  ← SELECT THIS ONE

☑️ Allow GitHub Actions to create and approve pull requests  ← CHECK THIS
```

## Step 2: Alternative - Use Personal Access Token (If Above Doesn't Work)

If repository settings can't be changed (org restrictions), use a PAT:

### Create PAT:

1. Go to: https://github.com/settings/tokens/new
2. Token name: `node3-releases`
3. Expiration: 90 days (or custom)
4. Select scopes:
   - ☑️ `repo` (Full control of private repositories)
   - ☑️ `write:packages` (Upload packages)
5. Click "Generate token"
6. **COPY THE TOKEN** (you won't see it again!)

### Add Token to Repository:

1. Go to: https://github.com/squirtgunhero/node3/settings/secrets/actions
2. Click "New repository secret"
3. Name: `RELEASE_TOKEN`
4. Value: Paste the token you copied
5. Click "Add secret"

### Update Workflow to Use PAT:

I'll create a script to do this automatically...

## Step 3: Verify Actions Are Enabled

Ensure Actions are enabled:

1. Go to: https://github.com/squirtgunhero/node3/settings/actions
2. Under "Actions permissions":
   - ☑️ "Allow all actions and reusable workflows" should be selected
3. Click "Save"

## Why This Happens

GitHub recently changed default workflow permissions to be read-only for security. Even with `permissions: contents: write` in the workflow, the repository-level setting can override it.

## Test After Fixing

After changing repository settings OR adding the PAT:

```bash
cd ~/Desktop/node3agent

# Delete and recreate the tag
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0

# Wait 5 seconds
sleep 5

# Recreate and push
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

## Expected Result

After fixing, you should see in the Actions logs:

✅ "Creating release" or "Updating release"
✅ "Uploading assets"
✅ Green checkmarks on all jobs

NOT:
❌ "Resource not accessible by integration"
❌ "HttpError: 403"

