# Recipe Catalog API Client Guide

## Overview

This guide provides instructions for integrating with the Recipe Catalog API's recipe import functionality. The API allows external applications (such as browser extensions) to import recipes in Schema.org Recipe format.

**Base URL**: `http://localhost:8000` (development) or your deployed instance URL

**API Version**: 1.0.0

---

## Authentication

### Cookie Session Authentication

The API authenticates with httpOnly cookies. Logging in sets an `access_token`
cookie that your HTTP client's cookie jar sends automatically. The token is never
exposed to JavaScript and is **not** returned in the response body.

State-changing requests (POST, PUT, PATCH, DELETE) additionally require a CSRF
token, using the double-submit cookie pattern.

### Logging In

**Endpoint**: `POST /api/v1/auth/login`

**Request Body**:

```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response**:

```json
{
  "message": "Login successful",
  "csrf_token": "a1b2c3d4..."
}
```

The response sets three cookies:

| Cookie | Readable by JS | Lifetime |
|---|---|---|
| `access_token` | No (httpOnly) | 15 minutes (`ACCESS_TOKEN_EXPIRE_MINUTES`) |
| `refresh_token` | No (httpOnly) | 30 days (`REFRESH_TOKEN_EXPIRE_DAYS`) |
| `csrf_token` | Yes | 30 days |

### Making Authenticated Requests

Send the cookies with every request, and include the CSRF token in an
`X-CSRF-Token` header on state-changing methods:

```http
Cookie: access_token=<...>; csrf_token=<...>
X-CSRF-Token: <csrf_token>
```

Omitting the CSRF header on a POST, PUT, PATCH, or DELETE returns
`403 csrf_token_invalid`, even when authentication is otherwise valid.

**Token expiration**: access tokens expire after 15 minutes. Call
`POST /api/v1/auth/refresh` to issue a new one from the `refresh_token` cookie.

**Bearer alternative**: the API also accepts `Authorization: Bearer <jwt>` if you
hold a token by other means, but login does not return one — the cookie session
above is the supported path. CSRF protection applies either way.

---

## Import Recipes Endpoint

### `POST /api/v1/import/recipes/json`

Import one or more recipes from JSON data in Schema.org Recipe format.

#### Authentication Required

✅ Yes - Requires a logged-in cookie session plus an `X-CSRF-Token` header

#### Rate Limiting

- **Limit**: 20,000 requests per hour per IP address
- **Headers**: Rate limit information included in response headers

#### Request Parameters

**Headers**:

```http
Cookie: access_token=<...>; csrf_token=<...>
X-CSRF-Token: <csrf_token>
Content-Type: application/json
```

**Request Body** (JSON):

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `recipes` | Array<Object> | Yes | - | Array of recipe objects in Schema.org format |
| `duplicate_handling` | String | No | "skip" | How to handle duplicates: "skip", "update", or "create" |
| `collection_id` | Integer | No | null | Optional collection ID to add imported recipes to |

**Duplicate Handling Options**:

- `"skip"`: Skip recipes with matching names (by exact name match)
- `"update"`: Update existing recipes with matching names with new data
- `"create"`: Always create new recipes (allows duplicates)

#### Request Example

```json
{
  "recipes": [
    {
      "name": "Classic Chocolate Chip Cookies",
      "description": "Chewy and delicious homemade chocolate chip cookies",
      "image": "https://example.com/cookies.jpg",
      "author": ["Jane Baker"],
      "datePublished": "2024-01-15",
      "recipeYield": "24 cookies",
      "prepTime": "PT15M",
      "cookTime": "PT12M",
      "totalTime": "PT27M",
      "recipeCategory": "Dessert",
      "recipeCuisine": "American",
      "recipeIngredient": [
        "2 1/4 cups all-purpose flour",
        "1 tsp baking soda",
        "1 tsp salt",
        "1 cup butter, softened",
        "3/4 cup granulated sugar",
        "3/4 cup packed brown sugar",
        "2 large eggs",
        "2 tsp vanilla extract",
        "2 cups chocolate chips"
      ],
      "recipeInstructions": [
        "Preheat oven to 375°F (190°C).",
        "Mix flour, baking soda, and salt in a bowl.",
        "In a separate bowl, cream together butter and sugars until fluffy.",
        "Beat in eggs and vanilla extract.",
        "Gradually blend in flour mixture, then fold in chocolate chips.",
        "Drop rounded tablespoons of dough onto ungreased cookie sheets.",
        "Bake for 9-11 minutes or until golden brown."
      ],
      "keywords": "chocolate chip, cookies, baking, dessert",
      "nutrition": {
        "calories": "150 calories",
        "fatContent": "8g",
        "carbohydrateContent": "20g",
        "proteinContent": "2g"
      },
      "url": "https://example.com/recipes/chocolate-chip-cookies"
    }
  ],
  "duplicate_handling": "skip",
  "collection_id": 5
}
```

#### Response Format

**Success Response** (200 OK):

```json
{
  "success": true,
  "message": "Imported 1 new recipes, updated 0, skipped 0, failed 0",
  "details": {
    "total": 1,
    "created": 1,
    "updated": 0,
    "skipped": 0,
    "failed": 0,
    "errors": []
  }
}
```

**Partial Success Response** (200 OK with errors):

```json
{
  "success": true,
  "message": "Imported 2 new recipes, updated 1, skipped 1, failed 1",
  "details": {
    "total": 5,
    "created": 2,
    "updated": 1,
    "skipped": 1,
    "failed": 1,
    "errors": [
      {
        "index": 3,
        "name": "Invalid Recipe",
        "error": "Missing required field: name"
      }
    ]
  }
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `success` | Boolean | Whether the overall operation succeeded |
| `message` | String | Human-readable summary of import results |
| `details.total` | Integer | Total number of recipes in the import |
| `details.created` | Integer | Number of new recipes created |
| `details.updated` | Integer | Number of existing recipes updated |
| `details.skipped` | Integer | Number of recipes skipped (duplicates) |
| `details.failed` | Integer | Number of recipes that failed to import |
| `details.errors` | Array | List of error details for failed imports |

---

## Error Responses

### 401 Unauthorized

Missing or invalid authentication token.

```json
{
  "detail": "Could not validate credentials"
}
```

**Solution**: Log in again to refresh the `access_token` cookie. Access tokens
expire after 15 minutes; `POST /api/v1/auth/refresh` issues a new one.

### 404 Not Found

Collection ID specified but not found or doesn't belong to user.

```json
{
  "detail": "Collection not found"
}
```

**Solution**: Verify the collection ID exists and belongs to the authenticated user.

### 429 Too Many Requests

Rate limit exceeded.

```json
{
  "detail": "Rate limit exceeded"
}
```

**Solution**: Wait before making additional requests. The API allows 20,000 requests per hour.

### 500 Internal Server Error

Database or server error during import.

```json
{
  "detail": "Failed to save recipes: [error details]"
}
```

**Solution**: Check the error message for details. Contact support if the issue persists.

---

## Schema.org Recipe Format

The API expects recipes in [Schema.org Recipe](https://schema.org/Recipe) format. This is a widely-used standard for recipe markup.

### Required Fields

- `name` (String): Recipe name

### Optional Fields

All other fields are optional but recommended for better data quality:

- `description` (String): Recipe description
- `image` (String or Array): Single image URL string, or array of URLs, or array of image objects with `{url, data, mimeType}`
- `author` (Array<String>): Recipe author names (e.g., `["Jane Baker"]`)
- `datePublished` (String): Publication date (ISO 8601 or YYYY-MM-DD)
- `recipeYield` (String): Serving size (e.g., "4 servings", "12 cookies")
- `prepTime` (String): Preparation time in ISO 8601 duration format (e.g., "PT15M" = 15 minutes)
- `cookTime` (String): Cooking time in ISO 8601 duration format
- `totalTime` (String): Total time in ISO 8601 duration format
- `recipeCategory` (String or Array<String>): Recipe categories (e.g., "Dessert", "Main Course")
- `recipeCuisine` (String or Array<String>): Cuisine types (e.g., "Italian", "Mexican")
- `recipeIngredient` (Array<String>): List of ingredients
- `recipeInstructions` (String, Array<String>, or Array<Object>): Cooking instructions (see format details below)
- `keywords` (String): Comma-separated keywords
- `nutrition` (Object): Nutritional information (flexible schema)
- `url` (String): Source URL of the recipe
- `equipment` (Array<String>): Equipment needed for the recipe
- `notes` (String): Additional notes or tips
- `aggregateRating` (Object): Rating information (flexible schema)

### ISO 8601 Duration Format

Time durations use the ISO 8601 format: `PT<hours>H<minutes>M`

Examples:

- `PT15M` = 15 minutes
- `PT1H30M` = 1 hour 30 minutes
- `PT45M` = 45 minutes
- `PT2H` = 2 hours

### Recipe Instructions Format

Instructions can be provided in multiple formats:

**Array of strings** (recommended for simplicity):

```json
[
  "Preheat oven to 375°F.",
  "Mix dry ingredients.",
  "Combine wet ingredients.",
  "Bake for 20 minutes."
]
```

**Single string** (will be stored as-is):

```json
"Preheat oven to 375°F. Mix dry ingredients. Combine wet ingredients. Bake for 20 minutes."
```

**Array of HowToStep objects** (Schema.org standard):

```json
[
  {
    "@type": "HowToStep",
    "text": "Preheat oven to 375°F."
  },
  {
    "@type": "HowToStep",
    "text": "Mix dry ingredients."
  }
]
```

Note: The API extracts the instruction text regardless of format.

### Image Format Options

Images can be provided in several formats:

**Simple URL string**:

```json
"image": "https://example.com/recipe.jpg"
```

**Array of URL strings**:

```json
"image": [
  "https://example.com/recipe1.jpg",
  "https://example.com/recipe2.jpg"
]
```

**Array of image objects** (with optional base64 data):

```json
"image": [
  {
    "url": "https://example.com/recipe.jpg",
    "data": "base64-encoded-image-data",
    "mimeType": "image/jpeg"
  }
]
```

Note: The API will attempt to fetch and encode images from URLs automatically. If you provide base64 `data`, it will be stored; otherwise, the API fetches the image.

### Author Format

Authors should be provided as an array of strings:

```json
"author": ["Jane Baker", "John Doe"]
```

Or a single string (will be converted to array):

```json
"author": "Jane Baker"
```

---

## Complete Code Examples

### Python Example

```python
import requests
import json

class RecipeCatalogClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()  # holds the auth cookies
        self.csrf_token = None
    
    def login(self, email: str, password: str) -> bool:
        """Authenticate. Cookies are stored on the session; keep the CSRF token."""
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"email": email, "password": password}
        )

        if response.status_code == 200:
            self.csrf_token = response.json()["csrf_token"]
            return True
        return False
    
    def import_recipes(
        self,
        recipes: list,
        duplicate_handling: str = "skip",
        collection_id: int = None
    ) -> dict:
        """Import recipes to Recipe Catalog."""
        if not self.csrf_token:
            raise Exception("Not authenticated. Call login() first.")

        headers = {
            "X-CSRF-Token": self.csrf_token,
            "Content-Type": "application/json"
        }
        
        payload = {
            "recipes": recipes,
            "duplicate_handling": duplicate_handling
        }
        
        if collection_id:
            payload["collection_id"] = collection_id
        
        response = self.session.post(
            f"{self.base_url}/api/v1/import/recipes/json",
            headers=headers,
            json=payload
        )
        
        return response.json()


# Usage
client = RecipeCatalogClient("http://localhost:8000")

# Authenticate
if client.login("user@example.com", "password"):
    # Import recipes
    recipes = [
        {
            "name": "Test Recipe",
            "description": "A test recipe",
            "recipeIngredient": ["1 cup flour", "2 eggs"],
            "recipeInstructions": ["Mix ingredients", "Bake at 350°F"]
        }
    ]
    
    result = client.import_recipes(
        recipes=recipes,
        duplicate_handling="skip",
        collection_id=1
    )
    
    print(f"Import result: {result['message']}")
    print(f"Created: {result['details']['created']}")
    print(f"Failed: {result['details']['failed']}")
```

### JavaScript/TypeScript Example

```typescript
interface Recipe {
  name: string;
  description?: string;
  image?: string[];
  recipeIngredient?: string[];
  recipeInstructions?: any[];
  [key: string]: any;
}

interface ImportResult {
  success: boolean;
  message: string;
  details: {
    total: number;
    created: number;
    updated: number;
    skipped: number;
    failed: number;
    errors: Array<{ index: number; name: string; error: string }>;
  };
}

class RecipeCatalogClient {
  private baseUrl: string;
  private csrfToken: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async login(email: string, password: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/auth/login`, {
        method: 'POST',
        credentials: 'include',  // required: auth travels in cookies
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (response.ok) {
        const data = await response.json();
        this.csrfToken = data.csrf_token;
        return true;
      }
      return false;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  }

  async importRecipes(
    recipes: Recipe[],
    duplicateHandling: 'skip' | 'update' | 'create' = 'skip',
    collectionId?: number
  ): Promise<ImportResult> {
    if (!this.csrfToken) {
      throw new Error('Not authenticated. Call login() first.');
    }

    const payload: any = {
      recipes,
      duplicate_handling: duplicateHandling
    };

    if (collectionId) {
      payload.collection_id = collectionId;
    }

    const response = await fetch(`${this.baseUrl}/api/v1/import/recipes/json`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'X-CSRF-Token': this.csrfToken,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Import failed');
    }

    return await response.json();
  }
}

// Usage
const client = new RecipeCatalogClient('http://localhost:8000');

// Authenticate
await client.login('user@example.com', 'password');

// Import recipes
const recipes: Recipe[] = [
  {
    name: 'Chocolate Cake',
    description: 'Delicious chocolate cake',
    recipeIngredient: ['2 cups flour', '1 cup cocoa powder'],
    recipeInstructions: ['Mix ingredients', 'Bake at 350°F for 30 minutes']
  }
];

const result = await client.importRecipes(recipes, 'skip', 1);
console.log(`Import result: ${result.message}`);
console.log(`Created: ${result.details.created}`);
console.log(`Failed: ${result.details.failed}`);
```

### cURL Example

```bash
# Step 1: Log in, saving cookies to a jar and keeping the CSRF token
CSRF=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -c cookies.txt \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password"
  }' | jq -r '.csrf_token')

# Step 2: Import recipes, sending the cookies back plus the CSRF header
curl -X POST http://localhost:8000/api/v1/import/recipes/json \
  -b cookies.txt \
  -H "X-CSRF-Token: $CSRF" \
  -H "Content-Type: application/json" \
  -d '{
    "recipes": [
      {
        "name": "Test Recipe",
        "description": "A test recipe",
        "recipeIngredient": ["1 cup flour", "2 eggs"],
        "recipeInstructions": ["Mix ingredients", "Bake"]
      }
    ],
    "duplicate_handling": "skip",
    "collection_id": 1
  }'
```

---

## Browser Extension Integration

### Recommended Workflow

1. **Authentication Flow**:
   - Prompt user to log in via extension popup
   - Store access token securely in browser storage
   - Refresh token before it expires (30 minutes)

2. **Recipe Extraction**:
   - Extract Schema.org Recipe JSON-LD from web pages
   - Validate required fields (at minimum, `name`)
   - Show preview to user before import

3. **Import Execution**:
   - Call `import_recipes_json` endpoint with extracted recipe(s)
   - Handle duplicate detection based on user preference
   - Optionally let user select a collection

4. **Error Handling**:
   - Handle authentication errors (prompt re-login)
   - Handle rate limiting (show user-friendly message)
   - Display import results (created, skipped, failed)

### Token Storage Best Practices

The `access_token` and `refresh_token` are httpOnly cookies — your extension
cannot read them, and does not need to. The browser attaches them to requests
as long as you send credentials. Only the CSRF token needs storing.

**Chrome Extension Example**:

```javascript
// Store the CSRF token returned by login
await chrome.storage.local.set({ csrfToken });

// Retrieve it for state-changing requests
const { csrfToken } = await chrome.storage.local.get(['csrfToken']);

await fetch(`${baseUrl}/api/v1/import/recipes/json`, {
  method: 'POST',
  credentials: 'include',            // sends the httpOnly auth cookies
  headers: { 'X-CSRF-Token': csrfToken, 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
});

// Clear on logout
await chrome.storage.local.remove('csrfToken');
```

**Security Notes**:

- Use `chrome.storage.local` (not `localStorage` in content scripts)
- Request host permissions for the API origin so cookies are sent
- Clear the stored CSRF token on logout
- Handle 401s by calling `POST /api/v1/auth/refresh`, then retrying once

---

## API Testing with Postman

### Collection Setup

1. Create a new collection called "Recipe Catalog API"
2. Set collection variable `baseUrl` = `http://localhost:8000`
3. Set collection variable `csrfToken` (will be set after login)

### Login Request

```http
POST {{baseUrl}}/api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password"
}

// In Tests tab, add:
pm.collectionVariables.set("csrfToken", pm.response.json().csrf_token);
// Auth cookies are stored by the client's cookie jar automatically.
```

### Import Request

```http
POST {{baseUrl}}/api/v1/import/recipes/json
X-CSRF-Token: {{csrfToken}}
Content-Type: application/json

{
  "recipes": [
    {
      "name": "Test Recipe",
      "recipeIngredient": ["1 cup flour"],
      "recipeInstructions": ["Mix and bake"]
    }
  ],
  "duplicate_handling": "skip"
}
```

---

## Troubleshooting

### Common Issues

**Issue**: "Could not validate credentials"

- **Cause**: Missing, expired, or invalid access token
- **Solution**: Re-authenticate using the login endpoint

**Issue**: "Collection not found"

- **Cause**: Invalid collection ID or collection belongs to different user
- **Solution**: Verify collection ID with `GET /api/v1/collections/` endpoint

**Issue**: Import succeeds but no recipes created

- **Cause**: All recipes skipped due to duplicate names
- **Solution**: Change `duplicate_handling` to `"update"` or `"create"`

**Issue**: Some recipes fail to import

- **Cause**: Invalid recipe data format
- **Solution**: Check `details.errors` array in response for specific error messages

**Issue**: "Rate limit exceeded"

- **Cause**: Too many requests in a short time
- **Solution**: Implement request throttling or wait before retrying

---

## Support & Additional Resources

### Documentation

- **API Base Documentation**: See `backend/README.md`
- **Schema.org Recipe Spec**: <https://schema.org/Recipe>
- **JSON-LD Format**: <https://json-ld.org/>

### Development

- **Backend Source**: `backend/app/api/import_recipes.py`
- **Format Converter**: `backend/app/utils/recipe_format.py`

### Contact

For issues or questions about the API, please refer to the main project documentation.

---

**Document Version**: 1.0  
**Last Updated**: November 16, 2025  
**API Version**: 1.0.0
