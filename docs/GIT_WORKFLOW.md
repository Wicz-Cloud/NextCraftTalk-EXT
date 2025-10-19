# Git Workflow & Branching Strategy

This repository follows a structured Git workflow to ensure code quality, proper versioning, and collaborative development.

## Branch Structure

### Main Branches

- **`main`** - Production-ready code, always deployable
- **`develop`** - Integration branch for features, latest development changes

### Supporting Branches

- **`feature/*`** - New features (branched from `develop`)
- **`bugfix/*`** - Bug fixes (branched from `develop`)
- **`hotfix/*`** - Critical fixes for production (branched from `main`)
- **`release/*`** - Release preparation (branched from `develop`)

## Workflow

### Feature Development

```bash
# Start a new feature
git checkout develop
git pull origin develop
git checkout -b feature/amazing-feature

# Develop and commit
git add .
git commit -m "feat: add amazing feature"

# Push feature branch
git push origin feature/amazing-feature

# Create Pull Request to develop
```

### Release Process

```bash
# Create release branch from develop
git checkout develop
git pull origin develop
git checkout -b release/v1.1.0

# Final testing and bug fixes
# Update version numbers
# Update CHANGELOG.md

# Merge to main and develop
git checkout main
git merge release/v1.1.0
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin main --tags

git checkout develop
git merge release/v1.1.0
git push origin develop

# Delete release branch
git branch -d release/v1.1.0
```

### Hotfix Process

```bash
# Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug

# Fix the issue
git add .
git commit -m "fix: critical bug in production"

# Merge back to main and develop
git checkout main
git merge hotfix/critical-bug
git tag -a v1.0.1 -m "Hotfix v1.0.1"
git push origin main --tags

git checkout develop
git merge hotfix/critical-bug
git push origin develop

# Delete hotfix branch
git branch -d hotfix/critical-bug
```

## Commit Conventions

This project follows [Conventional Commits](https://conventionalcommits.org/):

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Testing changes
- `chore:` - Maintenance tasks

Examples:
- `feat: add user authentication`
- `fix: resolve memory leak in cache manager`
- `docs: update API documentation`
- `refactor: simplify database connection logic`

## Pull Request Guidelines

### Before Submitting
- [ ] Branch is up to date with base branch
- [ ] All tests pass
- [ ] Code follows project style guidelines
- [ ] Commit messages follow conventional format
- [ ] Documentation updated if needed

### PR Template
- **Title**: Clear, descriptive title following commit conventions
- **Description**: What changes were made and why
- **Testing**: How the changes were tested
- **Breaking Changes**: Any breaking changes and migration notes

## Branch Protection

The following branches have protection rules:

### `main` Branch
- ✅ Require pull request reviews (1 reviewer minimum)
- ✅ Require status checks to pass
- ✅ Require branches to be up to date before merging
- ✅ Include administrators in restrictions
- ✅ Restrict pushes that create matching branches

### `develop` Branch
- ✅ Require pull request reviews (1 reviewer minimum)
- ✅ Require status checks to pass
- ✅ Require branches to be up to date before merging

## Release Management

### Versioning
This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes (backward compatible)

### Release Checklist
- [ ] Update version in `src/__init__.py`
- [ ] Update `CHANGELOG.md` with release notes
- [ ] Run full test suite
- [ ] Create git tag
- [ ] Create GitHub release
- [ ] Deploy to production
- [ ] Update documentation

## Code Quality Gates

### Pre-commit Hooks
- Code formatting (black)
- Import sorting (isort)
- Linting (flake8, ruff)
- Type checking (mypy)
- Security scanning (bandit)

### CI/CD Pipeline
- Automated testing on all PRs
- Code quality checks
- Security vulnerability scanning
- Docker image building
- Deployment to staging/production

## Getting Started

```bash
# Clone the repository
git clone https://github.com/Wicz-Cloud/NextCraftTalk-EXT.git
cd NextCraftTalk-EXT

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run pre-commit hooks
pre-commit install

# Create feature branch
git checkout -b feature/your-feature-name
```
