import logging
import traceback

from fastapi import Request
from fastapi.responses import HTMLResponse
from openg2p_fastapi_common.errors import BaseAppException
from openg2p_fastapi_common.exception import BaseExceptionHandler

from .config import Settings
from .schemas.any_data import AnyData
from .services.template_renderer import TemplateRendererService

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class ExceptionHandlerForUi(BaseExceptionHandler):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tmpl_renderer: TemplateRendererService = None

    @property
    def tmpl_renderer(self):
        if not self._tmpl_renderer:
            self._tmpl_renderer = TemplateRendererService.get_component()
        return self._tmpl_renderer

    async def base_exception_handler(self, request: Request, exc: BaseAppException):
        if request.url.path.startswith(_config.openapi_common_api_prefix):
            return await super().base_exception_handler(request, exc)
        _logger.exception(f"Received Exception: {exc}")
        return HTMLResponse(
            content=self.tmpl_renderer.render_template(
                _config.template_name_error,
                input=AnyData(
                    code=exc.code,
                    message=exc.message,
                    stack_trace=traceback.format_exception(exc),
                    status_code=exc.status_code,
                ),
            ),
            status_code=exc.status_code,
            headers=exc.headers,
        )

    async def unknown_exception_handler(self, request: Request, exc: Exception):
        if request.url.path.startswith(_config.openapi_common_api_prefix):
            return await super().unknown_exception_handler(request, exc)
        _logger.exception("Received Unknown Exception: %s", repr(exc))
        exc_split = str(exc).split("::")
        if len(exc_split) > 1:
            code = exc_split[0]
            message = exc_split[1]
        else:
            code = "G2P-REQ-100"
            message = exc_split[0]
        return HTMLResponse(
            content=self.tmpl_renderer.render_template(
                _config.template_name_error,
                input=AnyData(
                    code=code,
                    message=message,
                    stack_trace=traceback.format_exception(exc),
                    status_code=500,
                ),
            ),
            status_code=500,
        )
