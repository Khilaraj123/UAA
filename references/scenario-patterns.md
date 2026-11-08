# Reference: Test Scenario Patterns & JSON Templates

## 1. Happy Path Template
```json
{
  "scenario_id": "SCEN-001-GET-USERS-HAPPY",
  "endpoint_id": "rest:GET:/api/v1/users",
  "title": "List users returns 200 with user list",
  "category": "happy_path",
  "priority": "P0",
  "rationale": "Verify basic read contract for authenticated users",
  "request": {
    "method": "GET",
    "path": "/api/v1/users",
    "headers": {
      "Authorization": "Bearer ${UAA_TEST_TOKEN}"
    }
  },
  "assertions": [
    { "type": "status", "expected": 200 },
    { "type": "content_type", "expected": "application/json" },
    { "type": "json_type", "path": "$", "expected": "array" }
  ],
  "safety": {
    "is_safe_read": true,
    "has_external_effects": false,
    "is_destructive": false
  },
  "enabled": true
}
```

## 2. Authentication Missing Template
```json
{
  "scenario_id": "SCEN-002-GET-USERS-UNAUTH",
  "endpoint_id": "rest:GET:/api/v1/users",
  "title": "List users without token returns 401 Unauthorized",
  "category": "auth_missing",
  "priority": "P0",
  "rationale": "Ensure protected endpoint fails closed without credentials",
  "request": {
    "method": "GET",
    "path": "/api/v1/users"
  },
  "assertions": [
    { "type": "status", "expected": 401 }
  ],
  "safety": {
    "is_safe_read": true,
    "has_external_effects": false,
    "is_destructive": false
  },
  "enabled": true
}
```

## 3. Input Validation (Missing Required Field)
```json
{
  "scenario_id": "SCEN-003-POST-USERS-INVALID",
  "endpoint_id": "rest:POST:/api/v1/users",
  "title": "Create user with missing email returns 400/422",
  "category": "input_validation",
  "priority": "P1",
  "rationale": "Verify server rejects invalid payload structure",
  "request": {
    "method": "POST",
    "path": "/api/v1/users",
    "headers": {
      "Authorization": "Bearer ${UAA_TEST_TOKEN}",
      "Content-Type": "application/json"
    },
    "body": {
      "name": "Test User"
    }
  },
  "assertions": [
    { "type": "status", "expected": 422 }
  ],
  "safety": {
    "is_safe_read": false,
    "has_external_effects": false,
    "is_destructive": false
  },
  "enabled": true
}
```

