import functools
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
        self.connection: BlockingConnection = None
        self.channel: BlockingChannel = None

    def configure(
        self,
        url: str,
        queues: list[str],
        callback: Callable[[str, BlockingChannel, Method, BasicProperties, bytes], None],
    ):
        """
        Can be called only once
        """
        self.connection = BlockingConnection(URLParameters(url))
        self.check_and_create_queues(queues)
        self.channel = self.connection.channel()
        for queue in queues:
            self.channel.basic_consume(
                queue=queue, on_message_callback=functools.partial(callback, queue), auto_ack=False
            )

    def consume_pending_messages(self, time_limit=0):
        """
        This is non-blocking. Run in while loop inside thread to block execution.
        """
        self.connection.process_data_events(time_limit=time_limit)
        if self.channel.is_closed and isinstance(self.channel._closing_reason, ChannelClosed):
            raise self.channel._closing_reason

    def stop_consuming_and_close(self):
        self.channel.stop_consuming()
        self.connection.close()

    def check_and_create_queues(self, queues: list[str]):
        channel = self.connection.channel()
        for queue in queues:
            try:
                channel.queue_declare(queue=queue)
            except Exception as e:
                if isinstance(e, ChannelClosed) and e.reply_code == 403:
                    # Means Queue already declared.
                    channel = self.connection.channel()
                else:
                    raise
        channel.close()
