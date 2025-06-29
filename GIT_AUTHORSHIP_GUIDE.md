# Git Authorship Change Guide

## Overview
This guide provides instructions to change Git commit authorship for all commits in the repository to "theoneste2060".

## Prerequisites
- Git installed on your system
- Access to the repository
- Command line/terminal access

## Method 1: Filter-Branch (Recommended for Complete History Rewrite)

### Step 1: Backup Your Repository
```bash
# Create a backup of your repository
git clone --bare https://github.com/your-username/your-repo.git repo-backup.git
```

### Step 2: Configure Git User Information
```bash
git config --global user.name "theoneste2060"
git config --global user.email "theoneste2060@gmail.com"
```

### Step 3: Rewrite Commit History
```bash
git filter-branch --env-filter '
OLD_EMAIL="*"
CORRECT_NAME="theoneste2060"
CORRECT_EMAIL="theoneste2060@gmail.com"

if [ "$GIT_COMMITTER_EMAIL" != "$CORRECT_EMAIL" ]
then
    export GIT_COMMITTER_NAME="$CORRECT_NAME"
    export GIT_COMMITTER_EMAIL="$CORRECT_EMAIL"
fi
if [ "$GIT_AUTHOR_EMAIL" != "$CORRECT_EMAIL" ]
then
    export GIT_AUTHOR_NAME="$CORRECT_NAME"
    export GIT_AUTHOR_EMAIL="$CORRECT_EMAIL"
fi
' --tag-name-filter cat -- --branches --tags
```

### Step 4: Force Push Changes
```bash
git push --force --tags origin 'refs/heads/*'
```

## Method 2: Interactive Rebase (For Recent Commits)

### Change Last N Commits
```bash
# For last 5 commits
git rebase -i HEAD~5

# In the editor, change 'pick' to 'edit' for commits you want to modify
# Then for each commit:
git commit --amend --author="theoneste2060 <theoneste2060@gmail.com>" --no-edit
git rebase --continue
```

## Method 3: BFG Repo-Cleaner (Alternative Tool)

### Install BFG
```bash
# Download from https://rtyley.github.io/bfg-repo-cleaner/
# Or use package manager:
brew install bfg  # macOS
```

### Use BFG to Change Authors
```bash
# Create author mapping file
echo "OLD_EMAIL=theoneste2060 <theoneste2060@gmail.com>" > authors.txt

# Run BFG
bfg --replace-text authors.txt --no-blob-protection .git
git reflog expire --expire=now --all && git gc --prune=now --aggressive
```

## Verification

### Check Commit History
```bash
# View recent commits with author information
git log --oneline --pretty="format:%h %an <%ae> %s"

# Check all authors in repository
git log --format='%aN <%aE>' | sort -u
```

### Verify Specific Commit
```bash
git show --format=fuller <commit-hash>
```

## Important Notes

### Before Making Changes
1. **Backup your repository** - This process rewrites Git history
2. **Coordinate with team** - If working with others, inform them of the change
3. **Update all clones** - All developers will need to re-clone after force push

### After Making Changes
1. **Force push required** - Normal push will be rejected due to history rewrite
2. **Update remote branches** - All remote tracking branches need updating
3. **Re-clone repositories** - Local clones of other developers become invalid

## Troubleshooting

### Common Issues

#### Protected Branch Error
```bash
# Temporarily disable branch protection
# Make changes, then re-enable protection
```

#### Large Repository Performance
```bash
# Use shallow clone for faster processing
git clone --depth 1 <repository-url>
# Then use filter-branch with --all option
```

#### Permission Denied
```bash
# Ensure you have write access to repository
# Check SSH keys or authentication tokens
```

### Recovery Options

#### Restore from Backup
```bash
# If something goes wrong, restore from backup
git clone repo-backup.git restored-repo
cd restored-repo
git push --force origin --all
```

#### Reset to Previous State
```bash
# Find previous commit before changes
git reflog
git reset --hard <previous-commit-hash>
```

## Advanced Options

### Preserve Merge Commits
```bash
git filter-branch --env-filter '...' --preserve-merges -- --all
```

### Change Specific Time Range
```bash
git filter-branch --env-filter '...' -- --since="2024-01-01" --until="2024-12-31"
```

### Change Only Specific Author
```bash
git filter-branch --env-filter '
if [ "$GIT_AUTHOR_EMAIL" = "old@example.com" ]
then
    export GIT_AUTHOR_NAME="theoneste2060"
    export GIT_AUTHOR_EMAIL="theoneste2060@gmail.com"
    export GIT_COMMITTER_NAME="theoneste2060"
    export GIT_COMMITTER_EMAIL="theoneste2060@gmail.com"
fi
' -- --all
```

## Platform-Specific Considerations

### GitHub
- Force push to update remote repository
- Update branch protection rules if necessary
- Consider creating new repository if needed

### GitLab
- May require disabling push rules temporarily
- Update merge request targets after history rewrite

### Bitbucket
- Force push updates all branches
- Team members need to re-clone repositories

## Best Practices

1. **Test on copy first** - Always test the process on a repository copy
2. **Document changes** - Keep record of what was changed and when
3. **Communicate clearly** - Inform all team members about the change
4. **Backup everything** - Multiple backups in different locations
5. **Verify results** - Double-check authorship after changes

## Alternative Approach: New Repository

If history rewrite is too risky, consider:

1. Create new repository with desired author
2. Copy current code state
3. Make initial commit with correct author
4. Archive old repository
5. Update all references to new repository

This approach preserves original history while establishing new authorship going forward.

## Security Considerations

- Changing Git history can affect commit signatures
- GPG signatures will become invalid after authorship change
- Consider re-signing commits if using signed commits
- Update any CI/CD systems that depend on specific authors

---

**Important**: This process rewrites Git history. Ensure you have proper backups and coordinate with your team before proceeding.