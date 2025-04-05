from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class AnyData(BaseModel):
    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def validator_model(cls, data: Any):
        if isinstance(data, dict):
            for key in data:
                if isinstance(data[key], dict):
                    data[key] = cls.model_validate(data[key])
        return data

    def get(self, name: str, default=None):
        if hasattr(self, name):
            return getattr(self, name)
        return default
