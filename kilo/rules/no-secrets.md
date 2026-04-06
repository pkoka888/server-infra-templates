# Rule: no-secrets

**Scope:** All files and outputs

## Rules

1. **Never commit .env** — .env is in .gitignore, never force-add it
2. **Never print API keys** — Use `[REDACTED]` in logs and outputs
3. **Use .env.example** — Document required variables without values
4. **Reference env vars** — Scripts must read from env vars, never hardcode
5. **Rotate if exposed** — If a key is accidentally committed, regenerate immediately

## Files That May Contain Secrets

- `.env` — NEVER commit
- `scripts/*.sh` — Must use env vars, not literals
- `docs/` — Reference keys as `$VAR`, never paste actual values
- `memory/` — Same rules as docs
