import logging

from openg2p_fastapi_common.controller import BaseController

from ..config import Settings
from ..schemas.query import QueryAPIRequest, QueryAPIResponse
from ..services.consumer import ConsumerService

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class QueryAPIController(BaseController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.router.tags += ["search-query"]

        self.router.add_api_route(
            "/query",
            self.post_query,
            responses={200: {"model": QueryAPIResponse}},
            methods=["POST"],
        )

        self._consumer_service: ConsumerService = None

    @property
    def consumer_service(self):
        if not self._consumer_service:
            self._consumer_service = ConsumerService.get_component()
        return self._consumer_service

    async def post_query(self, request: QueryAPIRequest):
        res = self.consumer_service.attr_search_iudx(
            request.resource_id,
            ",".join([f"{key}=={value}" for key, value in request.query.model_dump(mode="json").items()]),
            raise_for_status=False,
        )
        if not res:
            return QueryAPIResponse()
        elif isinstance(res, list):
            return QueryAPIResponse.model_validate({"result": res})
        else:
            return QueryAPIResponse.model_validate({"error": res})
