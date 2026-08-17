"""
API routers package.

Routers handle HTTP concerns ONLY:
- Request parsing and validation
- Response serialization
- HTTP status codes

Business logic belongs in services — routers call services, never repositories.
"""
