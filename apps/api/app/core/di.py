"""
Dependency injection wiring.

Maps repository interfaces to concrete implementations.
Services receive their dependencies via FastAPI's Depends() mechanism,
ensuring they never import concrete implementations directly.
"""

# Placeholder — wiring is added as domain repositories are created.
# Example pattern:
#
# from app.repositories.interfaces.product_repository import ProductRepositoryInterface
# from app.repositories.impl.product_repository import SqlAlchemyProductRepository
#
# def get_product_repository() -> ProductRepositoryInterface:
#     return SqlAlchemyProductRepository(session=get_db_session())
