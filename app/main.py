import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime, UTC

from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Incident


# ============================================================
# LOGGING
# ============================================================

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

log_file = LOG_DIR / "pulseops.log"

file_handler = RotatingFileHandler(
    log_file,
    maxBytes=5_000_000,
    backupCount=3,
    encoding="utf-8"
)

console_handler = logging.StreamHandler()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        file_handler,
        console_handler
    ]
)

logger = logging.getLogger("pulseops")


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="PulseOps",
    description="Production Incident & Reliability Intelligence Platform",
    version="1.0.0"
)


# ============================================================
# DATABASE SESSION
# ============================================================

def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================

class IncidentCreate(BaseModel):
    service_name: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")


class IncidentOut(BaseModel):
    id: int
    service_name: str
    title: str
    severity: str
    status: str
    investigation_state: str
    created_at: datetime
    resolved_at: datetime | None

    class Config:
        from_attributes = True


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    logger.info("Home endpoint called")

    return {
        "message": "PulseOps is running"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    logger.info("Health check requested")

    return {
        "status": "healthy"
    }


# ============================================================
# LIST INCIDENTS
# ============================================================

@app.get(
    "/incidents",
    response_model=list[IncidentOut]
)
def list_incidents(
    db: Session = Depends(get_db)
):
    logger.info("Fetching all incidents")

    incidents = db.query(Incident).all()

    logger.info(
        "Returned %d incidents",
        len(incidents)
    )

    return incidents


# ============================================================
# CREATE INCIDENT
# ============================================================

@app.post(
    "/incidents",
    response_model=IncidentOut,
    status_code=status.HTTP_201_CREATED
)
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db)
):
    logger.info(
        "Creating incident | service=%s | severity=%s | title=%s",
        payload.service_name,
        payload.severity,
        payload.title
    )

    incident = Incident(
        service_name=payload.service_name,
        title=payload.title,
        severity=payload.severity,
        status="open",
        investigation_state="open",
        created_at=datetime.now(UTC)
    )

    try:
        db.add(incident)
        db.commit()
        db.refresh(incident)

        logger.info(
            "Incident created successfully | id=%s",
            incident.id
        )

        return incident

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to create incident"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to create incident"
        )


# ============================================================
# INVESTIGATE INCIDENT
# ============================================================

@app.post(
    "/incidents/{incident_id}/investigate",
    response_model=IncidentOut
)
def investigate_incident(
    incident_id: int,
    db: Session = Depends(get_db)
):
    logger.info(
        "Investigating incident | id=%s",
        incident_id
    )

    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if not incident:
        logger.warning(
            "Incident not found | id=%s",
            incident_id
        )

        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    # A resolved incident cannot be investigated again.
    if incident.status == "resolved":
        logger.warning(
            "Cannot investigate resolved incident | id=%s",
            incident_id
        )

        raise HTTPException(
            status_code=409,
            detail="Resolved incident cannot be investigated"
        )

    incident.investigation_state = "investigating"

    try:
        db.commit()
        db.refresh(incident)

        logger.info(
            "Incident marked as investigating | id=%s",
            incident_id
        )

        return incident

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to investigate incident | id=%s",
            incident_id
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to investigate incident"
        )


# ============================================================
# RESOLVE INCIDENT
# ============================================================

@app.post(
    "/incidents/{incident_id}/resolve",
    response_model=IncidentOut
)
def resolve_incident(
    incident_id: int,
    db: Session = Depends(get_db)
):
    logger.info(
        "Resolving incident | id=%s",
        incident_id
    )

    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id)
        .first()
    )

    if not incident:
        logger.warning(
            "Incident not found | id=%s",
            incident_id
        )

        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    # A resolved incident cannot be resolved again.
    if incident.status == "resolved":
        logger.warning(
            "Incident already resolved | id=%s",
            incident_id
        )

        raise HTTPException(
            status_code=409,
            detail="Incident is already resolved"
        )

    incident.status = "resolved"
    incident.investigation_state = "resolved"
    incident.resolved_at = datetime.now(UTC)

    try:
        db.commit()
        db.refresh(incident)

        logger.info(
            "Incident resolved successfully | id=%s",
            incident_id
        )

        return incident

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to resolve incident | id=%s",
            incident_id
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to resolve incident"
        )