"""
app.core.audit_listener
------------------------
SQLAlchemy Change Data Capture (CDC) event listener engine.
Automatically intercepts all CREATE, UPDATE, DELETE, and SOFT_DELETE operations
across all ORM models at the session lifecycle level.

Captures:
  - Model name & record primary key
  - Pre-change state (old_data)
  - Post-change state (new_data)
  - Exact field-level diff (changes)
  - Operator identity & HTTP network context from audit_context
  - Automatic masking/redaction of sensitive credentials
"""

from datetime import datetime, date, time
from decimal import Decimal
from typing import Any, Dict, Optional, Set
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session, SessionTransaction

from app.core.audit_context import get_audit_context

# Sensitive fields to redact from change logs
SENSITIVE_FIELDS: Set[str] = {
    "hashed_password",
    "password",
    "secret_key",
    "token",
    "refresh_token",
    "access_token",
    "api_key"
}

# Tables/models to ignore to avoid recursive loops or logging transient records
IGNORED_MODELS: Set[str] = {
    "AuditLog",
    "audit_logs"
}

def serialize_value(val: Any) -> Any:
    """Convert non-JSON-serializable types into serializable primitives."""
    if val is None:
        return None
    if isinstance(val, (datetime, date, time)):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, (int, float, str, bool)):
        return val
    if isinstance(val, dict):
        return {str(k): serialize_value(v) for k, v in val.items()}
    if isinstance(val, (list, tuple, set)):
        return [serialize_value(x) for x in val]
    if isinstance(val, bytes):
        return "<binary data>"
    return str(val)

def extract_record_snapshot(obj: Any) -> Dict[str, Any]:
    """Capture a dictionary snapshot of all table columns on an ORM instance."""
    if not hasattr(obj, "__table__"):
        return {}
    
    snapshot = {}
    for col in obj.__table__.columns:
        col_name = col.name
        if col_name in SENSITIVE_FIELDS:
            snapshot[col_name] = "[REDACTED]"
        else:
            raw_val = getattr(obj, col_name, None)
            snapshot[col_name] = serialize_value(raw_val)
    return snapshot

def resolve_context_for_obj(obj: Any, ctx: Dict[str, Any], session: Optional[Session] = None) -> Dict[str, Any]:
    """Derive company_id, branch_id, user_id, user_name, and user_email from object or session."""
    comp_id = ctx.get("company_id")
    if comp_id is None and hasattr(obj, "company_id"):
        comp_id = getattr(obj, "company_id", None)
        
    br_id = ctx.get("branch_id")
    if br_id is None and hasattr(obj, "branch_id"):
        br_id = getattr(obj, "branch_id", None)

    user_id = ctx.get("user_id")
    if user_id is None and hasattr(obj, "created_by"):
        user_id = getattr(obj, "created_by", None)
    if user_id is None and hasattr(obj, "updated_by"):
        user_id = getattr(obj, "updated_by", None)

    user_name = ctx.get("user_name")
    user_email = ctx.get("user_email")

    if user_id and (not user_name or not user_email) and session:
        try:
            from app.models.auth.user import User
            # First check session identity map (no DB query needed)
            user = session.identity_map.get((User, (user_id,)))
            if not user:
                user = session.query(User).filter(User.id == user_id).first()
            if user:
                if not user_name:
                    user_name = user.name
                if not user_email:
                    user_email = user.email
                if comp_id is None:
                    comp_id = user.company_id
        except Exception:
            pass

    return {
        "company_id": comp_id,
        "branch_id": br_id,
        "user_id": user_id,
        "user_name": user_name,
        "user_email": user_email,
        "ip_address": ctx.get("ip_address"),
        "user_agent": ctx.get("user_agent"),
        "endpoint": ctx.get("endpoint"),
        "http_method": ctx.get("http_method"),
        "status_code": ctx.get("status_code")
    }

def handle_before_flush(session: Session, flush_context: Any, instances: Any):
    """
    Called before SQL statements are flushed to the database.
    Captures:
      1. UPDATEs: detects dirty objects and calculates field-level diffs.
      2. DELETEs: captures complete pre-deletion state.
    """
    pending = session.info.setdefault("_pending_audit_events", [])
    ctx = get_audit_context()

    # 1. Inspect modified (dirty) objects
    for obj in session.dirty:
        model_name = obj.__class__.__name__
        if model_name in IGNORED_MODELS or not hasattr(obj, "__table__"):
            continue
        
        insp = inspect(obj)
        changes: Dict[str, Dict[str, Any]] = {}
        old_data: Dict[str, Any] = {}
        new_data: Dict[str, Any] = {}

        for attr in insp.attrs:
            key = attr.key
            if key.startswith("_") or key not in obj.__table__.columns:
                continue

            hist = attr.history
            if hist.has_changes():
                if key in SENSITIVE_FIELDS:
                    old_val = "[REDACTED]"
                    new_val = "[REDACTED]"
                else:
                    old_val = serialize_value(hist.deleted[0]) if hist.deleted else None
                    new_val = serialize_value(hist.added[0]) if hist.added else None

                changes[key] = {"old": old_val, "new": new_val}
                old_data[key] = old_val
                new_data[key] = new_val

        if changes:
            # Check if this is a soft delete
            action = "UPDATE"
            if "status" in changes and new_data.get("status") == "deleted":
                action = "SOFT_DELETE"
            elif "deleted_at" in changes and new_data.get("deleted_at") is not None:
                action = "SOFT_DELETE"

            meta = resolve_context_for_obj(obj, ctx, session)
            record_id = str(getattr(obj, "id", None))

            pending.append({
                "action": action,
                "model_name": model_name,
                "record_id": record_id,
                "old_data": old_data,
                "new_data": new_data,
                "changes": changes,
                "details": {"modified_fields": list(changes.keys())},
                **meta
            })

    # 2. Inspect deleted objects
    for obj in session.deleted:
        model_name = obj.__class__.__name__
        if model_name in IGNORED_MODELS or not hasattr(obj, "__table__"):
            continue

        old_data = extract_record_snapshot(obj)
        meta = resolve_context_for_obj(obj, ctx, session)
        record_id = str(getattr(obj, "id", None))

        pending.append({
            "action": "DELETE",
            "model_name": model_name,
            "record_id": record_id,
            "old_data": old_data,
            "new_data": None,
            "changes": None,
            "details": {"deleted_fields_count": len(old_data)},
            **meta
        })

def handle_after_flush(session: Session, flush_context: Any):
    """
    Called after SQL statements have flushed to the database.
    Captures:
      1. CREATEs: objects in session.new now have generated primary keys.
      2. Executes atomic batch direct insert of all pending audit entries.
    """
    pending = session.info.get("_pending_audit_events", [])
    ctx = get_audit_context()

    # 1. Process newly created objects (their auto-increment IDs are now populated)
    for obj in session.new:
        model_name = obj.__class__.__name__
        if model_name in IGNORED_MODELS or not hasattr(obj, "__table__"):
            continue

        new_data = extract_record_snapshot(obj)
        meta = resolve_context_for_obj(obj, ctx, session)
        record_id = str(getattr(obj, "id", None))

        pending.append({
            "action": "CREATE",
            "model_name": model_name,
            "record_id": record_id,
            "old_data": None,
            "new_data": new_data,
            "changes": None,
            "details": {"created_fields_count": len(new_data)},
            **meta
        })

    # 2. Batch write to database via raw connection (bypassing ORM flush loop)
    if pending:
        audits_to_write = list(pending)
        pending.clear()
        try:
            from app.models.logging.audit_log import AuditLog
            conn = session.connection()
            conn.execute(AuditLog.__table__.insert(), audits_to_write)
        except Exception as e:
            # Guard against breaking business transaction if audit logging encounters a schema issue
            import logging
            logging.getLogger(__name__).error(f"Audit log batch insert error: {e}")

def register_audit_listeners(session_target: Any):
    """Register the before_flush and after_flush listeners on the sessionmaker or Session class."""
    event.listen(session_target, "before_flush", handle_before_flush)
    event.listen(session_target, "after_flush", handle_after_flush)
