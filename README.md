# Server Infrastructure Templates

Standardized templates for 3-server infrastructure (s60, s61, s62).

## Purpose

Provide reusable, production-ready templates for:
- Ansible roles and playbooks
- Docker Compose configurations
- GitHub Actions workflows

## Structure

```
templates/
├── ansible/
│   ├── roles/
│   │   └── common/          # Reusable role template
│   └── playbooks/           # Playbook templates
├── docker/
│   └── compose/           # Docker compose templates
├── github-actions/
│   └── workflows/         # CI/CD workflow templates
└── project/               # Project initialization
```

## Usage

Copy templates to your project:

```bash
# Ansible role
cp -r ansible/roles/common /path/to/ansible/roles/<role_name>

# Docker compose
cp docker/compose/app.yml /path/to/project/docker-compose.yml

# GitHub Actions
cp github-actions/workflows/deploy.yml /path/to/project/.github/workflows/
```

## Standards

All templates follow naming conventions defined in:
- `naming-conventions.md` - File and resource naming
- Standards from BOS (Business Operating System)

### Required Fields

**Docker:**
- Image pinned (no :latest)
- Healthcheck defined
- Logging configured (max-size: 10m, max-file: 3)
- Resource limits (memory, CPU)
- restart: unless-stopped
- security_opt: no-new-privileges:true
- Non-root user

**Ansible:**
- FQCN (Fully Qualified Collection Names)
- Idempotent tasks (changed_when, creates)
- No hardcoded secrets (use vars_files)
- Handlers for service restart

**GitHub Actions:**
- Permissions defined (deny-by-default)
- SHA-pinned actions
- Environment protection for production

## Version

1.0.0 - 2026-04-06

## Source

Canonical source: `.agent/templates/` in op.expc.cz repository