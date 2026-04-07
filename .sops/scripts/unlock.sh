#!/bin/bash
# Unlock SOPS vault - decrypts all secrets and exports as environment variables
# Usage: source .sops/scripts/unlock.sh

VAULT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGE_KEY_FILE="${SOPS_AGE_KEY_FILE:-$HOME/.config/sops/age/keys.txt}"
TEMP_EXPORTS=$(mktemp /tmp/sops-exports.XXXXXX)

if [ ! -f "$AGE_KEY_FILE" ]; then
    echo "❌ Age key not found at $AGE_KEY_FILE"
    echo "   Set SOPS_AGE_KEY_FILE or place key at ~/.config/sops/age/keys.txt"
    echo ""
    echo "   To generate new key:"
    echo "   age-keygen > ~/.config/sops/age/keys.txt"
    rm -f "$TEMP_EXPORTS"
    return 1 2>/dev/null || exit 1
fi

export SOPS_AGE_KEY_FILE="$AGE_KEY_FILE"

echo "🔓 Unlocking Metabase SOPS vault..."

> "$TEMP_EXPORTS"

for FILE in "$VAULT_DIR"/secrets/*.enc.yaml; do
    if [ -f "$FILE" ]; then
        NAME=$(basename "$FILE" .enc.yaml)
        echo "  Decrypting: $NAME"
        sops -d "$FILE" | yq -r -o=json '.' | jq -r '
            [paths(scalars) as $p | {"key": ($p | map(tostring) | join("_")), "value": getpath($p)}] |
            from_entries |
            to_entries[] |
            "export METABASE_" + (.key | ascii_upcase) + "=" + (.value | tostring | @sh)
        ' >> "$TEMP_EXPORTS" 2>/dev/null || true
    fi
done

source "$TEMP_EXPORTS" 2>/dev/null || true
rm -f "$TEMP_EXPORTS"

COUNT=$(env | grep '^METABASE_' | wc -l)
echo "✅ Vault unlocked. $COUNT secrets available as METABASE_* environment variables."
echo "   Run '.sops/scripts/lock.sh' to clear secrets from environment."
echo ""
echo "   Usage in pipeline:"
echo "   source .sops/scripts/unlock.sh"
echo "   echo \$METABASE_PS_SHOP_URL"