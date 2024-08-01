# coding: utf-8

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class StatusModel(BaseModel):
    """Represents a response status code complemented with additional details about the response reason.
    """

    code: Optional[int] = Field(title="response code", description="the response status code", default=None, example=409)
    message: Optional[str] = Field(title="response message", description="the response message with details", default=None, example="Level not found")


StatusModel.update_forward_refs()
