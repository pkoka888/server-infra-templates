---
name: metabase-embedding
description: Embed Metabase dashboards and questions in other applications. Use when creating embedded analytics, white-labeling, or sharing dashboards externally.
---

# Metabase Embedding Skill

This skill provides guidance for embedding Metabase dashboards and questions.

## Embedding Options

### 1. Public Embed
```html
<iframe src="https://metabase.expc.cz/public/dashboard/xxx"></iframe>
```

### 2. Signed Embed (Recommended)
```javascript
// Generate signed URL
const embedUrl = await metabase.getEmbeddingUrl({
  resource: { dashboard: 1 },
  params: { customer_id: 123 }
});
```

### 3. Interactive Embed
```javascript
// Full embedding with SDK
import { MetabaseEmbeddingSdk } from "@metabase/embedding-sdk";

const mb = await MetabaseEmbeddingSdk.init({
  metabaseUrl: "https://metabase.expc.cz",
  apiKey: "your-api-key"
});
```

## Embedding Types

| Type | Use Case | Security |
|------|----------|-----------|
| Public | Public dashboards | Low |
| Signed | Customer-facing | Medium |
| Interactive | Full SDK | High |

## Configuration

### Enable Embedding

1. Go to Admin > Settings > Embedding
2. Enable embedding for the application
3. Configure allowed origins

### Create Embeddable Dashboard

```bash
# Make dashboard public
curl -X PUT \
  -H "X-API-Key: $MB_API_KEY" \
  -H "Content-Type: application/json" \
  https://metabase.expc.cz/api/dashboard/1 \
  -d '{"enable_embedding": true}'
```

## Parameter Passing

### Filter Parameters
```javascript
// Pass filters to embedded dashboard
const embedUrl = await metabase.getEmbeddingUrl({
  resource: { dashboard: 1 },
  params: {
    "date_filter": "2024-01-01",
    "region": "US"
  }
});
```

### JWT Signing
```javascript
import jwt from "jsonwebtoken";

const token = jwt.sign(
  {
    resource: { dashboard: 1 },
    params: { customer_id: 123 }
  },
  "your-jwt-secret"
);
```

## Use Cases

### 1. Customer Portal
```html
<iframe 
  src="https://metabase.expc.cz/embed/dashboard/xxx#bordered=false&titled=true"
  frameborder="0"
  allowtransparency
></iframe>
```

### 2. White-Labeled Analytics
- Remove Metabase branding
- Custom colors matching your brand
- Custom domain

### 3. Embedded in SaaS
- Use iframes with signed URLs
- Filter data by tenant
- Track usage per customer

## Security Best Practices

1. **Use signed URLs** - Never use public embeds for sensitive data
2. **Filter data** - Use `params` to restrict data access
3. **Rotate secrets** - Change JWT secrets regularly
4. **Audit logs** - Monitor embed usage
5. **Allowed origins** - Configure allowed origins in Metabase

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/embed/` | Get embed config |
| `POST /api/embed/dashboard/:id` | Create dashboard embed |
| `GET /api/embed/card/:id` | Get card embed URL |

## Example: Full Embed with SDK

```javascript
import { MetabaseEmbeddingSdk } from "@metabase/embedding-sdk";

async function initEmbed() {
  const mb = await MetabaseEmbeddingSdk.init({
    metabaseUrl: "https://metabase.expc.cz",
    apiKey: process.env.METABASE_API_KEY,
  });

  const dashboard = await mb.dashboard({
    dashboardId: 1,
    showTitle: true,
    showFilters: true,
    theme: "transparent",
  });

  return dashboard;
}
```

## Troubleshooting

- **CORS errors**: Add origin to allowed origins
- **401 errors**: Check API key validity
- **Blank iframe**: Check embedding is enabled
- **Filters not working**: Verify params are passed correctly
