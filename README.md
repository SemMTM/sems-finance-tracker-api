# Finance Tracker API - Personal Finance Dashboard
## Overview
This RESTful API powers the backend of the Financial Tracker application — a full-stack solution that allows authenticated users to manage their personal finances in a secure, intuitive way.

The frontend README can be found [HERE](https://github.com/SemMTM/sems-financial-tracker/tree/main).

[Deployed version of the Monthly Finance Tracker can be found here.](https://www.monthlyfinancetracker.xyz)

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

# Authentication
All endpoints related to financial data are protected and require the user to be authenticated using JWT tokens issued by the `dj-rest-auth` package.

## Login & Token Flow
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

### Notes
- The frontend must include `withCredentials`: true in all API requests.
- On production, cookies should be:
  - Secure: True
  - SameSite: 'Lax'
  - HttpOnly: True 

For more details on security setup and environment variable configuration, see the [Security](https://github.com/SemMTM/sems-financial-tracker?tab=readme-ov-file#security) section of the overall projects README.

# Endpoints
All endpoints listed below require authentication via secure HttpOnly JWT cookies. Only the authenticated user's data is ever returned or modified.

## Income
**Base URL**: `/income/`

| Method | Endpoint                    | Description                                                         |
|--------|-----------------------------|---------------------------------------------------------------------|
| GET    | `/income/?month=YYYY-MM`    | List income entries for the specified month (user only)            |
| POST   | `/income/`                  | Create a new income entry                                          |
| GET    | `/income/<id>/`             | Retrieve a single income entry                                     |
| PUT    | `/income/<id>/`             | Update an existing income entry                                    |
| PATCH  | `/income/<id>/`             | Partially update an income entry                                   |
| DELETE | `/income/<id>/`             | Delete an income entry (and its future repeats if applicable)      |

> `GET /income/` requires a `?month=YYYY-MM` query parameter to filter results by selected calendar month.

#### POST /income/
Create a new income entry

**Request body:**
```json
{
  "title": "Salary",
  "amount": "1200.00",
  "date": "2025-06-01",
  "repeated": "WEEKLY"  // Options: NEVER, WEEKLY, MONTHLY
}
```

**Response**
```json
{
  "id": 1,
  "title": "Salary",
  "amount": 120000,         // stored in pence
  "formatted_amount": "£1200",
  "date": "2025-06-01",
  "repeated": "WEEKLY",
  "repeat_group_id": "uuid..."
}
```

## Expenditures
**Base URL**: `/expenditures/`

| Method | Endpoint                    | Description                                                         |
|--------|-----------------------------|---------------------------------------------------------------------|
| GET    | `/expenditures/?month=YYYY-MM`    | List expenditures for the current month (user only)          |
| POST   | `/expenditures/`                  | Create a new expenditure                                         |
| GET    | `/expenditures/<id>/`             | Retrieve a single expenditure                                  |
| PUT    | `/expenditures/<id>/`             | Update an existing expenditure                                  |
| PATCH  | `/expenditures/<id>/`             | Partially update an expenditure                                 |
| DELETE | `/expenditures/<id>/`             | Delete an expenditure (and future repeats if applicable)      |

#### POST /expenditures/
**Request body**:
```json
{
  "title": "Rent",
  "amount": "500.00",
  "type": "BILL",               // Options: BILL, SAVINGS, INVESTMENT
  "date": "2025-06-01",
  "repeated": "MONTHLY"
}
```

**Response**:
```json
{
  "id": 5,
  "title": "Rent",
  "amount": 50000,
  "formatted_amount": "£500",
  "type": "BILL",
  "date": "2025-06-01",
  "repeated": "MONTHLY",
  "repeat_group_id": "uuid..."
}
```

## Disposable Income Budget
**Base URL**: `/disposable-budget/`

| Method | Endpoint | Description |
|--|--|--|
| GET | `/disposable-budget/?month=YYYY-MM` | Retrieve the selected month’s budget entry |
| PUT | `/disposable-budget/<id>/` | Update the current month’s budget entry |

> Auto-created on the 1st of each month with default value 0.


## Disposable Income Spending

**Base URL**: `/disposable-spending/`

| Method | Endpoint                               | Description                                           |
|--------|----------------------------------------|-------------------------------------------------------|
| GET    | `/disposable-spending/?month=YYYY-MM`  | List spending entries for the selected month         |
| POST   | `/disposable-spending/`                | Add a new spending entry                             |
| DELETE | `/disposable-spending/<id>/`           | Delete a spending entry                              |

> `GET /disposable-spending/` requires the `?month=YYYY-MM` query parameter to filter entries by the selected month.

#### POST /disposable-spending/

**Request Body:**
```json
{
  "title": "Coffee",
  "amount": "3.50",
  "date": "2025-06-03"
}
```

**Response:**
```json
{
  "id": 14,
  "title": "Coffee",
  "amount": 350,
  "formatted_amount": "£3.50",
  "date": "2025-06-03",
  "owner": "user123"
}
```

## Calendar Summary

**Base URL**: `/calendar-summary/`

| Method | Endpoint | Description |
|---|---|---|
|  GET | `/calendar-summary/?month=YYYY-MM` |	Return per-day income, expenditure, and currency symbol  |

**Response:**
```json
[
  {
    "date": "2025-06-01",
    "income": "100.00",
    "expenditure": "50.00",
    "currency_symbol": "£"
  },
  ...
]
```

## Weekly Summary

**Endpoint**:
`GET /weekly-summary/?date=YYYY-MM-DD`

Returns a breakdown of all weeks that include any days from the given month. Each week includes only the data for days within that month, even if the week starts in the previous month or ends in the next.

**Exmaple Request**:
```
GET /weekly-summary/?month=2025-06
```

**Response**:
```json
[
  {
    "week_start": "2025-05-26",
    "week_end": "2025-06-01",
    "income": "100.00",
    "cost": "50.00",
    "summary": "50.00"
  },
  {
    "week_start": "2025-06-02",
    "week_end": "2025-06-08",
    "income": "200.00",
    "cost": "130.00",
    "summary": "70.00"
  }
]
```

#### Key Details
- Partial weeks are included, but only the portion within the month contributes to the totals
- summary is always the result of:
  - summary = income - cost
- All values are strings for formatting consistency
- Currency symbol is not returned — the frontend uses user settings for that

## Monthly Summary
**Endpoint**:
`GET /monthly-summary/?month=YYYY-MM`

Returns a comprehensive financial summary for the selected month. This includes total income, categorized expenditure, disposable spending, and disposable budget tracking.

All returned values are formatted strings with the user’s preferred currency symbol and are calculated based only on entries within the selected month.

**Example Request**:
```
GET /monthly-summary/?month=2025-06
```

**Response**
```json
{
  "formatted_income": "£800.00",
  "formatted_bills": "£420.00",
  "formatted_saving": "£100.00",
  "formatted_investment": "£80.00",
  "formatted_disposable_spending": "£50.00",
  "formatted_total": "£150.00",
  "formatted_budget": "£100.00",
  "formatted_remaining_disposable": "£50.00"
}
```

#### Field Descriptions
|--|--|
| Field | Description |
|formatted_income |	Total income for the month |
|formatted_bills |	Total bill expenditures (type = BILL) |
|formatted_saving |	Total savings expenditures (type = SAVING) |
|formatted_investment |	Total investment expenditures (type = INVESTMENT) |
|formatted_disposable_spending |	Total spending from user’s disposable income |
|formatted_total |	Net total: income - (bills + saving + investment + disposable_spending) |
|formatted_budget |	The budgeted disposable income for the month |
|formatted_remaining_disposable |	Disposable budget minus disposable spending |


## Currency
**Base URL**: `/currency/`

| Method | Endpoint | Description| 
|----|----|----|----|
| GET | `/currency/` | Retrieve current user’s currency |
| PUT | `/currency/` | Update user's currency code |

The selected currency controls the symbol returned in all financial endpoints.

**Example Response**:
```json
{
  "id": 1,
  "currency": "GBP",
  "currency_display": "British Pound £",
  "currency_symbol": "£",
}
```

## Change Email
**Endpoint**: `PUT /change-email/`

This endpoint allows an authenticated user to update their registered email address. It uses a custom `APIView` that validates the input and applies the change directly to the user model.

**Request Body**
```json
{
  "email": "new_email@example.com"
}
```

- `email`: Must be a valid, non-empty, and unique email address.

**Success Response (200)**:
```json
{
  "message": "Email updated successfully"
}
```
- Indicates the email change was successful
- The new email is immediately applied to the user’s account

**Error Responses (400)**
```json
{
  "email": ["This field is required."]
}
```
```json
{
  "email": ["Enter a valid email address."]
}
```
```json
{
  "email": ["This email is already in use."]
}
```

- These errors come from the ChangeEmailSerializer and cover:
  - Missing field
  - Email format
  - Uniqueness across all users

- 403 Forbidden – If the user is not authenticated:
```json
{
  "detail": "Authentication credentials were not provided."
}
```

####  Validation
The ChangeEmailSerializer performs:
- Required field check
- Valid email format check (e.g., test@domain.com)
- Uniqueness check against other users in the database

# Permissions & Security
The API enforces strict access control and data protection practices to ensure user privacy and prevent unauthorized access:

### Authentication
- All endpoints are protected using JWT-based cookie authentication.
- Tokens are stored in HttpOnly cookies, making them inaccessible via JavaScript and protecting against XSS attacks.
- Session persistence is handled by Django REST Auth and the token refresh flow is automatically managed on the frontend.

### Ownership Enforcement
- Every financial record (e.g. Income, Expenditure, Budget) is scoped to the authenticated user.
- Querysets are filtered so users can only access their own data. No user can retrieve, edit, or delete another user's records — even if they know the record ID.

### Data Visibility
- Sensitive fields like owner and is_owner are included in some responses for internal verification, but all actions are permission-locked server-side.
- All write operations (POST, PUT, PATCH, DELETE) require authentication and ownership.

### Other Security Measures
- Production secrets and keys are stored in environment variables and are never committed to source control.
- DEBUG = False in production.
- No passwords or sensitive data are ever logged or exposed through responses.
- Rate limiting and throttling are supported via DRF settings (optional but recommended for public APIs).

Refer to the Security section of the frontend README [HERE]((https://github.com/SemMTM/sems-financial-tracker?tab=readme-ov-file#security)) for details on:
- Token management
- Cookie security flags
- Secure routing logic based on auth state

# Error Handling
The API is designed to return clear, structured error responses for all major failure scenarios. These are caught and handled gracefully on the frontend.

### HTTP Status Codes Used

| Code | Meaning |
|--|--|
| `200 OK` | Request succeeded |
| 201 Created |	New resource created |
| 204 No Content |	Resource successfully deleted |
| 400 Bad Request |	Validation error or malformed request |
| 401 Unauthorized |	Missing or invalid authentication |
| 403 Forbidden |	Authenticated but not permitted (e.g. not the owner) |
| 404 Not Found |	Resource doesn't exist or is not owned by the user |
| 500 Internal Server Error |	Server-side issue (unexpected error) |

### Example Validation Errors
```json
{
  "amount": ["Ensure this value is greater than or equal to 0."]
}
```
```json
{
  "email": ["This email is already in use."]
}
```

### Frontend Handling
The frontend displays:
- Inline field errors for form validations
- General error banners for failed fetches or submissions
- Spinners and loading states during async operations
- Redirects to login if a user’s session expires or is invalid

# Testing & Validation
This project was manually tested end-to-end to ensure correctness, security, and consistency across all CRUD operations, authentication flows, and data presentation layers. The frontend and backend were tested separately and in coordination to ensure data integrity and correct user experience.

### Backend Testing (Django)
Manual and unit testing was applied across all views, serializers, and utility functions.
Comprehensive unit tests were written using for all key views:
- `IncomeViewSet`
- `ExpenditureViewSet`
- `DisposableIncomeSpendingViewSet`
- `DisposableIncomeBudgetViewSet`
- `CalendarSummaryView`
- `WeeklySummaryView`
- `MonthlySummaryView`
- `CurrencyViewSet`

Tests cover all major cases including:
- Successful creation, update, and deletion
- Proper filtering of data by user and date
- Permission enforcement (preventing cross-user access)
- Validation failures (e.g. negative amounts, invalid formats)
- Repeated entry logic and propagation

All tests include docstrings for clarity and alignment with best practices.

Unit test files can be found with the following links:
#### Transactions app:
- [Serializer unit tests](/transactions/tests/test_serializers.py)
- [Views unit tests](/transactions/tests/test_views.py)
- [Utility functions unit tests](/transactions/tests/test_utils.py)

#### Core app: 
- [Serializer unit tests](/core/tests/test_serializers.py)
- [Views unit tests](/core/tests/test_views.py)
- [Utils unit tests](/core/tests/test_utils.py)

For more detail on the manual testing that was done, see the TESTING.md file on the frontend repo [HERE](https://github.com/SemMTM/sems-financial-tracker/blob/main/TESTING.md).

# Deployment
See the Deployment section of this [README](https://github.com/SemMTM/sems-financial-tracker?tab=readme-ov-file#backend-deployment-heroku) for details on hosting the backend API on Heroku