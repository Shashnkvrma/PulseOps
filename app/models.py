from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String, nullable=False)
    title = Column(String, nullable=False)
    severity = Column(String, default="medium")
    status = Column(String, default="open")
    investigation_state = Column(String, default="open")
    created_at = Column(DateTime, nullable=False)
    resolved_at = Column(DateTime, nullable=True)