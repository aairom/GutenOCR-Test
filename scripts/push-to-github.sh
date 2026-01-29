#!/bin/bash

# GutenOCR GitHub Push Script
# This script automates pushing code to GitHub

set -e

echo "=========================================="
echo "GutenOCR GitHub Push Automation"
echo "=========================================="

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_prompt() {
    echo -e "${BLUE}[PROMPT]${NC} $1"
}

# Check if git is installed
if ! command -v git &> /dev/null; then
    print_error "git is not installed. Please install git first."
    exit 1
fi

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    print_warning "Not a git repository. Initializing..."
    git init
    print_info "Git repository initialized"
fi

# Parse command line arguments
COMMIT_MESSAGE=""
BRANCH="main"
REMOTE="origin"
FORCE=false
CREATE_REPO=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--message)
            COMMIT_MESSAGE="$2"
            shift 2
            ;;
        -b|--branch)
            BRANCH="$2"
            shift 2
            ;;
        -r|--remote)
            REMOTE="$2"
            shift 2
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        --create-repo)
            CREATE_REPO=true
            shift
            ;;
        --help)
            echo "Usage: ./scripts/push-to-github.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -m, --message MSG    Commit message (required if not provided interactively)"
            echo "  -b, --branch BRANCH  Branch name (default: main)"
            echo "  -r, --remote REMOTE  Remote name (default: origin)"
            echo "  -f, --force          Force push (use with caution)"
            echo "  --create-repo        Create a new GitHub repository"
            echo "  --help               Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./scripts/push-to-github.sh -m \"Initial commit\""
            echo "  ./scripts/push-to-github.sh -m \"Update docs\" -b develop"
            echo "  ./scripts/push-to-github.sh --create-repo"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Create GitHub repository if requested
if [ "$CREATE_REPO" = true ]; then
    print_info "Creating GitHub repository..."
    
    # Check if gh CLI is installed
    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI (gh) is not installed."
        print_info "Install it from: https://cli.github.com/"
        print_info "Or manually create the repository on GitHub and add the remote:"
        echo ""
        echo "  git remote add origin https://github.com/YOUR_USERNAME/GutenOCR-Test.git"
        exit 1
    fi
    
    # Check if authenticated
    if ! gh auth status &> /dev/null; then
        print_warning "Not authenticated with GitHub. Running authentication..."
        gh auth login
    fi
    
    # Create repository
    print_prompt "Enter repository name (default: GutenOCR-Test):"
    read -r REPO_NAME
    REPO_NAME=${REPO_NAME:-GutenOCR-Test}
    
    print_prompt "Make repository private? (y/N):"
    read -r PRIVATE
    
    VISIBILITY="--public"
    if [[ "$PRIVATE" =~ ^[Yy]$ ]]; then
        VISIBILITY="--private"
    fi
    
    print_prompt "Enter repository description (optional):"
    read -r DESCRIPTION
    
    DESC_FLAG=""
    if [ -n "$DESCRIPTION" ]; then
        DESC_FLAG="--description \"$DESCRIPTION\""
    fi
    
    print_info "Creating repository: $REPO_NAME"
    eval gh repo create "$REPO_NAME" $VISIBILITY $DESC_FLAG --source=. --remote="$REMOTE"
    
    print_info "Repository created successfully!"
fi

# Check if remote exists
if ! git remote get-url "$REMOTE" &> /dev/null; then
    print_warning "Remote '$REMOTE' not found."
    print_prompt "Enter GitHub repository URL (e.g., https://github.com/username/repo.git):"
    read -r REPO_URL
    
    if [ -z "$REPO_URL" ]; then
        print_error "Repository URL is required"
        exit 1
    fi
    
    git remote add "$REMOTE" "$REPO_URL"
    print_info "Remote '$REMOTE' added: $REPO_URL"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    print_info "Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv

# Distribution / packaging
build/
dist/
*.egg-info/

# PyInstaller
*.manifest
*.spec

# Unit test / coverage
.coverage
.pytest_cache/
htmlcov/

# Jupyter Notebook
.ipynb_checkpoints

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
output/*
!output/.gitkeep
*.log

# Model files (too large for git)
*.bin
*.safetensors
*.ckpt
*.pth

# Environment
.env
.env.local
EOF
    print_info ".gitignore created"
fi

# Create output/.gitkeep to preserve directory
mkdir -p output
touch output/.gitkeep

# Check for uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    HAS_CHANGES=true
else
    HAS_CHANGES=false
fi

if [ "$HAS_CHANGES" = false ] && [ -z "$(git status --porcelain)" ]; then
    print_info "No changes to commit"
    
    print_prompt "Push anyway? (y/N):"
    read -r PUSH_ANYWAY
    
    if [[ ! "$PUSH_ANYWAY" =~ ^[Yy]$ ]]; then
        print_info "Aborted"
        exit 0
    fi
else
    # Get commit message if not provided
    if [ -z "$COMMIT_MESSAGE" ]; then
        print_prompt "Enter commit message:"
        read -r COMMIT_MESSAGE
        
        if [ -z "$COMMIT_MESSAGE" ]; then
            print_error "Commit message is required"
            exit 1
        fi
    fi
    
    # Show status
    print_info "Current status:"
    git status --short
    echo ""
    
    # Confirm
    print_prompt "Commit and push these changes? (Y/n):"
    read -r CONFIRM
    
    if [[ "$CONFIRM" =~ ^[Nn]$ ]]; then
        print_info "Aborted"
        exit 0
    fi
    
    # Add all changes
    print_info "Staging changes..."
    git add .
    
    # Commit
    print_info "Creating commit..."
    git commit -m "$COMMIT_MESSAGE"
fi

# Check if branch exists on remote
if git ls-remote --heads "$REMOTE" "$BRANCH" | grep -q "$BRANCH"; then
    BRANCH_EXISTS=true
else
    BRANCH_EXISTS=false
fi

# Push to GitHub
print_info "Pushing to $REMOTE/$BRANCH..."

if [ "$FORCE" = true ]; then
    print_warning "Force pushing..."
    git push -f "$REMOTE" "$BRANCH"
elif [ "$BRANCH_EXISTS" = false ]; then
    print_info "Creating new branch on remote..."
    git push -u "$REMOTE" "$BRANCH"
else
    git push "$REMOTE" "$BRANCH"
fi

# Get repository URL
REPO_URL=$(git remote get-url "$REMOTE")

print_info "Successfully pushed to GitHub!"
echo ""
echo "Repository: $REPO_URL"
echo "Branch: $BRANCH"
echo ""
print_info "View your repository at:"
echo "  ${REPO_URL%.git}"

# Made with Bob
