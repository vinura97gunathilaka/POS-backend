"""
app.core.audit_context
-----------------------
Async-safe and thread-safe request context for audit logging using Python contextvars.
Maintains operator metadata (user ID, name, email, company, IP address, user agent, etc.)
across the lifecycle of an HTTP request and SQLAlchemy transactions.
"""

import contextvars
from typing import Optional, Dict, Any

_audit_context: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar(
    "audit_context", default={}
)

def get_audit_context() -> Dict[str, Any]:
    """Retrieve the current audit context dictionary."""
    ctx = _audit_context.get()
    if ctx is None:
        ctx = {}
        _audit_context.set(ctx)
    return ctx

def set_audit_context(
    user_id: Optional[int] = None,
    user_name: Optional[str] = None,
    user_email: Optional[str] = None,
    company_id: Optional[int] = None,
    branch_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    endpoint: Optional[str] = None,
    http_method: Optional[str] = None,
    status_code: Optional[int] = None,
    **extra: Any
) -> Dict[str, Any]:
    """
    Update the current audit context in-place with non-null values.
    Returns the updated context dictionary.
    """
    ctx = get_audit_context()
    
    if user_id is not None:
        ctx["user_id"] = user_id
    if user_name is not None:
        ctx["user_name"] = user_name
    if user_email is not None:
        ctx["user_email"] = user_email
    if company_id is not None:
        ctx["company_id"] = company_id
    if branch_id is not None:
        ctx["branch_id"] = branch_id
    if ip_address is not None:
        ctx["ip_address"] = ip_address
    if user_agent is not None:
        ctx["user_agent"] = user_agent
    if endpoint is not None:
        ctx["endpoint"] = endpoint
    if http_method is not None:
        ctx["http_method"] = http_method
    if status_code is not None:
        ctx["status_code"] = status_code
        
    for k, v in extra.items():
        if v is not None:
            ctx[k] = v
            
    return ctx

def reset_audit_context(ctx_dict: Optional[Dict[str, Any]] = None):
    """Reset the audit context to a fresh dict."""
    _audit_context.set(dict(ctx_dict) if ctx_dict is not None else {})

def clear_audit_context():
    """Clear all audit context variables."""
    _audit_context.set({})
