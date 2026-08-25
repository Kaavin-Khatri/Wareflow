"""
Rate limiting module using slowapi.

Provides a shared Limiter instance for expensive operations:
- Groq LLM AI Briefing & Forecast endpoints: 5/minute
- CSV Bulk Imports: 10/minute
- Global default: 120/minute per IP
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120/minute"],
    headers_enabled=False,
)
