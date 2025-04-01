from urllib.parse import quote_plus

from openg2p_fastapi_common.config import Settings
from pydantic import model_validator
from pydantic_settings import SettingsConfigDict

from . import __version__


class Settings(Settings):
    model_config = SettingsConfigDict(env_prefix="iudx_consumer_", env_file=".env", extra="allow")

    openapi_title: str = "IUDX Consumer"
    openapi_description: str = """
    IUDX Consumer
    ***********************************
    Further details goes here
    ***********************************
    """
    openapi_version: str = __version__

    amqp_driver: str = "amqp"
    amqp_host: str = "localhost"
    amqp_port: int = 5672
    amqp_username: str = ""
    amqp_password: str = ""
    amqp_queue: str = ""
    amqp_vhost: str = "IUDX"

    amqp_url: str = ""

    attr_search_api_url: str = "https://rs.dev.openg2p.org/rs/api/v1/search"
    attr_search_api_timeout: int = 10

    es_url: str = "http://localhost:9200"
    es_username: str = ""
    es_password: str = ""
    es_ssl_verify: bool = False
    es_timeout_secs: int = 10
    es_index_for_reg: str = "registry"
    dashboard_url: str = "http://localhost:5601/dashboard"

    enable_snapshot: bool = True
    unique_id_field: str = "srID"
    persist_config_index: str = ".iudx-consumer-config"
    persist_config_doc_id: int = 1

    @model_validator(mode="after")
    def fix_fields_model_validator(self):
        if not self.amqp_url:
            url = f"{quote_plus(self.amqp_driver)}://"
            if self.amqp_username:
                url += quote_plus(self.amqp_username)
                if self.amqp_password:
                    url += ":" + quote_plus(self.amqp_password)
                url += "@"
            url += f"{quote_plus(self.amqp_host)}:{quote_plus(self.amqp_port)}"
            if self.amqp_vhost:
                url += f"/{quote_plus(self.amqp_vhost)}"
            self.amqp_url = url
        self.amqp_url = self.amqp_url.removesuffix("/")
        self.attr_search_api_url = self.attr_search_api_url.removesuffix("/")
        self.es_url = self.es_url.removesuffix("/")
        self.dashboard_url = self.dashboard_url.removesuffix("/")
        return self
