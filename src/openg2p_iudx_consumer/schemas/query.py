from pydantic import BaseModel

from .any_data import AnyData


class QueryAPIRequest(BaseModel):
    resource_id: str
    query: AnyData


class QueryAPIResponse(BaseModel):
    result: list[AnyData] = []
    error: AnyData | None = None
