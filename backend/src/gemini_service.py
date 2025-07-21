# services/gemini_service.py
import google.generativeai as genai
import json
from pathlib import Path
from typing import Optional
import logging
from PIL import Image
import PyPDF2
import io
import mimetypes

from src.infrastructure.db.models.enums import AIMetadataResponse, DocumentType

logger = logging.getLogger(__name__)

class GeminiDocumentAnalyzer:
    def __init__(self, api_key: str):
        """Inicializa el analizador de documentos con Gemini"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    async def analyze_document(self, file_path: str, original_filename: str) -> Optional[AIMetadataResponse]:
        """
        Analiza un documento usando Gemini y retorna metadatos estructurados
        """
        try:
            file_path = Path(file_path)

            # Determinar tipo de archivo
            mime_type, _ = mimetypes.guess_type(original_filename)

            # Extraer contenido según el tipo de archivo
            if mime_type and mime_type.startswith('image/'):
                content = await self._analyze_image(file_path)
            elif mime_type == 'application/pdf':
                content = await self._analyze_pdf(file_path)
            else:
                # Intentar como texto plano
                content = await self._analyze_text_file(file_path)

            return content

        except Exception as e:
            logger.error(f"Error analizando documento {original_filename}: {str(e)}")
            return None

    async def _analyze_image(self, file_path: Path) -> Optional[AIMetadataResponse]:
        """Analiza una imagen usando Gemini Vision"""
        try:
            # Cargar imagen
            image = Image.open(file_path)

            prompt = self._get_analysis_prompt()

            response = self.model.generate_content([prompt, image])

            # Parsear respuesta JSON
            return self._parse_ai_response(response.text)

        except Exception as e:
            logger.error(f"Error analizando imagen: {str(e)}")
            return None

    async def _analyze_pdf(self, file_path: Path) -> Optional[AIMetadataResponse]:
        """Analiza un PDF extrayendo texto y analizándolo"""
        try:
            # Extraer texto del PDF
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"

            if not text.strip():
                # Si no hay texto, intentar como imagen (PDF escaneado)
                return await self._analyze_scanned_pdf(file_path)

            prompt = self._get_analysis_prompt()
            full_prompt = f"{prompt}\n\nTexto del documento:\n{text}"

            response = self.model.generate_content(full_prompt)
            return self._parse_ai_response(response.text)

        except Exception as e:
            logger.error(f"Error analizando PDF: {str(e)}")
            return None

    async def _analyze_scanned_pdf(self, file_path: Path) -> Optional[AIMetadataResponse]:
        """Analiza un PDF escaneado usando Gemini"""
        try:
            # Para PDFs escaneados, convertir a imagen y analizar
            # Esto requiere pdf2image: pip install pdf2image
            from pdf2image import convert_from_path

            images = convert_from_path(file_path, first_page=1, last_page=1)
            if images:
                # Analizar solo la primera página
                prompt = self._get_analysis_prompt()
                response = self.model.generate_content([prompt, images[0]])
                return self._parse_ai_response(response.text)

        except ImportError:
            logger.warning("pdf2image no instalado. No se puede procesar PDF escaneado")
        except Exception as e:
            logger.error(f"Error analizando PDF escaneado: {str(e)}")

        return None

    async def _analyze_text_file(self, file_path: Path) -> Optional[AIMetadataResponse]:
        """Analiza un archivo de texto plano"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()

            prompt = self._get_analysis_prompt()
            full_prompt = f"{prompt}\n\nContenido del documento:\n{text}"

            response = self.model.generate_content(full_prompt)
            return self._parse_ai_response(response.text)

        except Exception as e:
            logger.error(f"Error analizando archivo de texto: {str(e)}")
            return None

    def _get_analysis_prompt(self) -> str:
        """Genera el prompt para el análisis de documentos contables"""

        document_types = [dt.value for dt in DocumentType]

        return f"""
Analiza este documento contable/financiero chileno y extrae la información relevante.
Responde ÚNICAMENTE con un JSON válido que siga exactamente esta estructura:

{{
    "document_type": "uno de: {', '.join(document_types)}",
    "confidence_score": 0.95,
    "document_number": "número del documento si existe, null si no",
    "document_date": "fecha en formato YYYY-MM-DD si existe, null si no",
    "due_date": "fecha de vencimiento en formato YYYY-MM-DD si existe, null si no",
    "issuer": {{
        "name": "nombre empresa emisora o null",
        "rut": "RUT sin puntos ni guión si existe o null",
        "address": "dirección si existe o null"
    }},
    "client": {{
        "name": "nombre cliente/receptor o null",
        "rut": "RUT sin puntos ni guión si existe o null",
        "address": "dirección si existe o null"
    }},
    "amounts": {{
        "total": 150000.0,
        "net": 126050.0,
        "tax": 23950.0,
        "other_taxes": 0.0
    }},
    "currency": "CLP",
    "description": "descripción clara del contenido y propósito del documento",
    "tags": ["tag1", "tag2", "tag3"],
    "accounting_period": "YYYY-MM del período contable si aplica o null",
    "account_codes": ["cuenta1", "cuenta2"],
    "requires_review": false,
    "extracted_text": "texto principal extraído",
    "key_data": {{}}
}}

INSTRUCCIONES ESPECÍFICAS:
- Si no puedes identificar un campo, usa null (no string "null", sino null JSON)
- Para document_type, elige el más apropiado de la lista, si no estás seguro usa "otros"
- Para tags, incluye palabras clave relevantes para búsqueda (mínimo 1 tag)
- Para amounts, si no hay montos visibles, usa null para cada campo
- Para RUTs, extrae solo números y dígito verificador (ej: 12345678K)
- confidence_score debe reflejar qué tan seguro estás de la clasificación
- requires_review = true si hay información ambigua o faltante importante
- description nunca debe ser null, siempre describe lo que ves
- extracted_text nunca debe ser null, extrae cualquier texto visible
- Responde SOLO el JSON, sin texto adicional
"""

    def _parse_ai_response(self, response_text: str) -> Optional[AIMetadataResponse]:
        """Parsea la respuesta de texto del AI a un objeto AIMetadataResponse"""
        try:
            # Limpiar respuesta para extraer solo el JSON
            response_text = response_text.strip()

            # Buscar JSON en la respuesta
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                logger.error("No se encontró JSON válido en la respuesta del AI")
                return None

            json_text = response_text[start_idx:end_idx]

            # Parsear JSON
            data = json.loads(json_text)

            # Crear objeto AIMetadataResponse
            return AIMetadataResponse(**data)

        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON de AI: {str(e)}")
            logger.error(f"Respuesta recibida: {response_text}")
            return None
        except Exception as e:
            logger.error(f"Error procesando respuesta de AI: {str(e)}")
            return None

# Instancia global del analizador (inicializar con tu API key)
gemini_analyzer = None

def init_gemini_service(api_key: str):
    """Inicializa el servicio de Gemini con la API key"""
    global gemini_analyzer
    gemini_analyzer = GeminiDocumentAnalyzer(api_key)

def get_gemini_analyzer() -> Optional[GeminiDocumentAnalyzer]:
    """Obtiene la instancia del analizador de Gemini"""
    return gemini_analyzer