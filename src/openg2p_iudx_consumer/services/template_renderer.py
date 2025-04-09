import base64
import logging
import os

import jinja2
import magic
from openg2p_fastapi_common.service import BaseService

from ..config import Settings
from ..schemas.any_data import AnyData

_config: Settings = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class TemplateRendererService(BaseService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.template_files_loader = jinja2.FileSystemLoader(_config.template_folder_path, followlinks=True)
        self.template_env = jinja2.Environment(
            loader=self.template_files_loader, autoescape=jinja2.select_autoescape()
        )
        self.magic_mime = magic.Magic(mime=True)

    def check_if_templates_exist(self):
        """
        Can be called on fastapi app startup.
        """
        self.template_env.get_template(_config.template_name_home)
        self.template_env.get_template(_config.template_name_about)
        self.template_env.get_template(_config.template_name_error)

    def render_template(self, template_name: str, input: AnyData = None, **kw) -> str:
        return self.template_env.get_template(template_name).render(
            renderer=self, input=input, config=_config, logger=_logger, **kw
        )

    def get_binary_template_data(self, template_name: str) -> bytes:
        bin_data = None
        with open(os.path.join(os.fspath(_config.template_folder_path), template_name), "rb") as file:
            bin_data = file.read()
        return bin_data

    def convert_bin_to_htmlsafe(self, data: bytes, mimetype: str = None):
        if not data:
            return None
        if not mimetype:
            mimetype = self.infer_mime_type_from_data(data)
        b64_data = base64.b64encode(data).decode()
        return f"data:{mimetype};base64,{b64_data}"

    def infer_mime_type_from_data(self, data: bytes | str):
        if not data:
            return None
        return self.magic_mime.from_buffer(data)

    def prefix_base_url(self, uri: str) -> str:
        return _config.ui_path_prefix + uri
