#!/bin/bash
# Lock SOPS vault - clears all METABASE_* environment variables
# Usage: source .sops/scripts/lock.sh

echo "🔒 Locking Metabase SOPS vault..."

# Unset all METABASE_ variables
for var in $(env | grep '^METABASE_' | cut -d= -f1); do
    unset "$var"
done

echo "✅ Vault locked. All METABASE_* environment variables cleared."