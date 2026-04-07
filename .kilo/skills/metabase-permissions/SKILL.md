---
name: metabase-permissions
description: Manage Metabase permissions, groups, and row-level security. Use when setting up access control, managing user roles, or configuring data sandboxing.
---

# Metabase Permissions Skill

This skill provides guidance for managing Metabase permissions and access control.

## Permission Levels

### 1. Collection Permissions
| Permission | Description |
|------------|-------------|
| `none` | No access |
| `read` | View items |
| `write` | Edit items |
| `curate` | Edit + manage |

### 2. Data Permissions
| Permission | Description |
|------------|-------------|
| `no` | No access |
| `limited` | Subset of schemas |
| `all` | Full access |
| `block` | Explicitly block |

## Groups

### Default Groups
- **Administrators** - Full access
- **All Users** - Base permissions
- **Data** - Can access data
- **Read Only** - View only

### Custom Groups
```bash
# Create group
curl -X POST \
  -H "X-API-Key: $MB_API_KEY" \
  -H "Content-Type: application/json" \
  https://metabase.expc.cz/api/group \
  -d '{"name": "Marketing Team"}'
```

## Managing Permissions

### Via API

```bash
# Update collection permissions
curl -X PUT \
  -H "X-API-Key: $MB_API_KEY" \
  -H "Content-Type: application/json" \
  https://metabase.expc.cz/api/collections/graph \
  -d '{
    "groups": {
      "1": { "1": "write" }
    }
  }'
```

### Via Database

```sql
-- View permissions
SELECT * FROM permissions GROUP_id, object;

-- View group members
SELECT u.email, g.name 
FROM users u 
JOIN group_members gm ON u.id = gm.user_id 
JOIN groups g ON gm.group_id = g.id;
```

## Row-Level Security (Sandboxing)

### Configure Data Sandbox

```bash
# Create segment
curl -X POST \
  -H "X-API-Key: $MB_API_KEY" \
  -H "Content-Type: application/json" \
  https://metabase.expc.cz/api/segment \
  -d '{
    "name": "Customer Dashboard",
    "description": "See only own data",
    "table_id": 12,
    "definition": {
      "filter": ["=", ["field-id", 123], ["variable", "current_user_id"]]
    }
  }'
```

### Sandbox Field Values
```sql
-- Filter sensitive data
UPDATE permissions 
SET object = 'schema/123' 
WHERE group_id = 5;
```

## User Management

### Create User
```bash
curl -X POST \
  -H "X-API-Key: $MB_API_KEY" \
  -H "Content-Type: application/json" \
  https://metabase.expc.cz/api/user \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com"
  }'
```

### Deactivate User
```bash
curl -X DELETE \
  -H "X-API-Key: $MB_API_KEY" \
  https://metabase.expc.cz/api/user/5
```

### Set User Password
```bash
curl -X PUT \
  -H "X-API-Key: $MB_API_KEY" \
  -H "Content-Type: application/json" \
  https://metabase.expc.cz/api/session/password \
  -d '{
    "user_id": 5,
    "password": "newpassword123"
  }'
```

## Best Practices

1. **Use groups** - Assign permissions to groups, not users
2. **Least privilege** - Start with minimal access
3. **Audit regularly** - Review permissions quarterly
4. **Document policies** - Keep permission matrix
5. **Use sandboxes** - For multi-tenant data

## Permission Matrix

| Group | Collections | Data | Users | Settings |
|-------|-------------|------|-------|----------|
| Admin | Full | Full | Full | Full |
| Editor | Write | All | None | None |
| Analyst | Read | Limited | None | None |
| Viewer | Read | Limited | None | None |
| Customer | Read | Sandbox | None | None |

## Troubleshooting

### User Can't Access
1. Check group membership
2. Verify data permissions
3. Check collection access

### Permission Denied
1. Verify API key has admin rights
2. Check group permissions graph
3. Clear cache and retry

### Sync Issues
```bash
# Force permission sync
curl -X POST \
  -H "X-API-Key: $MB_API_KEY" \
  https://metabase.expc.cz/api/permissions/graph
```

## Key Tables

| Table | Purpose |
|-------|---------|
| `permissions` | Permission entries |
| `permissions_group` | Group membership |
| `group` | Groups |
| `user` | Users |
| `collection` | Collections |
| `collection_permission` | Collection perms |
