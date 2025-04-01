# ruff: noqa: E402

from fastapi import FastAPI

from .config import Settings
from .controllers.health import HealthController
from .services.amqp_helper import AMQPHelperService
from .services.consumer import ConsumerService
from .services.es_helper import ESHelperService

_config: Settings = Settings.get_config()

from openg2p_fastapi_common.app import Initializer


class Initializer(Initializer):
    def initialize(self, **kwargs):
        super().initialize()

        AMQPHelperService()
        ESHelperService()
        self.consumer_service = ConsumerService()
        HealthController().post_init()

    async def fastapi_app_startup(self, app: FastAPI):
        super().fastapi_app_startup(app)
        self.consumer_service.check_and_run_init()

    async def fastapi_app_shutdown(self, app: FastAPI):
        super().fastapi_app_shutdown(app)
        self.consumer_service.do_run_consumer = False
