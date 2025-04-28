# Authentication

EmbedIQ uses Auth0 for authentication and authorization. This document describes how authentication works in the EmbedIQ backend.

## Authentication Flow

1. Users authenticate with Auth0 through the frontend application
2. Auth0 issues a JWT token to the authenticated user
3. The frontend includes this token in API requests to the backend
4. The backend validates the token and extracts user information

## JWT Tokens

JWT (JSON Web Token) is an open standard for securely transmitting information between parties as a JSON object. In EmbedIQ, JWT tokens are used to authenticate API requests.

### Token Structure

A JWT token consists of three parts:

1. **Header**: Contains the token type and signing algorithm
2. **Payload**: Contains claims about the user and token metadata
3. **Signature**: Used to verify the token's authenticity

### Token Claims

The JWT token payload contains the following claims:

- `sub`: The subject of the token (user ID)
- `iss`: The issuer of the token (Auth0 domain)
- `aud`: The audience of the token (API identifier)
- `exp`: The expiration time of the token
- `iat`: The time the token was issued
- `permissions`: The permissions granted to the user
- `scope`: The scopes granted to the user

## Using Authentication in API Requests

To authenticate API requests, include the JWT token in the `Authorization` header:

```
Authorization: Bearer your_jwt_token
```

Example using curl:

```bash
curl -X GET \
  https://api.embediq.com/api/v1/documents \
  -H 'Authorization: Bearer your_jwt_token'
```

Example using JavaScript:

```javascript
const response = await fetch('https://api.embediq.com/api/v1/documents', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

## Authentication Endpoints

The EmbedIQ backend provides the following authentication-related endpoints:

### Validate Token

```
GET /api/v1/auth/token
```

This endpoint validates the JWT token and returns token information.

**Response:**

```json
{
  "valid": true,
  "user_id": "auth0|123456789",
  "permissions": ["read:documents", "write:documents"],
  "scopes": ["openid", "profile", "email"],
  "token_metadata": {
    "iss": "https://your-auth0-domain.auth0.com/",
    "aud": "your-api-identifier",
    "exp": 1619712000,
    "iat": 1619625600
  }
}
```

### Get User Profile

```
GET /api/v1/auth/profile
```

This endpoint returns user profile information based on the validated JWT token.

**Response:**

```json
{
  "profile": {
    "user_id": "auth0|123456789",
    "email": "user@example.com",
    "name": "John Doe",
    "nickname": "johndoe",
    "picture": "https://example.com/profile.jpg",
    "email_verified": true,
    "updated_at": "2023-04-28T12:00:00Z"
  }
}
```

## Error Handling

If authentication fails, the API returns a 401 Unauthorized response:

```json
{
  "detail": "Invalid token: Token signature verification failed"
}
```

Common authentication errors:

- **Invalid token**: The token is malformed or has an invalid signature
- **Expired token**: The token has expired
- **Invalid audience**: The token was issued for a different audience
- **Invalid issuer**: The token was issued by an untrusted issuer
- **Insufficient permissions**: The user lacks the required permissions

## Permissions and Authorization

EmbedIQ uses a permission-based authorization model. Permissions are included in the JWT token and are used to determine what actions a user can perform.

Common permissions:

- `read:documents`: Allows reading documents
- `write:documents`: Allows creating and updating documents
- `delete:documents`: Allows deleting documents
- `admin`: Grants administrative privileges

## Testing Authentication

For testing purposes, you can obtain a test token using the Auth0 Management API or the Auth0 Dashboard. See the [Testing](testing.md) documentation for more details.
