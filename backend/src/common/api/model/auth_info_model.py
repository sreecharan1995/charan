# coding: utf-8

from __future__ import annotations
from pydantic import BaseModel, Field


class AuthInfoModel(BaseModel):
    """The auth information represents data needed for clients to be able to authenticate."""

    client_id: str = Field(default="", title="the client id", example="any string")
    tenant_id: str = Field(default="", title="the tenant id", example="any string")


AuthInfoModel.update_forward_refs()
