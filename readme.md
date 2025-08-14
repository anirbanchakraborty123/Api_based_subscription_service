# Django Subscription Service API

A comprehensive Django REST Framework API for managing subscription services with plans and features. Built with enterprise-level features including caching, rate limiting, logging, and comprehensive testing.

## 🚀 Features

### Core API Features
- **Subscription Management**: Create, list, update, and deactivate subscriptions
- **Plan Management**: Manage subscription plans with multiple features
- **Feature Management**: Individual features that can be assigned to plans
- **Nested Serialization**: Full plan and feature details in API responses
- **User Isolation**: Users can only access their own subscriptions

### Advanced Features
- **Query Optimization**: Eliminates N+1 queries using `select_related` and `prefetch_related`
- **Caching**: Redis-based caching for improved performance
- **Rate Limiting**: Configurable rate limits for different operations
- **Comprehensive Logging**: Request/response logging and business logic tracking
- **Custom Permissions**: Fine-grained access control
- **Pagination**: Configurable pagination with limits
- **Validation**: Comprehensive data validation at multiple levels
- **Error Handling**: Consistent error response format
- **Cache Invalidation**: Automatic cache clearing on data changes

### Testing & Development
- **Unit Tests**: Comprehensive test coverage for all functionality
- **Sample Data**: Management command to create test data
- **Admin Interface**: Optimized Django admin panels
- **API Documentation**: Built-in API documentation
- **Docker Support**: Containerized development environment

## 🛠 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL/MySQL (or SQLite for development)
- Redis (for caching and rate limiting)

### 1. Clone the Repository
```bash
git clone <https://github.com/anirbanchakraborty123/Api_based_subscription_service.git>
cd subscription_service
```

### 2. Create Virtual Environment
```bash
python -m venv subscription_env
source subscription_env/bin/activate  # On Windows: subscription_env\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the project root:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/subscription_db
# or for SQLite (development)
DATABASE_URL=sqlite:///db.sqlite3

# Redis
REDIS_URL=redis://localhost:6379/1

# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Logging
LOG_LEVEL=INFO
```

### 5. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 6. Create Sample Data (Optional)
```bash
python manage.py create_sample_data
```

### 7. Run the Server
```bash
python manage.py runserver
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/v1/
```

### Authentication
All endpoints require authentication. Use Token Authentication:
```bash
# Get token after creating user
curl -X POST http://localhost:8000/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Use token in subsequent requests
curl -H "Authorization: Token YOUR_TOKEN_HERE" ...
```

---

## 🔗 API Endpoints

### 1. Create Subscription
**Endpoint:** `POST /api/v1/subscriptions/`
**Rate Limit:** 10 requests/minute per user

Creates a new subscription for the authenticated user. If user has an active subscription, it will be deactivated.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/subscriptions/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan": 2}'
```

**Response (201 Created):**
```json
{
  "id": 15,
  "user_email": "john@example.com",
  "plan": {
    "id": 2,
    "name": "Professional",
    "description": "Ideal for growing businesses and teams",
    "price": "29.99",
    "features": [
      {
        "id": 2,
        "name": "Unlimited API Access",
        "description": "Unlimited access to all API endpoints",
        "is_active": true
      },
      {
        "id": 3,
        "name": "Priority Support",
        "description": "24/7 priority customer support",
        "is_active": true
      }
    ],
    "feature_count": 2,
    "is_active": true,
    "created_at": "2025-01-10T10:00:00Z"
  },
  "start_date": "2025-01-15T14:30:00Z",
  "end_date": null,
  "is_active": true,
  "duration_days": 5,
  "created_at": "2025-01-15T14:30:00Z"
}
```

---

### 2. List User Subscriptions
**Endpoint:** `GET /api/v1/subscriptions/`
**Cache:** 5 minutes

Returns paginated list of user's subscriptions with nested plan and feature data.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/subscriptions/?page=1&page_size=10" \
  -H "Authorization: Token YOUR_TOKEN"
```

**Response (200 OK):**
```json
{
  "count": 25,
  "next": "http://localhost:8000/api/v1/subscriptions/?page=2&page_size=10",
  "previous": null,
  "results": [
    {
      "id": 15,
      "user_email": "john@example.com",
      "plan": {
        "id": 2,
        "name": "Professional",
        "description": "Ideal for growing businesses and teams",
        "price": "29.99",
        "features": [
          {
            "id": 2,
            "name": "Unlimited API Access",
            "description": "Unlimited access to all API endpoints",
            "is_active": true
          },
          {
            "id": 3,
            "name": "Priority Support",
            "description": "24/7 priority customer support",
            "is_active": true
          }
        ],
        "feature_count": 2,
        "is_active": true,
        "created_at": "2025-01-10T10:00:00Z"
      },
      "start_date": "2025-01-15T14:30:00Z",
      "end_date": null,
      "is_active": true,
      "duration_days": 5,
      "created_at": "2025-01-15T14:30:00Z"
    }
  ]
}
```

---

### 3. Get Active Subscription
**Endpoint:** `GET /api/v1/subscriptions/active/`
**Cache:** 10 minutes

Returns user's currently active subscription.

**Request:**
```bash
curl -X GET http://localhost:8000/api/v1/subscriptions/active/ \
  -H "Authorization: Token YOUR_TOKEN"
```

**Response (200 OK):**
```json
{
  "id": 15,
  "user_email": "john@example.com",
  "plan": {
    "id": 2,
    "name": "Professional",
    "description": "Ideal for growing businesses and teams",
    "price": "29.99",
    "features": [
      {
        "id": 2,
        "name": "Unlimited API Access",
        "description": "Unlimited access to all API endpoints",
        "is_active": true
      }
    ],
    "feature_count": 1,
    "is_active": true,
    "created_at": "2025-01-10T10:00:00Z"
  },
  "start_date": "2025-01-15T14:30:00Z",
  "end_date": null,
  "is_active": true,
  "duration_days": 5,
  "created_at": "2025-01-15T14:30:00Z"
}
```

**Response (404 Not Found):**
```json
{
  "error": true,
  "message": "Resource not found",
  "details": {
    "message": "No active subscription found"
  },
  "status_code": 404
}
```

---

### 4. Change Subscription Plan
**Endpoint:** `PUT /api/v1/subscriptions/{id}/change-plan/`
**Rate Limit:** 5 requests/minute per user

Updates the subscription to use a different plan.

**Request:**
```bash
curl -X PUT http://localhost:8000/api/v1/subscriptions/15/change-plan/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan": 3}'
```

**Response (200 OK):**
```json
{
  "id": 15,
  "user_email": "john@example.com",
  "plan": {
    "id": 3,
    "name": "Business",
    "description": "Advanced features for established businesses",
    "price": "79.99",
    "features": [
      {
        "id": 2,
        "name": "Unlimited API Access",
        "description": "Unlimited access to all API endpoints",
        "is_active": true
      },
      {
        "id": 3,
        "name": "Priority Support",
        "description": "24/7 priority customer support",
        "is_active": true
      },
      {
        "id": 4,
        "name": "Advanced Analytics",
        "description": "Advanced analytics and reporting dashboard",
        "is_active": true
      }
    ],
    "feature_count": 3,
    "is_active": true,
    "created_at": "2025-01-10T10:00:00Z"
  },
  "start_date": "2025-01-15T14:30:00Z",
  "end_date": null,
  "is_active": true,
  "duration_days": 5,
  "created_at": "2025-01-15T14:30:00Z"
}
```

---

### 5. Deactivate Subscription
**Endpoint:** `POST /api/v1/subscriptions/{id}/deactivate/`
**Rate Limit:** 10 requests/minute per user

Deactivates a subscription by setting `is_active` to `False` and setting `end_date`.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/subscriptions/15/deactivate/ \
  -H "Authorization: Token YOUR_TOKEN"
```

**Response (200 OK):**
```json
{
  "id": 15,
  "user_email": "john@example.com",
  "plan": {
    "id": 3,
    "name": "Business",
    "description": "Advanced features for established businesses",
    "price": "79.99",
    "features": [
      {
        "id": 2,
        "name": "Unlimited API Access",
        "description": "Unlimited access to all API endpoints",
        "is_active": true
      }
    ],
    "feature_count": 1,
    "is_active": true,
    "created_at": "2025-01-10T10:00:00Z"
  },
  "start_date": "2025-01-15T14:30:00Z",
  "end_date": "2025-01-20T16:45:00Z",
  "is_active": false,
  "duration_days": 5,
  "created_at": "2025-01-15T14:30:00Z"
}
```

---

### 6. List Available Plans
**Endpoint:** `GET /api/v1/plans/`
**Cache:** 15 minutes

Returns paginated list of available subscription plans.

**Request:**
```bash
curl -X GET http://localhost:8000/api/v1/plans/ \
  -H "Authorization: Token YOUR_TOKEN"
```

**Response (200 OK):**
```json
{
  "count": 4,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Starter",
      "description": "Perfect for individuals and small projects",
      "price": "9.99",
      "features": [
        {
          "id": 1,
          "name": "Basic API Access",
          "description": "Access to basic API endpoints with rate limiting",
          "is_active": true
        }
      ],
      "feature_count": 1,
      "is_active": true,
      "created_at": "2025-01-10T10:00:00Z"
    },
    {
      "id": 2,
      "name": "Professional",
      "description": "Ideal for growing businesses and teams",
      "price": "29.99",
      "features": [
        {
          "id": 2,
          "name": "Unlimited API Access",
          "description": "Unlimited access to all API endpoints",
          "is_active": true
        },
        {
          "id": 3,
          "name": "Priority Support",
          "description": "24/7 priority customer support",
          "is_active": true
        }
      ],
      "feature_count": 2,
      "is_active": true,
      "created_at": "2025-01-10T10:00:00Z"
    }
  ]
}
```

---

### 7. Get Plan Details
**Endpoint:** `GET /api/v1/plans/{id}/`
**Cache:** 15 minutes

Returns detailed information about a specific plan.

**Request:**
```bash
curl -X GET http://localhost:8000/api/v1/plans/2/ \
  -H "Authorization: Token YOUR_TOKEN"
```

**Response (200 OK):**
```json
{
  "id": 2,
  "name": "Professional",
  "description": "Ideal for growing businesses and teams",
  "price": "29.99",
  "features": [
    {
      "id": 2,
      "name": "Unlimited API Access",
      "description": "Unlimited access to all API endpoints",
      "is_active": true
    },
    {
      "id": 3,
      "name": "Priority Support",
      "description": "24/7 priority customer support",
      "is_active": true
    }
  ],
  "feature_count": 2,
  "is_active": true,
  "created_at": "2025-01-10T10:00:00Z"
}
```

---

### 8. Health Check
**Endpoint:** `GET /health/`

Returns application health status.

**Request:**
```bash
curl -X GET http://localhost:8000/health/
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T16:45:30.123456Z",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "models": "ok"
  }
}
```

---

## 🚫 Error Responses

All API endpoints return consistent error response format:

### 400 Bad Request
```json
{
  "error": true,
  "message": "Invalid request data",
  "details": {
    "plan": ["Cannot subscribe to inactive plan"]
  },
  "status_code": 400
}
```

### 401 Unauthorized
```json
{
  "error": true,
  "message": "Authentication required",
  "details": {
    "detail": "Authentication credentials were not provided."
  },
  "status_code": 401
}
```

### 403 Forbidden
```json
{
  "error": true,
  "message": "Permission denied",
  "details": {
    "detail": "You do not have permission to perform this action."
  },
  "status_code": 403
}
```

### 404 Not Found
```json
{
  "error": true,
  "message": "Resource not found",
  "details": {
    "detail": "Not found."
  },
  "status_code": 404
}
```

### 429 Too Many Requests
```json
{
  "error": true,
  "message": "Too many requests. Please try again later.",
  "details": {
    "detail": "Request was throttled. Expected available in 45 seconds."
  },
  "status_code": 429
}
```

---

## 🧪 Testing

### Run All Tests
```bash
python manage.py test
```

### Run Tests with Coverage
```bash
pip install coverage
coverage run manage.py test
coverage report
coverage html  # Generates HTML coverage report
```

### Run Specific Test Cases
```bash
# Test specific app
python manage.py test subscriptions

# Test specific test case
python manage.py test subscriptions.tests.SubscriptionAPITestCase

# Test specific method
python manage.py test subscriptions.tests.SubscriptionAPITestCase.test_subscription_creation
```

### Using Pytest (Alternative)
```bash
pip install pytest-django pytest-cov
pytest
pytest --cov=subscriptions
pytest --cov=subscriptions --cov-report=html
```

### Test Data Setup
```bash
# Create sample data for manual testing
python manage.py create_sample_data

# Clean and recreate sample data
python manage.py create_sample_data --clean
```

## 🔍 Monitoring & Logging

### Log Files
- **Application Logs**: `subscription_api.log`
- **Error Logs**: Django logs to console and file
- **Performance Logs**: Database query monitoring

### Key Metrics to Monitor
- Response times for API endpoints
- Database query counts per request
- Cache hit/miss ratios
- Rate limit violations
- Authentication failures

### Log Examples
```log
2025-01-15 16:45:30 INFO subscriptions.views: Creating subscription for user john_doe
2025-01-15 16:45:31 INFO subscriptions.models: Subscription 15 deactivated for user john_doe
2025-01-15 16:45:31 WARNING subscriptions.views: High query count detected in list: 15 queries
```

### Cache Configuration
```python
# Custom cache timeouts
CACHE_TIMEOUTS = {
    'subscription_list': 300,  # 5 minutes
    'active_subscription': 600,  # 10 minutes
    'plans': 900,  # 15 minutes
}

```
# Made the readme file using AI IDE cursor.
# Also have experience working with AI Ide cursor for smart work and boosting speed and understanding. This enhances productivity.