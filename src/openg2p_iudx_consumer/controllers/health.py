from openg2p_fastapi_common.controller import BaseController
from openg2p_fastapi_common.errors.http_exceptions import InternalServerError

from ..schemas.health import HealthCheckStatus
from ..services.consumer import ConsumerService


class HealthController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["health"]

        self.router.add_api_route(
            "/health",
            self.get_health,
            responses={200: {"model": HealthCheckStatus}},
            methods=["GET"],
        )

        self._consumer_service: ConsumerService = None

    @property
    def consumer_service(self):
        if not self._consumer_service:
            self._consumer_service = ConsumerService.get_component()
        return self._consumer_service

    async def get_health(self):
        if not self.consumer_service.is_running():
            raise InternalServerError(code="G2P-IUDX-500", message="Consumer Thread is not active.")
        return HealthCheckStatus(status="healthy")
