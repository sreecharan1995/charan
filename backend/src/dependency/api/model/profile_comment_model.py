# coding: utf-8

from __future__ import annotations

from pydantic import BaseModel, validator


class ProfileCommentModel(BaseModel):
    """Model to represent a comment included in a profile list of comments.
    """

    comment: str
    created_by: str
    created_at: str

    @validator("comment", always=True)
    def comment_is_acceptable(cls, v : str):                
        if v.strip() == '':
            raise ValueError("profile comment text is invalid")
        return v

ProfileCommentModel.update_forward_refs()
