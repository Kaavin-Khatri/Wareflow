"""
Repository interfaces — Protocol/ABC contracts.

Every repository interface defines the data-access contract that services
depend on. Concrete implementations live in ../impl/ and are wired
via dependency injection in core/di.py.

This satisfies the Dependency Inversion Principle:
  High-level modules (services) depend on abstractions (these interfaces),
  not on low-level modules (SQLAlchemy implementations).
"""
