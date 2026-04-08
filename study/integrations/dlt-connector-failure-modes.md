# DLT Connector Failure Modes & Mitigation Strategies

Reference guide for diagnosing and resolving common failures when loading data from GA4, Facebook/Meta Ads, and PrestaShop using dlt (data load tool).

---

## Table of Contents

1. [Google Analytics 4 (GA4)](#1-google-analytics-4-ga4)
2. [Facebook/Meta Ads](#2-facebookmeta-ads)
3. [PrestaShop](#3-prestashop)

---

## 1. Google Analytics 4 (GA4)

### Overview

GA4 Data API has three quota categories: **Core**, **Realtime**, and **Funnel**. Quotas are applied at the Google Cloud Project level and enforced per Analytics Property.

### Top Failure Modes

#### 1.1 Quota Exceeded (HTTP 429)

**Cause**: Exceeded daily/hourly token quotas or concurrent request limits.

**Error Messages**:
```
# Token quota exceeded
{
  "error": {
    "code": 429,
    "message": "Quota exceeded for quota metric 'Core token usage'",
    "status": "RESOURCE_EXHAUSTED"
  }
}

# Concurrent request limit
{
  "error": {
    "code": 429,
    "message": "Concurrent request limit exceeded for property"
  }
}
```

**Standard Property Limits**:
| Quota Type | Limit |
|------------|-------|
| Core Tokens/Property/Day | 200,000 |
| Core Tokens/Property/Hour | 40,000 |
| Tokens/Project/Property/Hour | 14,000 |
| Concurrent Requests | 10 |

**Recovery Strategy**:
- Implement exponential backoff with jitter (dlt handles this by default)
- Reduce request frequency by batching queries or spreading requests over time
- Use `returnPropertyQuota: true` to monitor token usage
- Schedule heavy loads outside peak hours

**Prevention**:
```python
# In dlt source config
@dlt.source
def ga4_source():
    config = {
        "quota_project": "your-gcp-project",
        "requests_per_minute": 60  # Stay under limit
    }
    # ...
```

#### 1.2 Data Sampling

**Cause**: Queries exceeding row limits trigger automatic sampling (typically 10M row limit per request).

**Error Messages**:
```json
{
  "metaData": {
    "dataLossFromSampling": false,
    "samplesReadCounts": ["12345678"],
    "samplingSpaceSizes": ["123456789"],
    "hitsBucket": "bucket_123"
  }
}
```

**Recovery Strategy**:
- Add `rowLimit` parameter to requests (max 100,000 rows per page)
- Break large date ranges into smaller chunks (daily or weekly)
- Use incremental loading with cursor-based pagination

**Prevention**:
```python
# Split large queries by date range
date_ranges = [
    ("2024-01-01", "2024-01-31"),
    ("2024-02-01", "2024-02-29"),
    # ...
]
```

#### 1.3 Authentication/Refresh Token Failures

**Cause**: Expired OAuth tokens, invalid credentials, or missing scopes.

**Error Messages**:
```
# Invalid credentials
{
  "error": "invalid_credentials",
  "error_description": "The credentials do not allow access to this resource."
}

# Missing scope
{
  "error": "ACCESS_TOKEN_SCOPE_INSUFFICIENT",
  "message": "Request had insufficient authentication scopes."
}
```

**Required OAuth Scopes**:
- `https://www.googleapis.com/auth/analytics.readonly`

**Recovery Strategy**:
- Implement token refresh logic (dlt handles this automatically with valid credentials)
- Store refresh tokens securely (never log or expose them)
- Validate token before pipeline execution

**Prevention**:
```python
# Use service account for server-to-server auth
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    "service-account.json",
    scopes=["https://www.googleapis.com/auth/analytics.readonly"]
)
```

#### 1.4 Invalid Property ID

**Cause**: Using Universal Analytics property ID format instead of GA4, or referencing a property without access.

**Error Messages**:
```
# Wrong property format
{
  "error": {
    "code": 400,
    "message": "Invalid property ID format. Expected numeric string."
  }
}

# No access to property
{
  "error": {
    "code": 403,
    "message": "User does not have access to this property"
  }
}
```

**Recovery Strategy**:
- GA4 Property IDs are numeric (e.g., `123456789`)
- UA property IDs use format `UA-XXXXX-Y`
- Verify service account has `Viewer` role on the property

**Prevention**:
- Double-check property ID format (numeric only for GA4 Data API)
- Grant least-privilege access via Google Admin console

#### 1.5 Property Quota Exhaustion

**Cause**: Any exhausted quota blocks all requests to that property.

**Error Messages**:
```json
{
  "error": {
    "code": 429,
    "message": "Property quota exhausted. See PropertyQuota for details."
  }
}
```

**Recovery Strategy**:
- Monitor quota status via `PropertyQuota` in API responses
- Use `getPropertyQuotasSnapshot` endpoint to check current state
- Wait for quota reset (daily quotas reset at midnight PST)

---

## 2. Facebook/Meta Ads

### Overview

Meta Marketing API enforces rate limits at multiple levels: **App-level**, **Ad Account-level**, and **Business-level**. Rate limits are measured in calls per hour (T菩提) and calls per second.

### Top Failure Modes

#### 2.1 Rate Limiting (HTTP 429)

**Cause**: Exceeded API call quota within the rolling window.

**Error Messages**:
```json
{
  "error": {
    "message": "Application request limit reached",
    "type": "OAuthException",
    "code": 613,
    "error_subcode": 1511005,
    "fbtrace_id": "trace_id_123"
  }
}

# Common error codes:
# 613 - Application request limit reached
# 4 - Too many calls
# 17 - User request limit reached
```

**Rate Limit Tiers** (Business Use Case limits):
| Level | Default Limit |
|-------|---------------|
| App Level | 200 APITe/HP (Ad Performance) |
| Ad Account Level | 50 APITe/HP per ad account |
| Business Level | Tier-based (Bronze: 250K/day) |

**Recovery Strategy**:
- Implement exponential backoff (Meta recommends 15-60+ minute delays)
- Check `X-App-Usage` and `X-Business-Usage` headers for remaining quota
- Reduce parallel requests and batch operations

**Prevention**:
```python
# dlt config for rate limit handling
@dlt.source
def facebook_ads():
    config = {
        "max_batch_size": 100,  # Reduce batch size
        "requests_per_hour": 180,  # Stay under 200 limit
        "backoff_min_seconds": 30
    }
```

#### 2.2 Access Token Expiration

**Cause**: Short-lived tokens (hours) or long-lived tokens (60 days) expired, or token revoked.

**Error Messages**:
```json
{
  "error": {
    "message": "Error validating access token: session has expired",
    "type": "OAuthException",
    "code": 190,
    "error_subcode": 463
  }
}

# Common error subcodes:
# 463 - Token expired
# 467 - Invalid token
# 460 - Token has been replaced
```

**Recovery Strategy**:
- Implement token refresh mechanism
- Use system to exchange short-lived for long-lived tokens
- Store and refresh long-lived tokens automatically

**Prevention**:
```python
# Token refresh flow
def refresh_long_lived_token(short_lived_token):
    url = f"https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": short_lived_token
    }
    # Returns token valid for 60 days
```

#### 2.3 App Review Requirements

**Cause**: Accessing permissions/features that require Meta app review.

**Error Messages**:
```json
{
  "error": {
    "message": "Permissions error",
    "type": "OAuthException",
    "code": 290,
    "error_subcode": 151703
  }
}
```

**Common Permissions Requiring Review**:
- `ads_read` - Access Ads data
- `business_management` - Manage business assets
- `ads_insights` - View ad insights
- `pages_read_engagement` - Read page metrics

**Recovery Strategy**:
- Submit app for review with use case documentation
- Use test/development tokens for testing
- Work with reduced permissions scope

#### 2.4 API Version Compatibility

**Cause**: Using deprecated API version or incompatible endpoint changes.

**Error Messages**:
```json
{
  "error": {
    "message": "(#100) Unknown fields: reach",
    "type": "OAuthException",
    "code": 100,
    "error_subcode": 2108006
  }
}

# June 2025 breaking change:
# "reach" field no longer returned for queries with breakdowns 
# and start_date > 13 months old
```

**Recovery Strategy**:
- Keep dlt connector updated to latest version
- Monitor Meta changelog for breaking changes
- Test against sandbox before production updates

#### 2.5 Ad Account Access Errors

**Cause**: Token doesn't have access to requested ad accounts, or account has restrictions.

**Error Messages**:
```json
{
  "error": {
    "message": "Invalid ad account ID",
    "type": "OAuthException",
    "code": 100,
    "error_subcode": 1100
  }
}

# No permission for ad account
{
  "error": {
    "message": "You do not have permission to access this ad account",
    "code": 278
  }
}
```

**Prevention**:
- Verify token has `ADVERTISER` or `ANALYST` role on ad account
- Add ad accounts via Business Manager for multi-account access
- Check account status (suspended accounts return errors)

---

## 3. PrestaShop

### Overview

PrestaShop WebService API provides REST access to store data. Authentication uses HTTP Basic Auth with an API key generated in the PrestaShop admin panel.

### Top Failure Modes

#### 3.1 Authentication Failures (HTTP 401)

**Cause**: Invalid API key, malformed authentication header, or webservice disabled.

**Error Messages**:
```
# Invalid key
<?xml version="1.0" encoding="UTF-8"?>
<prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
  <errors>
    <error>
      <code><![CDATA[1]]></code>
      <message><![CDATA[Bad authentication]]></message>
    </error>
  </errors>
</prestashop>

# No webservice key
<?xml version="1.0" encoding="UTF-8"?>
<prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
  <errors>
    <error>
      <code><![CDATA[2]]></code>
      <message><![CDATA[Unknown webservice key]]></message>
    </error>
  </errors>
</prestashop>
```

**Recovery Strategy**:
- Verify API key is correct and hasn't been regenerated
- Check HTTP Basic Auth header format: `Authorization: Basic base64(api_key:)`
- Ensure webservice is enabled in PrestaShop admin

**Prevention**:
```python
# Correct authentication
import base64

api_key = "YOUR_API_KEY_HERE"
auth = base64.b64encode(f"{api_key}:".encode()).decode()

headers = {
    "Authorization": f"Basic {auth}"
}
```

#### 3.2 Permission/Authorization Errors (HTTP 403)

**Cause**: API key doesn't have permissions for the requested resource.

**Error Messages**:
```
<?xml version="3.1.0"?>
<prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
  <errors>
    <error>
      <code><![CDATA[2]]></code>
      <message><![CDATA[Permission denied]]></message>
    </error>
  </errors>
</prestashop>
```

**Recovery Strategy**:
- Enable specific resource permissions in PrestaShop Webservice ACL
- Grant minimum required permissions (read vs write)
- Check resource-specific access settings

**Prevention**:
```
# In PrestaShop admin:
# Advanced Parameters > Webservice > Edit key > Set permissions
# Resources needed: customers, orders, products, etc.
```

#### 3.3 SSL/TLS Certificate Errors

**Cause**: Outdated SSL certificates, hostname mismatch, or SSL verification issues.

**Error Messages**:
```
# Certificate verification failed
SSLError: CERTIFICATE_VERIFY_FAILED

# Hostname mismatch
SSLError: hostname 'shop.example.com' doesn't match certificate

# Connection refused
ConnectionError: Connection refused
```

**Recovery Strategy**:
- Update server SSL certificates
- Configure Python SSL context for compatibility
- Check firewall/network connectivity to PrestaShop server

**Prevention**:
```python
# Handle SSL issues in dlt config
import ssl

context = ssl.create_default_context()
context.check_hostname = True
context.verify_mode = ssl.CERT_REQUIRED

# Or for testing with self-signed certs:
context = ssl._create_unverified_context()
```

#### 3.4 Server Errors (HTTP 500)

**Cause**: PrestaShop internal errors, database issues, or module conflicts.

**Error Messages**:
```
# Internal server error
<?xml version="1.0" encoding="UTF-8"?>
<prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
  <errors>
    <error>
      <code><![CDATA[0]]></code>
      <message><![CDATA[Internal error]]></message>
    </error>
  </errors>
</prestashop>
```

**Recovery Strategy**:
- Retry with exponential backoff (transient errors may resolve)
- Check PrestaShop error logs for details
- Verify database connectivity and health

#### 3.5 Rate Limiting / Timeout Issues

**Cause**: Too many requests, slow server response, or PrestaShop resource limits.

**Error Messages**:
```
# Timeout
ReadTimeout: HTTPSConnectionPool Read timed out

# Connection pool exhausted
ConnectionError: Connection pool full
```

**Recovery Strategy**:
- Reduce request concurrency
- Implement request throttling in pipeline
- Increase timeout settings
- Schedule loads during off-peak hours

**Prevention**:
```python
# Configure timeouts and retries
@dlt.source
def prestashop():
    config = {
        "request_timeout": 120,  # seconds
        "max_retries": 3,
        "retry_wait": 30,
        "max_concurrent_requests": 2
    }
```

---

## Summary: Key Error Patterns and Actions

| Source | Error Type | HTTP Code | Action |
|--------|------------|-----------|--------|
| **GA4** | Quota Exceeded | 429 | Reduce request rate, wait for reset |
| **GA4** | Sampling | Response | Split date ranges, add row limits |
| **GA4** | Auth Failure | 401/403 | Refresh OAuth token, check scopes |
| **GA4** | Invalid Property | 400/403 | Verify property ID format and access |
| **Meta** | Rate Limit | 429 | Exponential backoff, reduce parallelism |
| **Meta** | Token Expired | 190 | Refresh long-lived token |
| **Meta** | Permission Denied | 290 | Submit for app review |
| **Meta** | API Version | 400 | Update connector, monitor changelog |
| **PrestaShop** | Auth Failed | 401 | Verify API key, check Basic Auth format |
| **PrestaShop** | Permission Denied | 403 | Configure ACL permissions |
| **PrestaShop** | SSL Error | - | Update certificates, configure SSL context |
| **PrestaShop** | Server Error | 500 | Retry, check server logs |

---

## General Best Practices

1. **Implement Retry Logic**: All connectors should use exponential backoff for transient failures
2. **Monitor Rate Limits**: Track API usage headers and quota status
3. **Token Management**: Implement secure token storage and refresh mechanisms
4. **Incremental Loading**: Use date cursors or incremental syncs to reduce data volume
5. **Error Logging**: Log full error responses for debugging
6. **Health Checks**: Add pre-flight checks before pipeline execution
7. **Alerting**: Monitor for repeated failures and alert on quota exhaustion

---

*Last Updated: April 2026*
*Sources: Google Analytics Data API docs, Meta Marketing API docs, PrestaShop WebService docs*
