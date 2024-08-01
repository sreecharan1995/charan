# coding: utf-8

from typing import Optional

from pydantic import BaseModel, Field


class NavigateModel(BaseModel):
    """Represents data regarding navigation in endpoints returning partial results in the form of pages"""

    prev: Optional[str] = Field(default=None, title="previous page", description="The url pointing to previous page, if any")
    next: Optional[str] = Field(default=None, title="next page", description="The url pointing to next page, if any")
    page: Optional[int] = Field(default=None, title="page number", description="The current page number", example=11)
    total: Optional[int] = Field(default=None, title="total items", description="The total number of listable items", example=100)
    items: Optional[int] = Field(default=None, title="items count", description="The actual number of items in the current page", example=0)
    pages: Optional[int] = Field(default=None, title="pages count", description="The total number of listable pages, for the current page size", example=10)
    pageSize: Optional[int] = Field(default=None, title="page size", description="The current page size", example=10)

NavigateModel.update_forward_refs()
    
