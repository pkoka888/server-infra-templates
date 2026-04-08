# Secrets Management

## Overview

This project supports two secrets management approaches:

1. **SOPS** (Secrets OPerationS) - For development
2. **Ansible Vault** - For production deployment

## SOPS Configuration (Development)

### Directory Structure

```
.sops/
├── .sops.yaml              # SOPS configuration
├── secrets/               # Encrypted secrets
│   └── metabase-clients.template.yaml
└── scripts/
    ├── lock.sh            # Lock all secrets
    └── unlock.sh          # Unlock all secrets
```

## Ansible Vault Configuration (Production)

### Directory Structure

```
ansible/
├── ansible.cfg            # Vault configuration
├── inventory/
│   └── hosts.yml          # Server inventory
├── group_vars/
│   └── all/
│       └── vault.yml      # Encrypted secrets
├── playbooks/
│   ├── deploy.yml         # Deploy platform
│   ├── backup.yml         # Backup database
│   └── rotate-secrets.yml # Rotate API keys
└── templates/
    ├── env.j2             # Environment template
    └── docker-compose.yml.j2
```

### Quick Commands

```bash
# Create vault password file
echo "your-secure-password" > ~/.vault_pass
chmod 600 ~/.vault_pass

# Edit encrypted vault
ansible-vault edit ansible/group_vars/all/vault.yml

# Encrypt vault file
ansible-vault encrypt ansible/group_vars/all/vault.yml

# Decrypt vault file
ansible-vault decrypt ansible/group_vars/all/vault.yml

# Run playbook with vault
ansible-playbook ansible/playbooks/deploy.yml --ask-vault-pass

# View vault variables (decrypted)
ansible-inventory -i ansible/inventory/hosts.yml --list --vault-password-file ~/.vault_pass
```

### Ansible Vault Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `vault_postgres_password` | PostgreSQL password | `secret123` |
| `vault_client1_ga4_*` | GA4 credentials | OAuth tokens |
| `vault_client1_fb_*` | Facebook Ads credentials | Access tokens |
| `vault_borg_passphrase` | Backup encryption | Passphrase |

## Configuration

### .sops.yaml

```yaml
creation_rules:
  - path_regex: \.sops/secrets/.*
    encrypted_suffix: .yaml
    age: >-
      age10j83qpjzwup04f02enfrqdcy5hfshtyx98swckmvh4zg578qayxs5jmdra
```

## Usage

### Unlock Secrets

```bash
# Unlock all secrets (loads environment variables)
source .sops/scripts/unlock.sh

# Or manually decrypt
sops --decrypt .sops/secrets/metabase-clients.yaml
```

### Lock Secrets

```bash
# Lock all secrets after editing
.sops/scripts/lock.sh
```

### Edit Encrypted Files

```bash
# Opens editor with decrypted content
sops .sops/secrets/metabase-clients.yaml

# Or with Age key
sops --age age10j83... .sops/secrets/metabase-clients.yaml
```

## Secrets Structure

### metabase-clients.template.yaml

```yaml
# Template for client configurations
# Copy to .sops/secrets/metabase-client1.yaml and fill in values

client_id: client1
environment: production

# Database
postgres:
  host: localhost
  port: 5432
  database: metabase
  username: metabase
  password: CHANGE_ME

# Google Analytics 4
ga4:
  property_id: "123456789"
  client_id: CHANGE_ME.apps.googleusercontent.com
  client_secret: CHANGE_ME
  refresh_token: CHANGE_ME

# Facebook Ads
facebook:
  ad_account_id: act_123456
  access_token: CHANGE_ME

# Google Ads
google_ads:
  customer_id: "1234567890"
  developer_token: CHANGE_ME
  client_id: CHANGE_ME.apps.googleusercontent.com
  client_secret: CHANGE_ME

# PrestaShop
prestashop:
  shop_url: https://shop.example.com
  api_key: CHANGE_ME
```

## Adding New Secrets

1. **Create template:**
   ```bash
   cp .sops/secrets/metabase-clients.template.yaml \
      .sops/secrets/metabase-client2.yaml
   ```

2. **Edit with SOPS:**
   ```bash
   sops .sops/secrets/metabase-client2.yaml
   ```

3. **Use in pipeline:**
   ```bash
   source .sops/scripts/unlock.sh
   export POSTGRES_PASSWORD=$(sops -d .sops/secrets/metabase-client2.yaml | yq '.postgres.password')
   ```

## Integration with Docker Compose

### Load secrets at startup

```bash
#!/bin/bash
# start.sh

# Unlock secrets
source .sops/scripts/unlock.sh

# Export variables
export $(sops -d .sops/secrets/metabase-clients.yaml | grep -v "^#" | xargs)

# Start services
docker compose up -d
```

## Key Management

### Age Key Location

```
~/.config/sops/age/keys.txt
```

### Backup Keys

```bash
# Backup to secure location
tar czf sops-backup-$(date +%Y%m%d).tar.gz \
  .sops/ \
  ~/.config/sops/

# Encrypt backup
gpg -c sops-backup-*.tar.gz
```

## Security Checklist

- [ ] Age keys stored securely (~/.config/sops/)
- [ ] Key file has correct permissions (600)
- [ ] `.sops/` directory is in `.gitignore`
- [ ] Only templates/commit encrypted files
- [ ] Unlock script uses secure key retrieval
- [ ] Regular key rotation scheduled

## Quick Commands

```bash
# Decrypt all secrets
sops --decrypt --in-place .sops/secrets/

# Encrypt all secrets
sops --encrypt --in-place .sops/secrets/

# View decrypted content
sops -d .sops/secrets/metabase-clients.yaml

# Rotate keys
sops --rotate-keys --in-place .sops/secrets/

# Check for unencrypted secrets
grep -r "password\|secret\|token\|key" .sops/secrets/ --include="*.yaml" | grep -v "^#"
```

## Troubleshooting

### "No key found"

```bash
# Ensure Age key is available
export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt

# Or add to shell profile
echo 'export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt' >> ~/.bashrc
```

### "Decryption failed"

```bash
# Check key matches .sops.yaml
cat ~/.config/sops/age/keys.txt
# Should contain: age10j83qpjzwup04f02enfrqdcy5hfshtyx98swckmvh4zg578qayxs5jmdra
```
