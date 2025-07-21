# models/metadata.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

from src.infrastructure.db.models.document_metadata import DocumentMetadata, DocumentStatus


Base = declarative_base()

class DocumentType(str, Enum):
    FACTURA = "factura"
    BOLETA = "boleta"
    NOTA_CREDITO = "nota_credito"
    NOTA_DEBITO = "nota_debito"
    GUIA_DESPACHO = "guia_despacho"
    ORDEN_COMPRA = "orden_compra"
    COTIZACION = "cotizacion"
    CONTRATO = "contrato"
    BALANCE = "balance"
    ESTADO_RESULTADO = "estado_resultado"
    FLUJO_EFECTIVO = "flujo_efectivo"
    COMPROBANTE_EGRESO = "comprobante_egreso"
    COMPROBANTE_INGRESO = "comprobante_ingreso"
    COMPROBANTE_DIARIO = "comprobante_diario"
    DECLARACION_IVA = "declaracion_iva"
    DECLARACION_RENTA = "declaracion_renta"
    CERTIFICADO_TRIBUTARIO = "certificado_tributario"
    OTROS = "otros"


# Modelo Pydantic para respuesta del AI
class AIMetadataResponse(BaseModel):
    """Estructura que debe devolver el modelo de IA"""

    # Clasificación del documento
    document_type: DocumentType = Field(description="Tipo de documento identificado")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confianza en la clasificación (0-1)")

    # Información básica
    document_number: Optional[str] = Field(None, description="Número del documento (factura, boleta, etc.)")
    document_date: Optional[str] = Field(None, description="Fecha del documento en formato YYYY-MM-DD")
    due_date: Optional[str] = Field(None, description="Fecha de vencimiento en formato YYYY-MM-DD")

    # Información de empresas/personas - CAMPOS INTERNOS OPCIONALES
    issuer: Optional[Dict[str, Optional[str]]] = Field(None, description="Empresa emisora: {name, rut, address}")
    client: Optional[Dict[str, Optional[str]]] = Field(None, description="Cliente/receptor: {name, rut, address}")

    # Información financiera - CAMPOS INTERNOS OPCIONALES
    amounts: Optional[Dict[str, Optional[float]]] = Field(None, description="Montos: {total, net, tax, other_taxes}")
    currency: str = Field(default="CLP", description="Moneda del documento")

    # Contenido y clasificación
    description: str = Field(description="Descripción del contenido del documento")
    tags: List[str] = Field(default_factory=list, description="Tags relevantes para búsqueda")

    # Campos específicos para contadores
    accounting_period: Optional[str] = Field(None, description="Período contable (YYYY-MM)")
    account_codes: List[str] = Field(default_factory=list, description="Códigos de cuenta contable sugeridos")
    requires_review: bool = Field(default=False, description="Si el documento requiere revisión manual")

    # Información adicional extraída del texto
    extracted_text: str = Field(description="Texto principal extraído del documento")
    key_data: Dict[str, Optional[str]] = Field(default_factory=dict, description="Datos clave extra extraídos")

# Modelo Pydantic para crear metadatos
class CreateMetadata(BaseModel):
    file_id: int
    ai_response: AIMetadataResponse

# Modelo Pydantic para respuesta de API
class MetadataResponse(BaseModel):
    id: int
    file_id: int
    document_type: Optional[str]
    document_number: Optional[str]
    document_date: Optional[datetime]
    due_date: Optional[datetime]
    company_name: Optional[str]
    company_rut: Optional[str]
    client_name: Optional[str]
    client_rut: Optional[str]
    total_amount: Optional[float]
    net_amount: Optional[float]
    tax_amount: Optional[float]
    currency: str
    description: Optional[str]
    tags: Optional[List[str]]
    confidence_score: Optional[float]
    status: str
    processed_at: datetime
    needs_review: bool

    class Config:
        from_attributes = True

# Función para convertir respuesta AI a modelo de BD
def ai_response_to_db_metadata(ai_response: AIMetadataResponse, file_id: int) -> DocumentMetadata:
    """Convierte la respuesta del AI al modelo de base de datos"""

    # Parsear fechas si existen
    document_date = None
    due_date = None

    if ai_response.document_date:
        try:
            document_date = datetime.strptime(ai_response.document_date, "%Y-%m-%d")
        except ValueError:
            pass

    if ai_response.due_date:
        try:
            due_date = datetime.strptime(ai_response.due_date, "%Y-%m-%d")
        except ValueError:
            pass

    # Extraer información de empresas con manejo seguro de None
    company_name = None
    company_rut = None
    client_name = None
    client_rut = None

    if ai_response.issuer:
        company_name = ai_response.issuer.get("name")
        company_rut = ai_response.issuer.get("rut")

    if ai_response.client:
        client_name = ai_response.client.get("name")
        client_rut = ai_response.client.get("rut")

    # Extraer montos con manejo seguro de None
    total_amount = None
    net_amount = None
    tax_amount = None

    if ai_response.amounts:
        total_amount = ai_response.amounts.get("total")
        net_amount = ai_response.amounts.get("net")
        tax_amount = ai_response.amounts.get("tax")

    return DocumentMetadata(
        file_id=file_id,
        document_type=ai_response.document_type.value,
        document_number=ai_response.document_number,
        document_date=document_date,
        due_date=due_date,
        company_name=company_name,
        company_rut=company_rut,
        client_name=client_name,
        client_rut=client_rut,
        total_amount=total_amount,
        net_amount=net_amount,
        tax_amount=tax_amount,
        currency=ai_response.currency,
        description=ai_response.description,
        tags=ai_response.tags,
        confidence_score=ai_response.confidence_score,
        needs_review=ai_response.requires_review,
        status=DocumentStatus.PROCESADO.value
    )