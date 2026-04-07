#!/bin/bash
# LangGraph Diagnostics and Fix Script
# Usage: ./langgraph-diagnostics.sh [--fix] [--restart] [--test]

set -euo pipefail

LANGGRAPH_CONTAINER="langgraph_app-langgraph-app-1"
LANGGRAPH_HOST="100.111.141.111"
LANGGRAPH_PORT="8093"
LANGGRAPH_URL="http://${LANGGRAPH_HOST}:${LANGGRAPH_PORT}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

log_ok() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_container() {
    log "Checking LangGraph container..."
    
    if ! docker ps --format '{{.Names}}' | grep -q "^${LANGGRAPH_CONTAINER}$"; then
        log_error "Container not running: $LANGGRAPH_CONTAINER"
        return 1
    fi
    
    local status=$(docker inspect --format='{{.State.Status}}' "$LANGGRAPH_CONTAINER" 2>/dev/null)
    log_ok "Container status: $status"
    
    local health=$(docker inspect --format='{{.State.Health.Status}}' "$LANGGRAPH_CONTAINER" 2>/dev/null || echo "none")
    log_ok "Health: $health"
    
    return 0
}

check_logs() {
    log "Checking recent logs for errors..."
    
    local errors=$(docker logs "$LANGGRAPH_CONTAINER" --tail 100 2>&1 | grep -iE "error|exception|traceback|fail" | head -10)
    
    if [ -n "$errors" ]; then
        log_warn "Found errors in logs:"
        echo "$errors" | while read line; do
            echo "  $line"
        done
    else
        log_ok "No errors found in recent logs"
    fi
    
    # Check for 500 errors
    local http_errors=$(docker logs "$LANGGRAPH_CONTAINER" --tail 200 2>&1 | grep "500 Internal Server Error" | wc -l)
    if [ "$http_errors" -gt 0 ]; then
        log_warn "Found $http_errors HTTP 500 errors in recent logs"
    else
        log_ok "No HTTP 500 errors in recent logs"
    fi
}

check_endpoints() {
    log "Testing endpoints..."
    
    # Health check
    local health_resp=$(curl -sf -m 5 "$LANGGRAPH_URL/health" 2>/dev/null || echo "FAILED")
    if [ "$health_resp" = "FAILED" ]; then
        log_error "Health endpoint failed"
    else
        log_ok "Health: $health_resp"
    fi
    
    # Test audit endpoint multiple times
    log "Testing audit endpoint (5 attempts)..."
    
    local success_count=0
    local fail_count=0
    
    for i in {1..5}; do
        local start=$(date +%s%N)
        local resp=$(curl -sf -m 10 -X POST "$LANGGRAPH_URL/workflow/audit" \
            -H "Content-Type: application/json" \
            -d '{"target_server":"s60","audit_type":"security"}' 2>&1)
        local end=$(date +%s%N)
        local duration=$(( (end - start) / 1000000 ))
        
        if echo "$resp" | grep -q "status"; then
            log_ok "Attempt $i: OK (${duration}ms)"
            success_count=$((success_count + 1))
        else
            log_error "Attempt $i: FAILED (${duration}ms)"
            fail_count=$((fail_count + 1))
        fi
        
        sleep 1
    done
    
    log "Results: $success_count success, $fail_count failures"
    
    if [ $fail_count -gt 0 ]; then
        return 1
    fi
    return 0
}

fix_restart() {
    log "Applying fixes..."
    
    log "Step 1: Restarting container..."
    docker restart "$LANGGRAPH_CONTAINER"
    log_ok "Container restarted"
    
    log "Waiting 15 seconds for startup..."
    sleep 15
    
    log "Step 2: Checking container is healthy..."
    for i in {1..10}; do
        if curl -sf -m 5 "$LANGGRAPH_URL/health" > /dev/null 2>&1; then
            log_ok "Container is responding"
            break
        fi
        if [ $i -eq 10 ]; then
            log_error "Container not responding after 10 attempts"
            return 1
        fi
        sleep 2
    done
    
    log "Step 3: Testing endpoints after restart..."
    sleep 5
    
    local success=0
    for i in {1..3}; do
        if curl -sf -m 10 -X POST "$LANGGRAPH_URL/workflow/audit" \
            -H "Content-Type: application/json" \
            -d '{"target_server":"s60","audit_type":"security"}' | grep -q "status"; then
            log_ok "Audit endpoint working after restart"
            success=1
            break
        fi
        sleep 2
    done
    
    if [ $success -eq 0 ]; then
        log_error "Audit endpoint still failing after restart"
        log "Checking for deeper issues..."
        docker logs "$LANGGRAPH_CONTAINER" --tail 50
        return 1
    fi
    
    log_ok "All fixes applied successfully"
    return 0
}

fix_memory_saver() {
    log "Switching to MemorySaver (less persistent but more stable)..."
    
    # This would require modifying the app.py and rebuilding
    # For now, just document the option
    log "To switch to MemorySaver:"
    log "  1. Edit langgraph_app/app.py"
    log "  2. Change: checkpointer = MemorySaver()"
    log "  3. Rebuild: cd langgraph_app && docker compose build"
    log "  4. Deploy: docker compose up -d"
    
    log_warn "This change would lose checkpoint persistence"
    log "Use this only if PostgresSaver continues to have issues"
}

show_status() {
    echo "========================================="
    echo "  LangGraph Diagnostics Report"
    echo "========================================="
    echo ""
    
    echo "Container: $LANGGRAPH_CONTAINER"
    docker ps --filter "name=langgraph" --format "  {{.Names}}: {{.Status}}"
    echo ""
    
    echo "Endpoint: $LANGGRAPH_URL"
    curl -sf -m 5 "$LANGGRAPH_URL/health" 2>/dev/null || echo "  NOT RESPONDING"
    echo ""
    
    echo "Recent errors in logs:"
    docker logs "$LANGGRAPH_CONTAINER" --tail 50 2>&1 | grep -iE "error|exception|500" | tail -5 | sed 's/^/  /'
    echo ""
    
    echo "========================================="
}

# Main
case "${1:-}" in
    --fix)
        fix_restart
        ;;
    --restart)
        log "Restarting container..."
        docker restart "$LANGGRAPH_CONTAINER"
        sleep 15
        check_endpoints
        ;;
    --test)
        check_container && check_logs && check_endpoints
        ;;
    *)
        show_status
        echo ""
        echo "Usage: $0 [option]"
        echo "  --test     Run diagnostics tests"
        echo "  --fix      Attempt to fix issues (restart + retest)"
        echo "  --restart  Just restart container"
        ;;
esac