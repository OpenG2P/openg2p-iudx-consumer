import logging
from datetime import datetime

import httpx
import orjson
from openg2p_fastapi_common.service import BaseService
from openg2p_fastapi_common.utils.ctx_thread import CTXThread

from ..config import Settings
from ..persist_config import PersistentConfig
from .amqp_helper import AMQPHelperService, BasicProperties, BlockingChannel, Method
from .es_helper import ESHelperService

_config: Settings = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class ConsumerService(BaseService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.do_run_consumer = True
        self.consumer_thread = CTXThread(target=self.run_consumer_thread)

        self._amqp_helper_service: AMQPHelperService = None
        self._es_helper_service: ESHelperService = None

        self.resource_tokens: dict[str, str] = {}
        self.resource_tokens_expires_at: dict[str, datetime] = {}

    @property
    def amqp_helper_service(self):
        if not self._amqp_helper_service:
            self._amqp_helper_service = AMQPHelperService.get_component()
        return self._amqp_helper_service

    @property
    def es_helper_service(self):
        if not self._es_helper_service:
            self._es_helper_service = ESHelperService.get_component()
        return self._es_helper_service

    def is_running(self) -> bool:
        return self.consumer_thread.is_alive()

    def run_consumer_thread(self):
        self.amqp_helper_service.configure(
            _config.amqp_url, _config.resource_queue_names, self.on_message_callback
        )
        while self.do_run_consumer:
            self.amqp_helper_service.consume_pending_messages()
        self.amqp_helper_service.stop_consuming_and_close()

    def on_message_callback(
        self, queue: str, channel: BlockingChannel, method: Method, properties: BasicProperties, body: bytes
    ):
        """
        This will be called on the same thread that calls amqp_helper.configure()
        and amqp_helper.consume_pending_messages().
        """
        rec = orjson.loads(body.decode())
        self.process_record(rec)
        unq_id = self.get_unique_id_of_rec(rec)
        self.es_helper_service.put_by_id(rec, unq_id)
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def check_and_run_init(self):
        persist_config = PersistentConfig.retrieve()
        if _config.enable_snapshot and not persist_config.snapshot_saved:
            self.do_snapshot()
            persist_config.snapshot_saved = True
            persist_config.save()
        if _config.enable_subscribe:
            self.consumer_thread.start()

    def get_full_data_from_api(self) -> list[dict]:
        final_res = []
        for resource_id in _config.resource_ids:
            res = self.attr_search_iudx(resource_id, f"id=={resource_id}")
            if res:
                final_res += res
        for rec in final_res:
            self.process_record(rec)
        _logger.info("Total Count of data received from Attr search APIs: %s", len(final_res))
        return final_res

    def get_iudx_resource_token(self, resource_id: str, raise_for_status=True) -> str:
        if (
            resource_id in self.resource_tokens_expires_at
            and datetime.now() < self.resource_tokens_expires_at[resource_id]
        ):
            return self.resource_tokens[resource_id]
        res = httpx.post(
            _config.token_api_url,
            timeout=_config.attr_search_api_timeout,
            json={"itemId": resource_id, "itemType": "resource", "role": "consumer"},
            headers={
                "clientId": _config.consumer_client_id,
                "clientSecret": _config.consumer_client_secret,
            },
        )
        try:
            res.raise_for_status()
        except Exception:
            _logger.exception("Exception while receiving token for DX Attribute Search. %s", res.text)
            if raise_for_status:
                raise
            return res.json()
        res = res.json()["results"]
        token = res["accessToken"]
        expires_at = datetime.fromtimestamp(res["expiry"])
        self.resource_tokens[resource_id] = token
        self.resource_tokens_expires_at[resource_id] = expires_at
        return token

    def attr_search_iudx(self, resource_id: str, query: str, raise_for_status=True) -> list | None:
        token_res = self.get_iudx_resource_token(resource_id, raise_for_status=raise_for_status)
        if isinstance(token_res, dict):
            return token_res
        res = httpx.get(
            _config.attr_search_api_url,
            timeout=_config.attr_search_api_timeout,
            params={
                "q": query,
                "id": resource_id,
            },
            headers={
                "token": token_res,
                "accept": "application/json",
            },
        )
        _logger.debug("Data received from Attr Search APIs. %s", res.text)
        if res.status_code == 204:
            return []
        try:
            res.raise_for_status()
        except Exception:
            _logger.exception("Exception during DX Attribute Search. %s", res.text)
            if raise_for_status:
                raise
            return res.json()
        return res.json()["results"]

    def do_snapshot(self):
        res = self.get_full_data_from_api()
        for rec in res:
            unq_id = self.get_unique_id_of_rec(rec)
            self.es_helper_service.put_by_id(rec, unq_id)

    def get_unique_id_of_rec(self, rec: dict) -> str:
        return rec.get(_config.unique_id_field, None)

    def process_record(self, rec):
        if "incomeDetails" in rec:
            income: str = rec["incomeDetails"].get("income")
            hh_income: str = rec["incomeDetails"].get("total_household_income")
            income_value = float(income.removeprefix("$")) if income else None
            hh_income_value = float(hh_income.removeprefix("$")) if hh_income else None
            rec["incomeDetails"]["income_value"] = income_value
            rec["incomeDetails"]["total_household_income_value"] = hh_income_value
        if "landInfo" in rec:
            land_area: str = rec["landInfo"].get("total_land_area")
            land_area_value = float(land_area.removesuffix("acres").strip()) if land_area else None
            rec["landInfo"]["total_land_area_value"] = land_area_value
