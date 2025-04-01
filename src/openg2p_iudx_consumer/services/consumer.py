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
        self.amqp_helper_service.configure(_config.amqp_url, _config.amqp_queue, self.on_message_callback)
        while self.do_run_consumer:
            self.amqp_helper_service.consume_pending_messages()
        self.amqp_helper_service.stop_consuming_and_close()

    def on_message_callback(
        self, channel: BlockingChannel, method: Method, properties: BasicProperties, body: bytes
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
        res = httpx.get(
            _config.attr_search_api_url,
            timeout=_config.attr_search_api_timeout,
        )
        res.raise_for_status()
        res = res.json().get("response", [])

    def do_snapshot(self):
        res = self.get_full_data_from_api()
        for rec in res:
            unq_id = self.get_unique_id_of_rec(rec)
            self.es_helper_service.put_by_id(rec, unq_id)

    def get_unique_id_of_rec(self, rec: dict) -> str:
        return rec.get(_config.unique_id_field, None)
