import logging
from datetime import datetime, timezone

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
        if res.status_code == 404:
            return {}
        res.raise_for_status()
        res = res.json()
        return res.get("_source", {})

    def put_by_id(self, body: dict, id, index=_config.es_index_for_reg, insert_times=True):
        auth = None
        if _config.es_username:
            auth = (_config.es_username, _config.es_password)
        now = self.get_curr_timestamp()
        res = httpx.post(
            f"{_config.es_url}/{index}/_update/{id}",
            auth=auth,
            timeout=_config.es_timeout_secs,
            verify=_config.es_ssl_verify,
            json={
                "doc": {"updated_at": now, "@timestamp": now, **body},
                "upsert": {"created_at": now, "updated_at": None, "@timestamp": now, **body},
            },
        )
        res.raise_for_status()

    def get_curr_timestamp(self) -> str:
        now = datetime.now().astimezone(tz=timezone.utc).replace(tzinfo=None)
        now = now.isoformat(timespec="milliseconds") + "Z"
        return now
