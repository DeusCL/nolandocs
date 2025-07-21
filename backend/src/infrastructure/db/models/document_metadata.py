from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, Float, Text, JSON
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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    file_id: Mapped[int] = mapped_column(Integer, ForeignKey("file.id"), nullable=False)

    # Información básica del documento
    document_type: Mapped[str] = mapped_column(String(50), nullable=True)
    document_number: Mapped[str] = mapped_column(String(100), nullable=True)
    document_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Información de empresa/cliente
    company_name: Mapped[str] = mapped_column(String(255), nullable=True)
    company_rut: Mapped[str] = mapped_column(String(20), nullable=True)
    client_name: Mapped[str] = mapped_column(String(255), nullable=True)
    client_rut: Mapped[str] = mapped_column(String(20), nullable=True)

    # Información financiera
    total_amount: Mapped[float] = mapped_column(Float, nullable=True)
    net_amount: Mapped[float] = mapped_column(Float, nullable=True)
    tax_amount: Mapped[float] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="CLP")

    # Metadatos adicionales
    description: Mapped[str] = mapped_column(Text, nullable=True)
    tags: Mapped[dict] = mapped_column(JSON, nullable=True)  # Lista de tags como JSON
    confidence_score: Mapped[float] = mapped_column(Float, nullable=True)  # Confianza del AI

    # Control
    status: Mapped[str] = mapped_column(String(20), default=DocumentStatus.PENDIENTE.value)
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relación con el archivo principal
    file = relationship("File", back_populates="document_metadata")
