#!/bin/bash
# Import SOPS secrets to .env.client_name files
# Usage: ./scripts/import-sops.sh client_name

set -euo pipefail

CLIENT="${1:-}"
if [ -z "$CLIENT" ]; then
    echo "Usage: $0 client_name"
    echo "Example: $0 client1"
    exit 1
fi

# Source SOPS to get secrets
source .sops/scripts/unlock.sh

# Check if we have secrets for this client
ENV_FILE="scripts/.env.$CLIENT"

echo "Creating $ENV_FILE from SOPS secrets..."

# Check if file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating new file..."
    touch "$ENV_FILE"
fi

# Export secrets for this client
if [ -n "${METABASE_CLIENT1_PS_SHOP_URL:-}" ]; then
    echo "CLIENT_ID=$CLIENT" >> "$ENV_FILE"
    echo "" >> "$ENV_FILE"
    
    # PrestaShop
    echo "# PrestaShop" >> "$ENV_FILE"
    echo "PS_SHOP_URL=${METABASE_CLIENT1_PS_SHOP_URL:-}" >> "$ENV_FILE"
    echo "PS_API_KEY=${METABASE_CLIENT1_PS_API_KEY:-}" >> "$ENV_FILE"
    echo "" >> "$ENV_FILE"
    
    # GA4
    echo "# Google Analytics 4" >> "$ENV_FILE"
    echo "GA4_PROPERTY_ID=${METABASE_CLIENT1_GA4_PROPERTY_ID:-}" >> "$ENV_FILE"
    echo "GA4_CLIENT_ID=${METABASE_CLIENT1_GA4_CLIENT_ID:-}" >> "$ENV_FILE"
    echo "GA4_CLIENT_SECRET=${METABASE_CLIENT1_GA4_CLIENT_SECRET:-}" >> "$ENV_FILE"
    echo "GA4_REFRESH_TOKEN=${METABASE_CLIENT1_GA4_REFRESH_TOKEN:-}" >> "$ENV_FILE"
    echo "GA4_PROJECT_ID=${METABASE_CLIENT1_GA4_PROJECT_ID:-}" >> "$ENV_FILE"
    echo "" >> "$ENV_FILE"
    
    # Google Ads
    echo "# Google Ads" >> "$ENV_FILE"
    echo "GADS_CUSTOMER_ID=${METABASE_CLIENT1_GADS_CUSTOMER_ID:-}" >> "$ENV_FILE"
    echo "GADS_DEVELOPER_TOKEN=${METABASE_CLIENT1_GADS_DEVELOPER_TOKEN:-}" >> "$ENV_FILE"
    echo "GADS_CLIENT_ID=${METABASE_CLIENT1_GADS_CLIENT_ID:-}" >> "$ENV_FILE"
    echo "GADS_CLIENT_SECRET=${METABASE_CLIENT1_GADS_CLIENT_SECRET:-}" >> "$ENV_FILE"
    echo "GADS_REFRESH_TOKEN=${METABASE_CLIENT1_GADS_REFRESH_TOKEN:-}" >> "$ENV_FILE"
    echo "" >> "$ENV_FILE"
    
    # Facebook Ads
    echo "# Facebook Ads" >> "$ENV_FILE"
    echo "FB_AD_ACCOUNT_ID=${METABASE_CLIENT1_FB_AD_ACCOUNT_ID:-}" >> "$ENV_FILE"
    echo "FB_ACCESS_TOKEN=${METABASE_CLIENT1_FB_ACCESS_TOKEN:-}" >> "$ENV_FILE"
    
    echo "✅ Created $ENV_FILE"
else
    echo "❌ No secrets found for client: $CLIENT"
    echo "   Check SOPS vault or add client to .sops/secrets/metabase-clients.template.yaml"
fi

# Lock vault
source .sops/scripts/lock.sh