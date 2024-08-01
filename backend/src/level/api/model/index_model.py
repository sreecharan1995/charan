## coding: utf-8

from __future__ import annotations

from typing import Optional

from fastapi import Request
from pydantic import BaseModel

from common.api.utils import Utils


class IndexModel(BaseModel):
    """Model to represent an index of available resources
    """

    base_url: Optional[str] = None

    @staticmethod
    def build(req: Request):
        url_base = Utils.base_url(req)
        return IndexModel(base_url=url_base)


IndexModel.update_forward_refs()
