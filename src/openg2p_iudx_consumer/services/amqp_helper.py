import logging
from typing import Callable

from openg2p_fastapi_common.service import BaseService
from pika import BlockingConnection, URLParameters
from pika.adapters.blocking_connection import BlockingChannel
from pika.amqp_object import Method
from pika.exceptions import ChannelClosed
from pika.spec import BasicProperties

from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class AMQPHelperService(BaseService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.channel: BlockingChannel = None
        self.queue: str = None

    def configure(
        self,
        url: str,
        queue: str,
        callback: Callable[[BlockingChannel, Method, BasicProperties, bytes], None],
    ):
        """
        Can be called only once
        """
        self.queue = queue
        self.channel = BlockingConnection(URLParameters(url)).channel()

        self.channel.queue_declare(queue=self.queue)
        self.channel.basic_consume(queue=self.queue, on_message_callback=callback, auto_ack=False)

    def consume_pending_messages(self, time_limit=0):
        """
        This is non-blocking. Run in while loop inside thread to block execution.
        """
        self.channel.connection.process_data_events(time_limit=time_limit)
        if self.channel.is_closed and isinstance(self.channel._closing_reason, ChannelClosed):
            raise self.channel._closing_reason

    def stop_consuming_and_close(self):
        self.channel.stop_consuming()
        self.channel.connection.close()
