import logging

import httpx
from openg2p_fastapi_common.service import BaseService

from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


class ESHelperService(BaseService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_by_id(self, id, index=_config.es_index_for_reg):
        auth = None
        if _config.es_username:
            auth = (_config.es_username, _config.es_password)
        res = httpx.get(
            f"{_config.es_url}/{index}/_doc/{id}",
            auth=auth,
            timeout=_config.es_timeout_secs,
            verify=_config.es_ssl_verify,
        )
        res.raise_for_status()
        res = res.json()
        return res.get("_source", {})

    def put_by_id(self, body: dict, id, index=_config.es_index_for_reg):
        auth = None
        if _config.es_username:
            auth = (_config.es_username, _config.es_password)
        res = httpx.put(
            f"{_config.es_url}/{index}/_doc/{id}",
            auth=auth,
            timeout=_config.es_timeout_secs,
            verify=_config.es_ssl_verify,
            json=body,
        )
        res.raise_for_status()
