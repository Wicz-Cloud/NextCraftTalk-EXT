# Release Process

This document outlines the process for creating new releases of the Minecraft AI Chatbot.

## Versioning Strategy

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., `1.2.3`)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## Release Types

### Major Release (X.0.0)
- Breaking changes
- Major feature additions
- API changes
- Requires migration guide

### Minor Release (x.X.0)
- New features
- Enhancements
- Backward compatible
- No migration required

### Patch Release (x.x.X)
- Bug fixes
- Security updates
- Performance improvements
- Documentation updates

## Release Process

### 1. Preparation

#### Manual Steps
- [ ] Review open issues and PRs
- [ ] Check CI/CD pipeline status
- [ ] Review security scan results
- [ ] Update dependencies if needed

#### Automated Checks
- [ ] All tests pass
- [ ] Code quality checks pass
- [ ] Security scans pass
- [ ] Docker build succeeds

### 2. Create Release Branch

```bash
# From develop branch
git checkout develop
git pull origin develop
git checkout -b release/v1.1.0
```

### 3. Update Version and Documentation

#### Update Version
```bash
# Edit src/__init__.py
__version__ = "1.1.0"
```

#### Update CHANGELOG.md
```markdown
## [1.1.0] - YYYY-MM-DD

### Added
- New feature description

### Changed
- Enhancement description

### Fixed
- Bug fix description

### Security
- Security improvement description
```

### 4. Testing and Validation

```bash
# Run full test suite
pytest

# Run pre-commit checks
pre-commit run --all-files

# Test Docker build
docker-compose build

# Manual testing
# - Deploy to staging environment
# - Test critical user flows
# - Verify integrations work
```

### 5. Create Release

#### Git Operations
```bash
# Commit version changes
git add .
git commit -m "chore: prepare release v1.1.0"

# Merge to main
git checkout main
git pull origin main
git merge release/v1.1.0

# Create annotated tag
git tag -a v1.1.0 -m "Release v1.1.0

## What's New
- Feature 1
- Feature 2
- Bug fixes

## Breaking Changes
- None

## Migration Guide
- No migration required"

# Push to main with tags
git push origin main --tags

# Merge back to develop
git checkout develop
git merge main
git push origin develop

# Clean up release branch
git branch -d release/v1.1.0
```

#### GitHub Release
1. Go to [Releases](https://github.com/Wicz-Cloud/NextCraftTalk-EXT/releases)
2. Click "Create a new release"
3. Select the new tag (v1.1.0)
4. Title: "Release v1.1.0"
5. Copy changelog content to description
6. Attach any relevant binaries/assets
7. Publish release

### 6. Post-Release Tasks

#### Automated (via CI/CD)
- Docker images are built and tagged
- Release is created on GitHub
- Notifications sent (if configured)

#### Manual Tasks
- [ ] Update documentation website (if applicable)
- [ ] Notify stakeholders
- [ ] Update deployment environments
- [ ] Monitor for issues post-release
- [ ] Close related issues/PRs

## Hotfix Releases

For critical bugs in production:

```bash
# Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug-v1.0.1

# Fix the bug
# Update version to 1.0.1
# Update CHANGELOG.md

# Commit and test
git add .
git commit -m "fix: critical bug description"

# Merge to main
git checkout main
git merge hotfix/critical-bug-v1.0.1
git tag -a v1.0.1 -m "Hotfix v1.0.1"
git push origin main --tags

# Merge to develop
git checkout develop
git merge main
git push origin develop

# Clean up
git branch -d hotfix/critical-bug-v1.0.1
```

## Rollback Process

If a release needs to be rolled back:

1. Identify the problematic release
2. Create a new release that reverts the changes
3. Update version (patch increment)
4. Document the rollback in CHANGELOG.md
5. Notify users of the rollback

## Release Checklist

### Pre-Release
- [ ] All PRs merged and approved
- [ ] CI/CD pipeline passes
- [ ] Security scans pass
- [ ] Dependencies updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers updated

### Release
- [ ] Release branch created
- [ ] Code tested and validated
- [ ] Release merged to main
- [ ] Git tag created
- [ ] GitHub release created
- [ ] Docker images built

### Post-Release
- [ ] Release branch deleted
- [ ] Develop branch updated
- [ ] Stakeholders notified
- [ ] Issues/PRs closed
- [ ] Monitoring active

## Release Cadence

- **Major releases**: As needed (breaking changes)
- **Minor releases**: Monthly (new features)
- **Patch releases**: As needed (bug fixes)
- **Hotfixes**: As needed (critical issues)

## Communication

- Release notes posted in CHANGELOG.md
- GitHub releases for each version
- Announcements in relevant channels
- Migration guides for breaking changes
