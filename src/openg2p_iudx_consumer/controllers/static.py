import logging

from fastapi.staticfiles import StaticFiles
from openg2p_fastapi_common.context import app_registry
from openg2p_fastapi_common.controller import BaseController

from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class StaticController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.router = None

    def post_init(self):
        app_registry.get().mount(
            _config.ui_path_prefix + "/static",
            StaticFiles(directory=_config.static_folder_path),
            name="static",
        )
        return self
