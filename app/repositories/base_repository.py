"""
app.repositories.base_repository
----------------------------------
Generic typed CRUD base class.

All domain repositories inherit from BaseRepository[ModelT] and gain
standard create / read / update / delete operations for free.
Domain-specific queries are added as methods on each subclass.

Example:
    class SaleRepository(BaseRepository[Sale]):
        def __init__(self, db: Session):
            super().__init__(Sale, db)

        def get_by_invoice(self, invoice_number: str) -> Optional[Sale]:
            return (
                self.db.query(self.model)
                .filter(self.model.invoice_number == invoice_number)
                .first()
            )
"""

from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    """
    Generic repository providing typed CRUD operations over a SQLAlchemy model.

    Attributes:
        model:  The SQLAlchemy model class this repository manages.
        db:     The active SQLAlchemy Session, injected per-request.
    """

    def __init__(self, model: Type[ModelT], db: Session) -> None:
        self.model = model
        self.db = db

    # ------------------------------------------------------------------ #
    #  Read                                                                #
    # ------------------------------------------------------------------ #

    def get(self, id: int) -> Optional[ModelT]:
        """Fetch a single record by primary key. Returns None if not found."""
        return self.db.query(self.model).filter(self.model.id == id).first()  # type: ignore[attr-defined]

    def get_or_raise(self, id: int, detail: str = "Resource not found") -> ModelT:
        """Fetch by PK or raise a 404 HTTPException."""
        from fastapi import HTTPException, status

        obj = self.get(id)
        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
        return obj

    def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[List[Any]] = None,
    ) -> List[ModelT]:
        """
        Fetch a paginated list of records.

        Args:
            skip:    Number of records to skip (offset).
            limit:   Maximum number of records to return.
            filters: Optional list of SQLAlchemy filter expressions.
        """
        q = self.db.query(self.model)
        if filters:
            q = q.filter(*filters)
        return q.offset(skip).limit(limit).all()

    def count(self, filters: Optional[List[Any]] = None) -> int:
        """Return total count of records matching optional filters."""
        q = self.db.query(self.model)
        if filters:
            q = q.filter(*filters)
        return q.count()

    # ------------------------------------------------------------------ #
    #  Write                                                               #
    # ------------------------------------------------------------------ #

    def create(self, obj_in: Dict[str, Any]) -> ModelT:
        """
        Create and persist a new record from a plain dict.

        Args:
            obj_in: Dictionary of field → value pairs.

        Returns:
            The newly created and refreshed ORM instance.
        """
        db_obj = self.model(**obj_in)  # type: ignore[call-arg]
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: ModelT, obj_in: Dict[str, Any]) -> ModelT:
        """
        Update an existing ORM instance with fields from a dict.

        Args:
            db_obj: Existing ORM instance to update.
            obj_in: Dict of fields to apply.

        Returns:
            The updated and refreshed ORM instance.
        """
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: int) -> bool:
        """
        Delete a record by primary key (soft-deletes if model supports deleted_at).

        Returns:
            True if deleted, False if record was not found.
        """
        obj = self.get(id)
        if obj is None:
            return False
        if hasattr(obj, "deleted_at"):
            from datetime import datetime, timezone
            if hasattr(obj, "status"):
                obj.status = "deleted"  # type: ignore[attr-defined]
            obj.deleted_at = datetime.now(timezone.utc)  # type: ignore[attr-defined]
            self.db.commit()
            return True
        self.db.delete(obj)
        self.db.commit()
        return True

    def soft_delete(self, id: int, deleted_by: Optional[int] = None) -> Optional[ModelT]:
        """
        Soft-delete by setting status='deleted' and deleted_at timestamp.
        Requires the model to use AuditMixin.

        Returns:
            The updated ORM instance, or None if not found.
        """
        from datetime import datetime, timezone

        obj = self.get(id)
        if obj is None:
            return None
        if hasattr(obj, "status"):
            obj.status = "deleted"  # type: ignore[attr-defined]
        if hasattr(obj, "deleted_at"):
            obj.deleted_at = datetime.now(timezone.utc)  # type: ignore[attr-defined]
        if hasattr(obj, "updated_by") and deleted_by is not None:
            obj.updated_by = deleted_by  # type: ignore[attr-defined]
        self.db.commit()
        self.db.refresh(obj)
        return obj

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def exists(self, id: int) -> bool:
        """Return True if a record with the given PK exists."""
        return self.get(id) is not None

    def bulk_create(self, objs_in: List[Dict[str, Any]]) -> List[ModelT]:
        """
        Insert multiple records in a single transaction.

        Args:
            objs_in: List of field dicts.

        Returns:
            List of created and refreshed ORM instances.
        """
        db_objs = [self.model(**obj) for obj in objs_in]  # type: ignore[call-arg]
        self.db.add_all(db_objs)
        self.db.commit()
        for obj in db_objs:
            self.db.refresh(obj)
        return db_objs
