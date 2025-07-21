from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, Float, Text, JSON, Column
from datetime import datetime
from src.utils.timing import now

from enum import Enum

from .base import BaseModel



class DocumentStatus(str, Enum):
    PENDIENTE = "pendiente"
    PROCESADO = "procesado"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    ARCHIVADO = "archivado"


# Modelo SQLAlchemy para la base de datos
class DocumentMetadata(BaseModel):
    __tablename__ = "document_metadata"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("file.id"), nullable=False)

    # Información básica del documento
    document_type = Column(String(50), nullable=True)
    document_number = Column(String(100), nullable=True)
    document_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)

    # Información de empresa/cliente
    company_name = Column(String(255), nullable=True)
    company_rut = Column(String(20), nullable=True)
    client_name = Column(String(255), nullable=True)
    client_rut = Column(String(20), nullable=True)

    # Información financiera
    total_amount = Column(Float, nullable=True)
    net_amount = Column(Float, nullable=True)
    tax_amount = Column(Float, nullable=True)
    currency = Column(String(10), default="CLP")

    # Metadatos adicionales
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Lista de tags como JSON
    confidence_score = Column(Float, nullable=True)  # Confianza del AI

    # Control
    status = Column(String(20), default=DocumentStatus.PENDIENTE.value)
    processed_at = Column(DateTime, default=now)
    needs_review = Column(Boolean, default=False)

    # Relación con el archivo principal
    file = relationship("File", back_populates="document_metadata")
