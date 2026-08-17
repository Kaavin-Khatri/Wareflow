"""
Services package — business logic layer.

Services orchestrate domain operations by calling repository interfaces.
They NEVER import concrete repository implementations directly.
Dependencies are injected via FastAPI's Depends() mechanism.

Rule: routers → services → repository interfaces
"""
