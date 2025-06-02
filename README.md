# Finance Tracker API - Personal Finance Dashboard
## Overview
This RESTful API powers the backend of the Financial Tracker application — a full-stack solution that allows authenticated users to manage their personal finances in a secure, intuitive way.

The API exposes structured endpoints for:
- Adding, editing, and deleting income/expenditure entries (with support for automatic repetition)
- Managing recurring and one-off expenditures
- Tracking a user's disposable income budget and spending
- Retrieving calendar-based and summary views of financial data
- Setting a preferred currency, used across all frontend displays

Key features include:
- **User isolation**: All financial records are scoped strictly to the authenticated user.
- **Repeat logic**: Recurring entries (weekly/monthly) are automatically generated and grouped via `repeat_group_id`.
- **Currency support**: Each user selects their currency, and all financial responses return values with symbols.
- **Performance-optimized summaries**: Calendar, weekly, and monthly summaries are pre-aggregated for efficient frontend rendering.
- **Security**: All endpoints require authentication; permissions prevent unauthorized access or manipulation of any other user’s data.

This API is built with Django REST Framework, following best practices for structure, modularity, and extensibility. It serves a React-based frontend and is deployed separately to a cloud platform.

## Authentication
All endpoints related to financial data are protected and require the user to be authenticated using JWT tokens issued by the `dj-rest-auth` package.

### Login & Token Flow
1. **Login** - The user sends their credentials. On success, the server sets the access and refresh tokens in secure, HTTP-only cookies:
```
POST /dj-rest-auth/login/
```
Request Body (json):
```
{
  "username": "exampleuser",
  "password": "password123"
}
```
2. **Session Restoration** - On subsequent requests, the cookies are sent automatically by the browser, allowing the frontend to:
```
GET /dj-rest-auth/user/
```
This retrieves the authenticated user without needing to store tokens in JavaScript or headers.
3. **Logout** - Clears the authentication cookies and logs the user out:
```
POST /dj-rest-auth/logout/
```
4. **Token Refresh** - Token refresh is handled automatically via cookies:
```
POST /dj-rest-auth/token/refresh/
```

###  Access Control Summary
- All authentication is cookie-based.
- All CRUD views check for an authenticated session using the token in the cookie.
- Users can only access their own data. Attempts to access other users' entries return:
  - 403 Forbidden if authenticated but unauthorized
  - 401 Unauthorized if unauthenticated

#### Notes
- The frontend must include `withCredentials`: true in all API requests.
- On production, cookies should be:
  - Secure: True
  - SameSite: 'Lax'
  - HttpOnly: True 

For more details on security setup and environment variable configuration, see the [Security](https://github.com/SemMTM/sems-financial-tracker?tab=readme-ov-file#security) section of the overall projects README.