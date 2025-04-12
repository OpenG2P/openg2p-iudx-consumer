from urllib.parse import quote_plus

from openg2p_fastapi_common.config import Settings as BaseSettings
from pydantic import model_validator
from pydantic_settings import SettingsConfigDict

from . import __version__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="iudx_consumer_", env_file=".env", extra="allow")

    openapi_title: str = "OpenG2P IUDX Consumer"
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
    amqp_vhost: str = "IUDX"

    amqp_url: str = ""

    es_url: str = "http://localhost:9200"
    es_username: str = ""
    es_password: str = ""
    es_ssl_verify: bool = False
    es_timeout_secs: int = 10
    es_index_for_reg: str = "social-registry"

    # consumer_id: str = "" # Not Required in code
    consumer_client_id: str = ""
    consumer_client_secret: str = ""
    resource_queue_names: list[str] = []
    resource_ids: list[str] = []
    resource_program_names: list[str] = []
    token_api_url: str = "https://aaa.dev.openg2p.org/auth/v1/token"
    attr_search_api_url: str = "https://rs.dev.openg2p.org/ngsi-ld/v1/entities"
    attr_search_api_timeout: int = 10

    enable_snapshot: bool = True
    enable_subscribe: bool = True
    unique_id_field: str = "srID"
    persist_config_index: str = ".iudx-consumer-config"
    persist_config_doc_id: int = 1

    ui_path_prefix: str = ""
    openapi_common_api_prefix: str = "/api"

    template_folder_path: str = "templates"
    template_name_home: str = "home.html"
    template_name_about: str = "about.html"
    template_name_error: str = "error.html"

    static_folder_path: str = "static"

    @model_validator(mode="after")
    def fix_fields_model_validator(self):
        if not self.amqp_url:
            url = f"{quote_plus(self.amqp_driver)}://"
            if self.amqp_username:
                url += quote_plus(self.amqp_username)
                if self.amqp_password:
                    url += ":" + quote_plus(self.amqp_password)
                url += "@"
            url += f"{quote_plus(self.amqp_host)}:{self.amqp_port}"
            if self.amqp_vhost:
                url += f"/{quote_plus(self.amqp_vhost)}"
            self.amqp_url = url
        self.es_url = self.es_url.removesuffix("/")
        self.ui_path_prefix = self.ui_path_prefix.removesuffix("/")
        if self.enable_subscribe:
            assert len(self.resource_queue_names) == len(self.resource_ids)
        return self
