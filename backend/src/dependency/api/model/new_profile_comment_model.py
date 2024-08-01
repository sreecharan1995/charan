# coding: utf-8

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class NewProfileCommentModel(BaseModel):
    """Model to represent a request to create a new comment for a profile
    """

    comment: str = ''
    created_by: Optional[str] = 'system'


NewProfileCommentModel.update_forward_refs()
