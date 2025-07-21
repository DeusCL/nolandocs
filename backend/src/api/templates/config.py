from litestar.template.config import TemplateConfig
from litestar.contrib.jinja import JinjaTemplateEngine

from src.api.templates.callables import static_version
from src.core.config.constants import ROOT_PATH



def configure_template_engine(engine: JinjaTemplateEngine) -> None:
    # Callables disponibles en templates
    engine.register_template_callable("static_version", static_version)


template_config = TemplateConfig(
    directory=ROOT_PATH / "templates",
    engine=JinjaTemplateEngine,
    engine_callback=configure_template_engine,
)
