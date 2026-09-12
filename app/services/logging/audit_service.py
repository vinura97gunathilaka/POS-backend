"""
app.services.logging.audit_service
-----------------------------------
Enterprise audit service for explicit event logging, advanced query filtering,
statistics aggregation, record timeline histories, and CSV compliance exports.
"""

import io
import csv
import math
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc
from fastapi import Request

from app.core.audit_context import get_audit_context
from app.models.logging.audit_log import AuditLog
from app.models.auth.user import User

class AuditService:
    @staticmethod
    def get_client_ip(request: Request) -> Optional[str]:
        """Extract client IP from request headers or direct connection."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        return request.client.host if request.client else None

    @staticmethod
    def log_action(
        db: Session,
        action: str,
        *,
        company_id: Optional[int] = None,
        branch_id: Optional[int] = None,
        user_id: Optional[int] = None,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        model_name: Optional[str] = None,
        record_id: Optional[str] = None,
        old_data: Optional[Dict[str, Any]] = None,
        new_data: Optional[Dict[str, Any]] = None,
        changes: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        endpoint: Optional[str] = None,
        http_method: Optional[str] = None,
        status_code: Optional[int] = None,
        commit: bool = True
    ) -> AuditLog:
        """Explicitly log a system, security, or business event."""
        ctx = get_audit_context()
        
        audit_entry = AuditLog(
            company_id=company_id if company_id is not None else ctx.get("company_id"),
            branch_id=branch_id if branch_id is not None else ctx.get("branch_id"),
            user_id=user_id if user_id is not None else ctx.get("user_id"),
            user_name=user_name or ctx.get("user_name"),
            user_email=user_email or ctx.get("user_email"),
            action=action.upper(),
            model_name=model_name,
            record_id=str(record_id) if record_id is not None else None,
            old_data=old_data,
            new_data=new_data,
            changes=changes,
            details=details,
            ip_address=ip_address or ctx.get("ip_address"),
            user_agent=user_agent or ctx.get("user_agent"),
            endpoint=endpoint or ctx.get("endpoint"),
            http_method=http_method or ctx.get("http_method"),
            status_code=status_code or ctx.get("status_code")
        )

        db.add(audit_entry)
        if commit:
            db.commit()
            db.refresh(audit_entry)
        return audit_entry

    @staticmethod
    def log_login_success(db: Session, user: User, request: Request, details: Optional[Dict[str, Any]] = None):
        """Log a successful authentication event."""
        ip = AuditService.get_client_ip(request)
        ua = request.headers.get("user-agent")
        
        info = {
            "auth_method": "password",
            "is_superadmin": user.is_superadmin,
            "roles": [r.name for r in user.roles] if hasattr(user, "roles") else []
        }
        if details:
            info.update(details)

        AuditService.log_action(
            db=db,
            action="LOGIN",
            company_id=user.company_id,
            user_id=user.id,
            user_name=user.name,
            user_email=user.email,
            model_name="User",
            record_id=str(user.id),
            details=info,
            ip_address=ip,
            user_agent=ua,
            endpoint=request.url.path,
            http_method=request.method,
            status_code=200
        )

    @staticmethod
    def log_login_failure(db: Session, login_id: str, request: Request, reason: str = "Invalid credentials"):
        """Log a failed login attempt (security audit)."""
        ip = AuditService.get_client_ip(request)
        ua = request.headers.get("user-agent")

        AuditService.log_action(
            db=db,
            action="LOGIN_FAILED",
            model_name="User",
            details={
                "attempted_id": login_id,
                "reason": reason
            },
            ip_address=ip,
            user_agent=ua,
            endpoint=request.url.path,
            http_method=request.method,
            status_code=401
        )

    @staticmethod
    def log_password_change(db: Session, user: User, request: Request):
        """Log a user password change."""
        ip = AuditService.get_client_ip(request)
        ua = request.headers.get("user-agent")

        AuditService.log_action(
            db=db,
            action="PASSWORD_CHANGE",
            company_id=user.company_id,
            user_id=user.id,
            user_name=user.name,
            user_email=user.email,
            model_name="User",
            record_id=str(user.id),
            details={"status": "password_updated"},
            ip_address=ip,
            user_agent=ua,
            endpoint=request.url.path,
            http_method=request.method,
            status_code=200
        )

    @staticmethod
    def get_audit_logs(
        db: Session,
        *,
        company_id: Optional[int] = None,
        branch_id: Optional[int] = None,
        action: Optional[str] = None,
        model_name: Optional[str] = None,
        record_id: Optional[str] = None,
        user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 50
    ) -> Tuple[List[AuditLog], int, int]:
        """Query audit logs with multi-field filtering and pagination."""
        query = db.query(AuditLog)

        if company_id is not None:
            query = query.filter(AuditLog.company_id == company_id)
        if branch_id is not None:
            query = query.filter(AuditLog.branch_id == branch_id)
        if action:
            query = query.filter(func.upper(AuditLog.action) == action.strip().upper())
        if model_name:
            query = query.filter(func.lower(AuditLog.model_name) == model_name.strip().lower())
        if record_id:
            query = query.filter(AuditLog.record_id == str(record_id).strip())
        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)
        if date_from:
            query = query.filter(AuditLog.created_at >= date_from)
        if date_to:
            query = query.filter(AuditLog.created_at <= date_to)

        if search:
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    AuditLog.user_name.ilike(term),
                    AuditLog.user_email.ilike(term),
                    AuditLog.action.ilike(term),
                    AuditLog.model_name.ilike(term),
                    AuditLog.record_id.ilike(term),
                    AuditLog.ip_address.ilike(term),
                    AuditLog.endpoint.ilike(term)
                )
            )

        total_count = query.count()
        total_pages = math.ceil(total_count / limit) if limit > 0 else 1
        skip = (page - 1) * limit

        logs = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit).all()
        return logs, total_count, total_pages

    @staticmethod
    def get_record_history(
        db: Session,
        model_name: str,
        record_id: str,
        company_id: Optional[int] = None
    ) -> List[AuditLog]:
        """Fetch the full change history timeline of a specific model record."""
        query = db.query(AuditLog).filter(
            func.lower(AuditLog.model_name) == model_name.strip().lower(),
            AuditLog.record_id == str(record_id).strip()
        )
        if company_id is not None:
            query = query.filter(AuditLog.company_id == company_id)

        return query.order_by(desc(AuditLog.created_at)).all()

    @staticmethod
    def get_statistics(db: Session, company_id: Optional[int] = None) -> Dict[str, Any]:
        """Aggregate summary metrics of system changes and security activities."""
        base_query = db.query(AuditLog)
        if company_id is not None:
            base_query = base_query.filter(AuditLog.company_id == company_id)

        total_events = base_query.count()

        # Action breakdown
        action_counts = (
            base_query.with_entities(AuditLog.action, func.count(AuditLog.id))
            .group_by(AuditLog.action)
            .all()
        )
        actions_dict = {a: count for a, count in action_counts}

        # Model breakdown
        model_counts = (
            base_query.filter(AuditLog.model_name != None)
            .with_entities(AuditLog.model_name, func.count(AuditLog.id))
            .group_by(AuditLog.model_name)
            .order_by(desc(func.count(AuditLog.id)))
            .limit(10)
            .all()
        )
        models_dict = {m: count for m, count in model_counts}

        # Top active users
        user_counts = (
            base_query.filter(AuditLog.user_name != None)
            .with_entities(AuditLog.user_name, func.count(AuditLog.id))
            .group_by(AuditLog.user_name)
            .order_by(desc(func.count(AuditLog.id)))
            .limit(5)
            .all()
        )
        users_dict = {u: count for u, count in user_counts}

        return {
            "total_events": total_events,
            "actions": actions_dict,
            "top_models": models_dict,
            "top_operators": users_dict
        }

    @staticmethod
    def export_csv(
        db: Session,
        *,
        company_id: Optional[int] = None,
        action: Optional[str] = None,
        model_name: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> str:
        """Export audit logs to CSV string format."""
        logs, _, _ = AuditService.get_audit_logs(
            db,
            company_id=company_id,
            action=action,
            model_name=model_name,
            date_from=date_from,
            date_to=date_to,
            page=1,
            limit=5000  # Reasonable export ceiling
        )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID", "Timestamp (UTC)", "Action", "Model", "Record ID",
            "Operator Name", "Operator Email", "IP Address", "Endpoint", "Method", "Status Code"
        ])

        for log in logs:
            writer.writerow([
                log.id,
                log.created_at.isoformat() if log.created_at else "",
                log.action,
                log.model_name or "",
                log.record_id or "",
                log.user_name or "",
                log.user_email or "",
                log.ip_address or "",
                log.endpoint or "",
                log.http_method or "",
                log.status_code or ""
            ])

        return output.getvalue()
