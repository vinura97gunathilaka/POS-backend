from sqlalchemy import Column, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BranchAuditMixin

class CSATFeedback(Base, BranchAuditMixin):
    __tablename__ = "csat_feedbacks"

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    rating = Column(Integer, nullable=False) # 1 to 5
    feedback_text = Column(Text, nullable=True)

    company = relationship("Company")
    branch = relationship("Branch")
    sale = relationship("Sale", back_populates="csat_feedback")
