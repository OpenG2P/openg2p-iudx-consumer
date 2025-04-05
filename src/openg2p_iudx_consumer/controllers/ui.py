import logging

from fastapi.responses import HTMLResponse
from openg2p_fastapi_common.controller import BaseController

from ..config import Settings
from ..services.template_renderer import TemplateRendererService

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class UIController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["ui"]
        self.router.responses = {}
        self.router.redirect_slashes = True
        self.router.include_in_schema = False
        self.router.prefix = _config.ui_path_prefix

        self.router.add_api_route("/dashboard", self.get_dashboard, methods=["GET"])

        self.router.add_api_route("/about", self.get_about, methods=["GET"])

        self._tmpl_renderer: TemplateRendererService = None

    @property
    def tmpl_renderer(self):
        if not self._tmpl_renderer:
            self._tmpl_renderer = TemplateRendererService.get_component()
        return self._tmpl_renderer

    def get_dashboard(self):
        return HTMLResponse(content=self.tmpl_renderer.render_template(_config.template_name_dashboard))

    def get_about(self):
        return HTMLResponse(content=self.tmpl_renderer.render_template(_config.template_name_about))
