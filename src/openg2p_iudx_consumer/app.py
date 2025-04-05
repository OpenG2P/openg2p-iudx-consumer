# ruff: noqa: E402

from fastapi import FastAPI

from .config import Settings

_config: Settings = Settings.get_config()

from openg2p_fastapi_common.app import Initializer

from .controllers.health import HealthController
from .controllers.static import StaticController
from .controllers.ui import UIController
from .exception_handler import ExceptionHandlerForUi
from .services.amqp_helper import AMQPHelperService
from .services.consumer import ConsumerService
from .services.es_helper import ESHelperService
from .services.template_renderer import TemplateRendererService


class Initializer(Initializer):
    def initialize(self, **kwargs):
        super().initialize()

        AMQPHelperService()
        ESHelperService()
        self.tmpl_service = TemplateRendererService()
        self.consumer_service = ConsumerService()
        HealthController().post_init()
        UIController().post_init()
        StaticController().post_init()
        ExceptionHandlerForUi()

    async def fastapi_app_startup(self, app: FastAPI):
        await super().fastapi_app_startup(app)
        self.tmpl_service.check_if_templates_exist()
        self.consumer_service.check_and_run_init()

    async def fastapi_app_shutdown(self, app: FastAPI):
        await super().fastapi_app_shutdown(app)
        self.consumer_service.do_run_consumer = False
