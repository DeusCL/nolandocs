import secrets
from pathlib import Path
from typing import Optional

from litestar import Litestar, get, post, delete as litestar_delete, patch
from litestar.params import Body
from litestar.response import Template
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.plugins.sqlalchemy import SQLAlchemyPlugin
from litestar.di import Provide
from litestar.exceptions import HTTPException, NotFoundException
from litestar.response import File as FileResponse
from litestar import MediaType

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

import mimetypes
from pydantic import BaseModel

from src.core.config.settings import env_vars
from src.core.config.logging import logging_config
from src.core.config.constants import ROOT_PATH
# from src.api.routes_v1 import routes
from src.api.middlewares.auth import AuthMiddleware
from src.api.templates import template_config, static_files
from src.infrastructure.db.models.file import File
from src.infrastructure.db.config import config_db

# Importar nuevos modelos y servicios
from src.infrastructure.db.models.enums import DocumentMetadata, ai_response_to_db_metadata, MetadataResponse
from src.gemini_service import get_gemini_analyzer, init_gemini_service





@get("/")
async def index() -> Template:
    return Template(template_name="index.html")


@post("/upload")
async def upload_file(
    db: AsyncSession,
    data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),
    description: str = Body(media_type=RequestEncodingType.MULTI_PART, default=""),
) -> dict:
    print(db)
    upload_dir = ROOT_PATH / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generar nombre aleatorio
    random_name = secrets.token_hex(16) + Path(data.filename).suffix
    file_location = upload_dir / random_name

    # Leer el contenido UNA SOLA VEZ
    content = await data.read()

    # Escribir el contenido leído
    with open(file_location, "wb") as f:
        f.write(content)  # Usar el contenido ya leído

    # Guardar info en DB
    new_file = File(
        original_name=data.filename,
        stored_name=random_name,
        description=description,
        size=len(content),  # Ahora tendrá el tamaño correcto
        path=str(file_location)
    )
    db.add(new_file)
    await db.commit()
    await db.refresh(new_file)

    # Analizar archivo con IA (asíncrono para no bloquear la respuesta)
    analysis_result = "processing"
    analyzer = get_gemini_analyzer()

    if analyzer:
        try:
            # Analizar documento con Gemini
            ai_response = await analyzer.analyze_document(
                str(file_location),
                data.filename
            )

            if ai_response:
                # Convertir respuesta AI a modelo de BD
                metadata = ai_response_to_db_metadata(ai_response, new_file.id)
                db.add(metadata)
                await db.commit()
                await db.refresh(metadata)
                analysis_result = "completed"
            else:
                analysis_result = "failed"

        except Exception as e:
            print(f"Error en análisis de IA: {str(e)}")
            analysis_result = "failed"


    return {
        "message": f"Archivo '{data.filename}' guardado con nombre '{random_name}'",
        "description": description,
        "file_id": new_file.id,
        "analysis_status": analysis_result
    }


@get("/files")
async def get_files(db: AsyncSession) -> list[dict]:
    """Obtiene todos los archivos con sus metadatos"""
    # Query join para obtener archivos y metadatos
    query = select(File, DocumentMetadata).outerjoin(
        DocumentMetadata, File.id == DocumentMetadata.file_id
    )
    result = await db.execute(query)
    files_with_metadata = result.all()

    files_list = []
    for file_row, metadata_row in files_with_metadata:
        file_data = {
            "id": file_row.id,
            "original_name": file_row.original_name,
            "stored_name": file_row.stored_name,
            "description": file_row.description,
            "size": file_row.size,
            "path": file_row.path,
            "metadata": None
        }

        if metadata_row:
            file_data["metadata"] = {
                "document_type": metadata_row.document_type,
                "document_number": metadata_row.document_number,
                "document_date": metadata_row.document_date.isoformat() if metadata_row.document_date else None,
                "company_name": metadata_row.company_name,
                "client_name": metadata_row.client_name,
                "total_amount": metadata_row.total_amount,
                "currency": metadata_row.currency,
                "tags": metadata_row.tags,
                "confidence_score": metadata_row.confidence_score,
                "status": metadata_row.status,
                "needs_review": metadata_row.needs_review
            }

        files_list.append(file_data)

    return files_list


@litestar_delete("/files/{file_id:int}", status_code=200)
async def delete_file(file_id: int, db: AsyncSession) -> dict:
    """Elimina un archivo y sus metadatos"""
    result = await db.execute(select(File).filter(File.id == file_id))
    file = result.scalar_one_or_none()

    if not file:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    # Borrar archivo del sistema de archivos
    try:
        path = Path(file.path)
        if path.exists():
            path.unlink()
    except Exception as e:
        pass

    # Borrar metadatos asociados
    await db.execute(delete(DocumentMetadata).filter(DocumentMetadata.file_id == file_id))

    # Borrar archivo de la base de datos
    await db.execute(delete(File).filter(File.id == file_id))
    await db.commit()

    return {"message": f"Archivo con id {file_id} eliminado"}


class UpdateDescriptionRequest(BaseModel):
    description: str

@patch("/files/{file_id:int}")
async def update_file_description(
    db: AsyncSession,
    file_id: int,
    data: UpdateDescriptionRequest = Body(),
) -> dict:
    result = await db.execute(select(File).filter(File.id == file_id))
    file = result.scalar_one_or_none()
    if not file:
        raise NotFoundException("Archivo no encontrado")

    file.description = data.description
    db.add(file)
    await db.commit()
    await db.refresh(file)

    return {
        "message": f"Descripción del archivo con id {file_id} actualizada",
        "file_id": file.id,
        "new_description": file.description,
    }



@get("/files/{file_id:int}/download")
async def download_file(file_id: int, db: AsyncSession) -> FileResponse:
    # Buscar el archivo en la base de datos
    result = await db.execute(select(File).filter(File.id == file_id))
    file = result.scalar_one_or_none()

    if not file:
        raise NotFoundException("Archivo no encontrado")

    # Verificar que el archivo existe en el sistema de archivos
    file_path = Path(file.path)
    if not file_path.exists():
        raise NotFoundException("El archivo físico no existe")

    # Determinar el tipo MIME
    mime_type, _ = mimetypes.guess_type(file.original_name)
    if mime_type is None:
        mime_type = "application/octet-stream"

    # Retornar el archivo para descarga
    return FileResponse(
        path=file_path,
        filename=file.original_name,  # Usar el nombre original para la descarga
        media_type=mime_type,
        content_disposition_type="attachment"  # Fuerza la descarga
    )


@get("/files/{file_id:int}/metadata")
async def get_file_metadata(file_id: int, db: AsyncSession) -> MetadataResponse:
    """Obtiene los metadatos de un archivo específico"""
    result = await db.execute(
        select(DocumentMetadata).filter(DocumentMetadata.file_id == file_id)
    )
    metadata = result.scalar_one_or_none()

    if not metadata:
        raise NotFoundException("Metadatos no encontrados")

    return MetadataResponse.from_orm(metadata)


@get("/search")
async def search_documents(
    db: AsyncSession,
    query: Optional[str] = None,
    document_type: Optional[str] = None,
    company: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
) -> list[dict]:
    """Busca documentos por diferentes criterios"""

    # Construir query base
    base_query = select(File, DocumentMetadata).outerjoin(
        DocumentMetadata, File.id == DocumentMetadata.file_id
    )

    # Aplicar filtros
    if query:
        base_query = base_query.where(
            File.original_name.ilike(f"%{query}%") |
            File.description.ilike(f"%{query}%") |
            DocumentMetadata.description.ilike(f"%{query}%")
        )

    if document_type:
        base_query = base_query.where(DocumentMetadata.document_type == document_type)

    if company:
        base_query = base_query.where(
            DocumentMetadata.company_name.ilike(f"%{company}%") |
            DocumentMetadata.client_name.ilike(f"%{company}%")
        )

    if min_amount is not None:
        base_query = base_query.where(DocumentMetadata.total_amount >= min_amount)

    if max_amount is not None:
        base_query = base_query.where(DocumentMetadata.total_amount <= max_amount)

    result = await db.execute(base_query)
    files_with_metadata = result.all()

    # Formato de respuesta similar a get_files
    return [
        {
            "id": file_row.id,
            "original_name": file_row.original_name,
            "stored_name": file_row.stored_name,
            "description": file_row.description,
            "size": file_row.size,
            "metadata": {
                "document_type": metadata_row.document_type if metadata_row else None,
                "company_name": metadata_row.company_name if metadata_row else None,
                "total_amount": metadata_row.total_amount if metadata_row else None,
                # ... otros campos
            } if metadata_row else None
        }
        for file_row, metadata_row in files_with_metadata
    ]


routes = [index, upload_file, get_files, delete_file, update_file_description, download_file, get_file_metadata, search_documents]


DEBUG_STATE = env_vars.environment == "dev"

# Inicializar servicio de Gemini al iniciar la app
def create_app() -> Litestar:
    # Inicializar Gemini con tu API key
    gemini_api_key = env_vars.gemini_api_key  # Agregar a tu config
    if gemini_api_key:
        init_gemini_service(gemini_api_key)
    else:
        print("⚠️  GEMINI_API_KEY no configurada. El análisis de IA estará deshabilitado.")

    return Litestar(
        route_handlers=[static_files, *routes],
        template_config=template_config,
        plugins=[
            SQLAlchemyPlugin(config=config_db)
        ],
        debug=DEBUG_STATE,
        logging_config=logging_config,
        middleware=[AuthMiddleware]
    )


app = create_app()

# uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload