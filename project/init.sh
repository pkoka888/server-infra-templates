#!/bin/bash
# Project Initialization Script Template
# Usage: ./init.sh <project-name> [--python|--node|--docker]

set -euo pipefail

PROJECT_NAME="${1:-}"

if [[ -z "$PROJECT_NAME" ]]; then
    echo "Usage: $0 <project-name> [--python|--node|--docker]"
    echo ""
    echo "Options:"
    echo "  --python    Create Python project with .venv"
    echo "  --node      Create Node.js project"
    echo "  --docker    Create Docker-based project"
    exit 1
fi

echo "Initializing project: $PROJECT_NAME"

create_python_project() {
    echo "Creating Python project structure..."
    
    mkdir -p "$PROJECT_NAME"/{lib,tests,scripts,.vscode,.kilo,.agent}
    cd "$PROJECT_NAME"
    
    python3 -m venv .venv
    source .venv/bin/activate
    
    cat > pyproject.toml << 'EOF'
[project]
name = "{{project_name}}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []
EOF

    cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
.env
.env.*
*.egg-info/
dist/
build/
.pytest_cache/
.mypy_cache/
EOF

    mkdir -p .vscode
    cat > .vscode/settings.json << 'EOF'
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.analysis.typeCheckingMode": "basic"
}
EOF

    echo "Python project created at: $PROJECT_NAME"
}

create_node_project() {
    echo "Creating Node.js project structure..."
    
    mkdir -p "$PROJECT_NAME"/{src,tests,.vscode,.kilo,.agent}
    cd "$PROJECT_NAME"
    
    npm init -y
    
    cat > .gitignore << 'EOF'
node_modules/
.env
.env.*
dist/
build/
*.log
.DS_Store
EOF

    echo "Node.js project created at: $PROJECT_NAME"
}

create_docker_project() {
    echo "Creating Docker project structure..."
    
    mkdir -p "$PROJECT_NAME"/{app,tests,docker,.vscode,.kilo,.agent}
    cd "$PROJECT_NAME"
    
    cat > docker/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
EOF

    cat > docker/docker-compose.yml << 'EOF'
version: '3.8'

services:
  app:
    build: 
      context: ..
      dockerfile: docker/Dockerfile
    env_file:
      - ../.env
    volumes:
      - ../:/app
EOF

    echo "Docker project created at: $PROJECT_NAME"
}

if [[ "${2:-}" == "--python" ]]; then
    create_python_project
elif [[ "${2:-}" == "--node" ]]; then
    create_node_project
elif [[ "${2:-}" == "--docker" ]]; then
    create_docker_project
else
    echo "Please specify project type: --python, --node, or --docker"
    exit 1
fi
