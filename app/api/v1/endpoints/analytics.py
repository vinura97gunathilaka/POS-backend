from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.rbac import User, Branch
from app.models.catalog import ProductVariant, Product, Category
from app.models.sales import Sale, SaleItem, Payment, CSATFeedback
from app.schemas.response import APIResponse

router = APIRouter()

@router.get("/dashboard", response_model=APIResponse[dict])
def get_analytics_dashboard(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    branch_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Enforce company bounds (unless superadmin)
    company_id = current_user.company_id

    # Resolve date boundaries
    parsed_start = None
    parsed_end = None
    
    try:
        if start_date:
            cleaned_start = start_date.replace("Z", "+00:00")
            # Handle short dates YYYY-MM-DD
            if len(cleaned_start) == 10:
                parsed_start = datetime.strptime(cleaned_start, "%Y-%m-%d")
            else:
                parsed_start = datetime.fromisoformat(cleaned_start)
        else:
            # Default to last 30 days
            parsed_start = datetime.utcnow() - timedelta(days=30)
            
        if end_date:
            cleaned_end = end_date.replace("Z", "+00:00")
            if len(cleaned_end) == 10:
                parsed_end = datetime.strptime(cleaned_end, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            else:
                parsed_end = datetime.fromisoformat(cleaned_end)
        else:
            parsed_end = datetime.utcnow()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO-8601 or YYYY-MM-DD")

    # Build primary query
    sales_query = db.query(Sale).filter(
        Sale.deleted_at == None,
        Sale.sale_status == "completed"
    )

    if not current_user.is_superadmin:
        sales_query = sales_query.filter(Sale.company_id == company_id)
        if branch_id:
            sales_query = sales_query.filter(Sale.branch_id == branch_id)
    elif branch_id:
        sales_query = sales_query.filter(Sale.branch_id == branch_id)

    # Filter dates
    sales_query = sales_query.filter(
        Sale.sale_date >= parsed_start,
        Sale.sale_date <= parsed_end
    )

    sales = sales_query.all()
    sale_ids = [s.id for s in sales]

    # Sub-totals & summaries
    total_revenue = sum(float(s.net_amount) for s in sales)
    total_tax = sum(float(s.tax_amount) for s in sales)
    total_discount = sum(float(s.discount_amount) for s in sales)
    total_transactions = len(sales)
    average_order_value = total_revenue / total_transactions if total_transactions > 0 else 0.0

    # Fetch items for COGS/margin
    items = db.query(SaleItem).filter(SaleItem.sale_id.in_(sale_ids)).all() if sale_ids else []
    total_cost = sum(float(item.quantity * item.unit_cost) for item in items)
    total_profit = total_revenue - total_cost
    margin_percent = (total_profit / total_revenue) * 100 if total_revenue > 0 else 0.0

    # 1. Sales Trend (Progress graph by Date)
    daily_data = {}
    
    # Initialize date ranges to avoid gaps in visual charts (up to 31 days)
    delta_days = (parsed_end - parsed_start).days
    if delta_days <= 31:
        for i in range(delta_days + 1):
            d = (parsed_start + timedelta(days=i)).strftime("%Y-%m-%d")
            daily_data[d] = {"date": d, "revenue": 0.0, "cost": 0.0, "profit": 0.0, "transactions": 0}
            
    for s in sales:
        d_str = s.sale_date.strftime("%Y-%m-%d")
        if d_str not in daily_data:
            daily_data[d_str] = {"date": d_str, "revenue": 0.0, "cost": 0.0, "profit": 0.0, "transactions": 0}
        daily_data[d_str]["revenue"] += float(s.net_amount)
        daily_data[d_str]["transactions"] += 1

    for item in items:
        sale = next((s for s in sales if s.id == item.sale_id), None)
        if sale:
            d_str = sale.sale_date.strftime("%Y-%m-%d")
            c = float(item.quantity * item.unit_cost)
            if d_str in daily_data:
                daily_data[d_str]["cost"] += c

    for k, v in daily_data.items():
        v["profit"] = v["revenue"] - v["cost"]
        
    sales_trend = sorted(daily_data.values(), key=lambda x: x["date"])

    # Load lookup maps to prevent N+1 query patterns
    variant_ids = list(set(item.product_variant_id for item in items))
    variants = db.query(ProductVariant).filter(ProductVariant.id.in_(variant_ids)).all() if variant_ids else []
    variant_map = {v.id: v for v in variants}

    product_ids = list(set(v.product_id for v in variants))
    products = db.query(Product).filter(Product.id.in_(product_ids)).all() if product_ids else []
    product_map = {p.id: p for p in products}

    category_ids = list(set(p.category_id for p in products if p.category_id))
    categories = db.query(Category).filter(Category.id.in_(category_ids)).all() if category_ids else []
    category_map = {c.id: c for c in categories}

    # 2. Category Breakdown
    cat_rev = {}
    for item in items:
        v = variant_map.get(item.product_variant_id)
        cname = "Uncategorized"
        if v:
            p = product_map.get(v.product_id)
            if p and p.category_id:
                c = category_map.get(p.category_id)
                if c:
                    cname = c.name
        cat_rev[cname] = cat_rev.get(cname, 0.0) + float(item.total_amount)

    category_breakdown = []
    for name, rev in cat_rev.items():
        pct = (rev / total_revenue) * 100 if total_revenue > 0 else 0.0
        category_breakdown.append({
            "category_name": name,
            "revenue": round(rev, 2),
            "percentage": round(pct, 2)
        })
    category_breakdown = sorted(category_breakdown, key=lambda x: x["revenue"], reverse=True)

    # 3. Top Products (Top 5 Best Sellers)
    prod_stats = {}
    for item in items:
        vid = item.product_variant_id
        if vid not in prod_stats:
            prod_stats[vid] = {"quantity_sold": 0, "revenue": 0.0, "cost": 0.0}
        prod_stats[vid]["quantity_sold"] += item.quantity
        prod_stats[vid]["revenue"] += float(item.total_amount)
        prod_stats[vid]["cost"] += float(item.quantity * item.unit_cost)

    top_products = []
    for vid, stat in prod_stats.items():
        v = variant_map.get(vid)
        pname = f"{v.product.name} - {v.name}" if (v and v.product) else f"Variant #{vid}"
        sku = v.sku if v else "N/A"
        prof = stat["revenue"] - stat["cost"]
        top_products.append({
            "product_name": pname,
            "sku": sku,
            "quantity_sold": stat["quantity_sold"],
            "revenue": round(stat["revenue"], 2),
            "profit": round(prof, 2)
        })
    top_products = sorted(top_products, key=lambda x: x["quantity_sold"], reverse=True)[:5]

    # 4. Cashier Performance with Audits
    user_ids = list(set(s.user_id for s in sales))
    users = db.query(User).filter(User.id.in_(user_ids)).all() if user_ids else []
    user_map = {u.id: u for u in users}

    cashier_stats = {}
    for s in sales:
        uid = s.user_id
        if uid not in cashier_stats:
            cashier_stats[uid] = {"revenue": 0.0, "transactions": 0}
        cashier_stats[uid]["revenue"] += float(s.net_amount)
        cashier_stats[uid]["transactions"] += 1

    # Shift variance query
    from app.models.finance import Shift
    from app.models.logging import AuditLog
    
    shifts_query = db.query(Shift).filter(Shift.status == "closed")
    if not current_user.is_superadmin:
        shifts_query = shifts_query.filter(Shift.company_id == company_id)
    shifts = shifts_query.all()
    
    cashier_variance = {}
    for sh in shifts:
        uid = sh.user_id
        cashier_variance[uid] = cashier_variance.get(uid, 0.0) + float(sh.variance or 0.0)
        
    # Get all void audit logs
    audit_query = db.query(AuditLog).filter(AuditLog.action == "sale_cancellation")
    if not current_user.is_superadmin:
        audit_query = audit_query.filter(AuditLog.company_id == company_id)
    audits = audit_query.all()
    
    cashier_voids = {}
    for au in audits:
        uid = au.user_id
        cashier_voids[uid] = cashier_voids.get(uid, 0) + 1

    cashier_performance = []
    for uid, stat in cashier_stats.items():
        u = user_map.get(uid)
        uname = u.name if u else f"Staff #{uid}"
        aov = stat["revenue"] / stat["transactions"] if stat["transactions"] > 0 else 0.0
        
        variance_amt = cashier_variance.get(uid, 0.0)
        voids_cnt = cashier_voids.get(uid, 0)
        
        cashier_performance.append({
            "cashier_name": uname,
            "revenue": round(stat["revenue"], 2),
            "transactions": stat["transactions"],
            "aov": round(aov, 2),
            "total_variance": round(variance_amt, 2),
            "voids_count": voids_cnt
        })
    cashier_performance = sorted(cashier_performance, key=lambda x: x["revenue"], reverse=True)

    # 5. Branch Performance
    branch_ids = list(set(s.branch_id for s in sales))
    branches = db.query(Branch).filter(Branch.id.in_(branch_ids)).all() if branch_ids else []
    branch_map = {b.id: b for b in branches}

    branch_stats = {}
    for s in sales:
        bid = s.branch_id
        if bid not in branch_stats:
            branch_stats[bid] = {"revenue": 0.0, "transactions": 0}
        branch_stats[bid]["revenue"] += float(s.net_amount)
        branch_stats[bid]["transactions"] += 1

    branch_performance = []
    for bid, stat in branch_stats.items():
        b = branch_map.get(bid)
        bname = b.name if b else f"Branch #{bid}"
        aov = stat["revenue"] / stat["transactions"] if stat["transactions"] > 0 else 0.0
        branch_performance.append({
            "branch_name": bname,
            "revenue": round(stat["revenue"], 2),
            "transactions": stat["transactions"],
            "aov": round(aov, 2)
        })
    branch_performance = sorted(branch_performance, key=lambda x: x["revenue"], reverse=True)

    # 6. Payment Methods Breakdown
    payments = db.query(Payment).filter(Payment.sale_id.in_(sale_ids)).all() if sale_ids else []
    pay_methods = {}
    for p in payments:
        method = p.payment_method.upper()
        pay_methods[method] = pay_methods.get(method, 0.0) + float(p.amount)

    total_payments = sum(pay_methods.values())
    payment_methods = []
    for m, amt in pay_methods.items():
        pct = (amt / total_payments) * 100 if total_payments > 0 else 0.0
        payment_methods.append({
            "method": m,
            "amount": round(amt, 2),
            "percentage": round(pct, 2)
        })
    payment_methods = sorted(payment_methods, key=lambda x: x["amount"], reverse=True)

    # 7. Intraday Hourly Heatmap Grid (7 weekdays x 24 hour slots)
    days_list = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    heatmap_data = {}
    for d in days_list:
        for h in range(24):
            heatmap_data[(d, h)] = {"day": d, "hour": h, "transactions": 0, "revenue": 0.0}
            
    for s in sales:
        w_idx = int(s.sale_date.strftime("%w"))
        day_name = days_list[w_idx]
        hour = s.sale_date.hour
        key = (day_name, hour)
        if key in heatmap_data:
            heatmap_data[key]["transactions"] += 1
            heatmap_data[key]["revenue"] += float(s.net_amount)
            
    heatmap_list = list(heatmap_data.values())

    # 8. Recent Audit Logs Feed
    recent_audits_query = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    if not current_user.is_superadmin:
        recent_audits_query = recent_audits_query.filter(AuditLog.company_id == company_id)
    recent_audits = recent_audits_query.limit(20).all()
    
    recent_audits_list = []
    for log in recent_audits:
        recent_audits_list.append({
            "id": log.id,
            "action": log.action,
            "details": log.details,
            "created_at": log.created_at.isoformat(),
            "user_name": log.user.name if log.user else "System"
        })

    # Compile result data
    analytics_data = {
        "summary": {
            "total_revenue": round(total_revenue, 2),
            "total_cost": round(total_cost, 2),
            "total_profit": round(total_profit, 2),
            "margin_percent": round(margin_percent, 2),
            "total_sales_count": total_transactions,
            "average_order_value": round(average_order_value, 2),
            "total_tax": round(total_tax, 2),
            "total_discount": round(total_discount, 2)
        },
        "sales_trend": sales_trend,
        "category_breakdown": category_breakdown,
        "top_products": top_products,
        "cashier_performance": cashier_performance,
        "branch_performance": branch_performance,
        "payment_methods": payment_methods,
        "intraday_heatmap": heatmap_list,
        "recent_audits": recent_audits_list
    }

    return APIResponse(data=analytics_data)


@router.get("/csat", response_model=APIResponse[dict])
def list_csat_feedbacks(
    page: int = 1,
    limit: int = 10,
    branch_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    company_id = current_user.company_id
    query = db.query(CSATFeedback).filter(CSATFeedback.company_id == company_id)
    if not current_user.is_superadmin:
        if branch_id:
            query = query.filter(CSATFeedback.branch_id == branch_id)
    elif branch_id:
        query = query.filter(CSATFeedback.branch_id == branch_id)

    total_count = query.count()
    feedbacks = query.order_by(CSATFeedback.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    # Calculate average rating
    from sqlalchemy import func
    avg_rating_val = db.query(func.avg(CSATFeedback.rating)).filter(CSATFeedback.company_id == company_id)
    if branch_id:
        avg_rating_val = avg_rating_val.filter(CSATFeedback.branch_id == branch_id)
    avg_rating = avg_rating_val.scalar() or 0.0

    # Counts by rating level (1 to 5)
    counts_by_rating = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    counts_query = db.query(CSATFeedback.rating, func.count(CSATFeedback.id)).filter(CSATFeedback.company_id == company_id)
    if branch_id:
        counts_query = counts_query.filter(CSATFeedback.branch_id == branch_id)
    counts_data = counts_query.group_by(CSATFeedback.rating).all()
    for rating_val, count_val in counts_data:
        if rating_val in counts_by_rating:
            counts_by_rating[rating_val] = count_val

    # Construct clean response
    data = {
        "feedbacks": [
            {
                "id": f.id,
                "sale_id": f.sale_id,
                "invoice_number": f.sale.invoice_number if f.sale else "N/A",
                "branch_name": f.branch.name if f.branch else "N/A",
                "rating": f.rating,
                "feedback_text": f.feedback_text,
                "created_at": f.created_at.isoformat() if f.created_at else None
            }
            for f in feedbacks
        ],
        "summary": {
            "average_rating": round(float(avg_rating), 2),
            "total_count": total_count,
            "counts": counts_by_rating
        },
        "pagination": {
            "total": total_count,
            "pages": (total_count + limit - 1) // limit if total_count > 0 else 0,
            "current_page": page,
            "limit": limit
        }
    }
    return APIResponse(data=data)

