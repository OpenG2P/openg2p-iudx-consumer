import logging

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
        unq_id = self.get_unique_id_of_rec(rec)
        self.es_helper_service.put_by_id(rec, unq_id)
        channel.basic_ack(delivery_tag=method.delivery_tag)

    def check_and_run_init(self):
        persist_config = PersistentConfig.retrieve()
        if _config.enable_snapshot and not persist_config.snapshot_saved:
            self.do_snapshot()
            persist_config.snapshot_saved = True
            persist_config.save()
        self.consumer_thread.start()

    def get_full_data_from_api(self) -> list[dict]:
        final_res = []
        for resource_id in _config.resource_ids:
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
                _logger.exception("Exception while receiving token for DX Attribute Search.", res.text)
                raise
            token = res.json()["results"]["accessToken"]
            res = httpx.get(
                _config.attr_search_api_url,
                timeout=_config.attr_search_api_timeout,
                params={
                    "q": f"id=={resource_id}",
                    "id": resource_id,
                },
                headers={
                    "token": token,
                    "accept": "application/json",
                },
            )
            _logger.debug("Data received from Attr Search APIs. %s", res.text)
            try:
                res.raise_for_status()
            except Exception:
                _logger.exception("Exception during DX Attribute Search.", res.text)
                raise
            if res.status_code != 204:
                final_res += res.json().get("results", [])
        _logger.info("Total Count of data received from Attr search APIs: %s", len(final_res))
        return final_res

    def do_snapshot(self):
        res = self.get_full_data_from_api()
        for rec in res:
            unq_id = self.get_unique_id_of_rec(rec)
            self.es_helper_service.put_by_id(rec, unq_id)

    def get_unique_id_of_rec(self, rec: dict) -> str:
        return rec.get(_config.unique_id_field, None)
