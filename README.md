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

## Endpoints
All endpoints listed below require authentication via secure HttpOnly JWT cookies. Only the authenticated user's data is ever returned or modified.

### Income
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

### Expenditures
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

### Disposable Income Budget
**Base URL**: `/disposable-budget/`

| Method | Endpoint | Description |
|--|--|--|
| GET | `/disposable-budget/?month=YYYY-MM` | Retrieve the selected month’s budget entry |
| PUT | `/disposable-budget/<id>/` | Update the current month’s budget entry |

> Auto-created on the 1st of each month with default value 0.


### Disposable Income Spending

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

### Calendar Summary

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

### Weekly Summary

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

### Monthly Summary
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


### Currency
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

### Change Email
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
