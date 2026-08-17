"""
Repositories package — data-access layer.

Split into two sub-packages:
  - interfaces/  — Protocol/ABC contracts that services depend on
  - impl/        — Concrete implementations (SQLAlchemy, etc.)

Services import from interfaces only. Concrete impls are wired in core/di.py.
"""
