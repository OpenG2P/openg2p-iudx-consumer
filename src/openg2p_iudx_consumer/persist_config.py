import logging
from contextvars import ContextVar

from pydantic import BaseModel, ConfigDict

from .config import Settings
from .services.es_helper import ESHelperService

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)

persist_config_registry: ContextVar["PersistentConfig"] = ContextVar("persist_config_registry", default=None)


class PersistentConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    snapshot_saved: bool = False

    @classmethod
    def retrieve(cls):
        if persist_config_registry.get():
            return persist_config_registry.get()
        es_helper: ESHelperService = ESHelperService.get_component()
        config = PersistentConfig.model_validate(
            es_helper.get_by_id(_config.persist_config_doc_id, index=_config.persist_config_index)
        )
        config._es_helper = es_helper
        persist_config_registry.set(config)
        return config

    def save(self):
        if not hasattr(self, "_es_helper"):
            self._es_helper: ESHelperService = ESHelperService.get_component()
        self._es_helper.put_by_id(
            self.model_dump(mode="json"), _config.persist_config_doc_id, index=_config.persist_config_index
        )
        return self
