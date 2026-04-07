#!/bin/bash
# Audit CLI - Run server audits via LangGraph
# Usage: ./audit.sh <server> [type]
# Example: ./audit.sh s60 security

set -euo pipefail

LANGGRAPH_URL="http://100.111.141.111:8093"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"; }
ok() { echo -e "${GREEN}✅${NC} $1"; }
warn() { echo -e "${YELLOW}⚠️${NC} $1"; }
err() { echo -e "${RED}❌${NC} $1"; }

# Usage
if [ $# -lt 1 ]; then
    echo "Usage: $0 <server> [type]"
    echo ""
    echo "Arguments:"
    echo "  server  - s60, s61, or s62"
    echo "  type    - security (default), performance, compliance"
    echo ""
    echo "Examples:"
    echo "  $0 s60              # Security audit on s60"
    echo "  $0 s61 performance # Performance audit on s61"
    echo "  $0 s62 compliance  # Compliance audit on s62"
    exit 1
fi

SERVER=$1
TYPE=${2:-security}

# Validate server
if [[ ! "$SERVER" =~ ^(s60|s61|s62)$ ]]; then
    err "Invalid server: $SERVER"
    echo "Valid servers: s60, s61, s62"
    exit 1
fi

# Validate type
if [[ ! "$TYPE" =~ ^(security|performance|compliance)$ ]]; then
    err "Invalid type: $TYPE"
    echo "Valid types: security, performance, compliance"
    exit 1
fi

log "Starting $TYPE audit on $SERVER..."

# Check LangGraph health first
if ! curl -sf -m 5 "$LANGGRAPH_URL/health" > /dev/null 2>&1; then
    err "LangGraph server not available"
    echo "Check: docker ps | grep langgraph"
    exit 1
fi
ok "LangGraph server ready"

# Run audit
log "Executing audit workflow..."
RESPONSE=$(curl -sf -m 60 -X POST "$LANGGRAPH_URL/workflow/audit" \
    -H "Content-Type: application/json" \
    -d "{\"target_server\": \"$SERVER\", \"audit_type\": \"$TYPE\"}" 2>&1)

if [ $? -ne 0 ]; then
    err "Audit request failed"
    echo "$RESPONSE"
    exit 1
fi

# Parse response
STATUS=$(echo "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null)
STEPS=$(echo "$RESPONSE" | python3 -c "import json,sys; print(', '.join(json.load(sys.stdin).get('steps_completed',[])))" 2>/dev/null)
FINDINGS=$(echo "$RESPONSE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('findings',[])))" 2>/dev/null)

if [ "$STATUS" = "completed" ]; then
    ok "Audit completed successfully"
    echo ""
    echo "Results:"
    echo "  Server: $SERVER"
    echo "  Type: $TYPE"
    echo "  Status: $STATUS"
    echo "  Steps: $STEPS"
    echo "  Findings: $FINDINGS items"
else
    warn "Audit status: $STATUS"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
fi