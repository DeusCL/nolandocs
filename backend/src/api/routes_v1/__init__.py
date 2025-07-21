""" Exportar todos los routes.

¿Qué hacen los routes?
1. Reciben la solicitud HTTP.
2. Validan datos con Pydantic (schemas/)
3. Llaman a casos de uso (ubicados en application/), nunca directamente a infrastructure
4. Devuelven respuesta HTTP

--> Éxito en tu aventura pequeño programmer <--

"""

from .health import health_check
from .auth import AuthController

routes = [health_check, AuthController]

