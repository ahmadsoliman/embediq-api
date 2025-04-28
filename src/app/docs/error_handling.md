# Error Handling

This document describes how errors are handled in the EmbedIQ backend API.

## Error Response Format

All API errors follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

For validation errors, the response includes more detailed information:

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Error message for this field",
      "type": "validation_error_type"
    }
  ]
}
```

## HTTP Status Codes

The API uses standard HTTP status codes to indicate the success or failure of a request:

| Status Code | Description |
|-------------|-------------|
| 200 | OK - The request was successful |
| 201 | Created - A new resource was successfully created |
| 204 | No Content - The request was successful, but there is no content to return |
| 400 | Bad Request - The request was invalid or cannot be served |
| 401 | Unauthorized - Authentication is required or failed |
| 403 | Forbidden - The authenticated user doesn't have permission |
| 404 | Not Found - The requested resource doesn't exist |
| 409 | Conflict - The request conflicts with the current state |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Something went wrong on the server |

## Common Error Types

### Authentication Errors (401)

Authentication errors occur when the JWT token is invalid, expired, or missing:

```json
{
  "detail": "Invalid token: Token signature verification failed"
}
```

### Authorization Errors (403)

Authorization errors occur when the authenticated user doesn't have permission to perform an action:

```json
{
  "detail": "Not enough permissions"
}
```

### Not Found Errors (404)

Not found errors occur when the requested resource doesn't exist:

```json
{
  "detail": "Document with ID '123' not found"
}
```

### Validation Errors (422)

Validation errors occur when the request data doesn't meet the validation requirements:

```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "tags"],
      "msg": "value is not a valid list",
      "type": "type_error.list"
    }
  ]
}
```

### Rate Limit Errors (429)

Rate limit errors occur when the client has sent too many requests in a given time period:

```json
{
  "detail": "Rate limit exceeded. Try again in 30 seconds."
}
```

### Server Errors (500)

Server errors occur when something goes wrong on the server:

```json
{
  "detail": "Internal server error"
}
```

## Error Logging

All errors are logged on the server for debugging and monitoring purposes. The logs include:

- Error message
- Error stack trace
- Request information (method, path, headers, body)
- User information (if authenticated)
- Timestamp

## Error Handling Best Practices

When working with the EmbedIQ API, follow these best practices for error handling:

1. **Check HTTP status codes**: Always check the HTTP status code of the response to determine if the request was successful.

2. **Parse error messages**: Parse the error message from the response body to provide meaningful feedback to users.

3. **Handle specific error types**: Implement specific handling for different types of errors (authentication, validation, etc.).

4. **Implement retry logic**: For transient errors (e.g., rate limiting), implement retry logic with exponential backoff.

5. **Log errors**: Log errors on the client side for debugging and monitoring.

## Example Error Handling

### JavaScript Example

```javascript
async function fetchDocuments() {
  try {
    const response = await fetch('https://api.embediq.com/api/v1/documents', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      
      if (response.status === 401) {
        // Handle authentication error
        console.error('Authentication error:', errorData.detail);
        // Redirect to login page or refresh token
      } else if (response.status === 403) {
        // Handle authorization error
        console.error('Authorization error:', errorData.detail);
        // Show permission denied message
      } else if (response.status === 429) {
        // Handle rate limit error
        console.error('Rate limit exceeded:', errorData.detail);
        // Implement retry with backoff
      } else {
        // Handle other errors
        console.error('API error:', errorData.detail);
        // Show generic error message
      }
      
      return null;
    }
    
    return await response.json();
  } catch (error) {
    // Handle network errors
    console.error('Network error:', error);
    // Show network error message
    return null;
  }
}
```

### Python Example

```python
import requests

def fetch_documents(token):
    try:
        response = requests.get(
            'https://api.embediq.com/api/v1/documents',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            # Handle authentication error
            print(f"Authentication error: {e.response.json()['detail']}")
        elif e.response.status_code == 403:
            # Handle authorization error
            print(f"Authorization error: {e.response.json()['detail']}")
        elif e.response.status_code == 429:
            # Handle rate limit error
            print(f"Rate limit exceeded: {e.response.json()['detail']}")
        else:
            # Handle other errors
            print(f"API error: {e.response.json()['detail']}")
        
        return None
    except requests.exceptions.RequestException as e:
        # Handle network errors
        print(f"Network error: {str(e)}")
        return None
```
