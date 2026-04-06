# Server Infrastructure Templates

**Version:** 1.0.0
**Date:** 2026-04-06
**Repository:** https://github.com/pkoka888/server-infra-templates

Standardized templates for 3-server infrastructure (s60, s61, s62) with Traefik, NAT, and centralized management.

---

## Purpose

Provide **reusable, production-ready** templates that:
- Follow security best practices (CIS benchmark-aligned)
- Enable consistent deployment across projects
- Reduce duplication in CI/CD pipelines
- Support agent and automation workflows

---

## Decision Matrix: Shared vs Project-Related

Use this criteria to determine where content belongs:

| Criterion | Shared (this repo) | Project-Related (in project) |
|-----------|-------------------|----------------------------|
| **Reusability** | Used by 2+ projects | Single project only |
| **Specificity** | Generic/templated | Custom configuration |
| **Frequency** | Changes rarely | Changes frequently |
| **Ownership** | Infrastructure team | Project team |
| **Security** | Base security settings | Project-specific secrets |

### Examples

| Content | Where | Reason |
|---------|-------|--------|
| Docker base templates | **Shared** | All projects use |
| PostgreSQL config | **Shared** | Standard across projects |
| Project .env file | Project | Contains secrets |
| CI/CD deploy workflow | **Shared** | Standard pipeline |
| Project-specific tests | Project | Custom logic |
| Ansible base roles | **Shared** | Reusable infrastructure |
| Application deployment | Project | Custom logic |
| Agent prompts | **Shared** | Standard prompts |
| Skill definitions | **Shared** | Reusable skills |
| Rules/constitution | **Shared** | Governance |

### Decision Rules

1. **If it could help 2+ projects** → Shared
2. **If it's infrastructure** → Shared (unless custom)
3. **If it contains secrets** → Project (never shared)
4. **If it requires project-specific secrets** → Not shared
5. **If it's governance** → Shared (constitution)

---

## Template Categories

### 1. Docker Compose (`docker/compose/`)

**Purpose:** Container orchestration templates

**Templates:**
- `app.yml` - Application with DB, Redis, monitoring

**Required Fields:**
- Image pinned (no `:latest`)
- Healthcheck defined
- Logging (max-size: 10m, max-file: 3)
- Resource limits (memory, CPU)
- `restart: unless-stopped`
- `security_opt: no-new-privileges:true`
- Non-root user

### 2. Ansible Roles (`ansible/roles/`)

**Purpose:** Infrastructure automation

**Templates:**
- `common/` - Reusable role template

**Required Fields:**
- FQCN (Fully Qualified Collection Names)
- Idempotent tasks (`changed_when`, `creates`)
- No hardcoded secrets (use `vars_files`)
- Handlers for restart

### 3. GitHub Actions (`github-actions/workflows/`)

**Purpose:** CI/CD pipelines

**Templates:**
- `deploy.yml` - Build and deploy workflow
- `reusable/` - Reusable workflow templates

**Required Fields:**
- Permissions (deny-by-default)
- SHA-pinned actions
- Environment protection for production

### 4. Project (`project/`)

**Purpose:** Project initialization

**Templates:**
- `Dockerfile` - Production-ready Dockerfile

**Required Fields:**
- Non-root user
- Healthcheck
- No secrets embedded

---

## Directory Structure

```
server-infra-templates/
├── README.md                    # This file
├── docker/compose/             # Docker templates
├── ansible/                   # Ansible templates
│   └── roles/
│       └── common/
├── github-actions/workflows/ # CI/CD templates
│   └── reusable/             # Reusable workflows
└── project/                  # Project templates
```

---

## Usage

### Copy to Project

```bash
# Docker compose
cp docker/compose/app.yml /path/to/project/docker-compose.yml

# GitHub Actions
cp github-actions/workflows/deploy.yml /path/to/project/.github/workflows/

# Ansible role
cp -r ansible/roles/common /path/to/ansible/roles/my_role

# Dockerfile
cp project/Dockerfile /path/to/project/Dockerfile
```

### Use as Git Submodule

```bash
# Add as submodule
git submodule add https://github.com/pkoka888/server-infra-templates.git infrastructure/templates

# Update
git submodule update --init infrastructure/templates
```

### Reference in Ansible

```yaml
# In playbook
- import_role:
    name: {{ role_name }}  # Copy common/ to this name
```

### Reference in GitHub Actions

```yaml
# In workflow
uses: pkoka888/server-infra-templates/.github/workflows/deploy.yml@main
```

---

## Best Practices (from research)

### Docker
- Always pin image tags (use digests in production)
- Use multi-stage builds to reduce size
- Never run as root
- Configure resource limits
- Set up log rotation
- Use healthchecks for orchestration

### Ansible
- Use FQCN (Fully Qualified Collection Names)
- Make idempotent with `changed_when` and `creates`
- Use variables for configuration
- Never hardcode secrets
- Use handlers for service restart

### GitHub Actions
- Define explicit permissions (deny-by-default)
- Pin actions to SHA
- Use reusable workflows for common patterns
- Protect environments for production

### General
- Test templates in isolation before use
- Version templates separately from projects
- Use naming conventions consistently
- Document customizations

---

## Related Repositories (from research)

- [thomvaill/tads-boilerplate](https://github.com/Thomvaill/tads-boilerplate) - Terraform + Ansible + Docker
- [securedbyfajobi/secure-iac-templates](https://github.com/securedbyfajobi/secure-iac-templates) - CIS-compliant templates
- [hunterkirk/github-action-templates](https://github.com/hunterkirk/github-action-templates) - Action templates

---

## Integration with .agent/

This templates repo integrates with `.agent/` in op.expc.cz:

- `.agent/templates/` → Canonical source (rendered here)
- `infrastructure/templates/` → Submodule in op.expc.cz
- `.kilo/` → Render targets in op.expc.cz

**Update flow:**
1. Update `.agent/templates/`
2. Render: `python3 .agent/generators/render.py`
3. Commit to op.expc.cz
4. Push updates to this repo

---

## Version History

| Version | Date | Changes |
|---------|------|----------|
| 1.0.0 | 2026-04-06 | Initial release |

---

## License

MIT License - See GitHub repository