# coding: utf-8

from typing import Generic, List, Optional, TypeVar

from fastapi import Request
from pydantic import Field
from pydantic.generics import GenericModel

from common.api.model.navigate_model import NavigateModel
from common.api.utils import Utils

T = TypeVar('T')


class PageModel(GenericModel, Generic[T]):
    """Represents a single page of results, containing items and navigational data"""

    navigation: Optional[NavigateModel] = Field(default=None, title="navigation data",
                                                description="The data for page navigation")
    items: List[T] = Field(default=[], title="list of items", description="The list of items in the page")

    @staticmethod
    def build(req: Request, items: List[T], total: Optional[int], p: int, ps: int, q: Optional[str], items_pre_paged: bool = True):

        page = PageModel[T]()
        navigation = NavigateModel()

        common = ""
        if ps is not None:
            common += "&ps=" + str(ps)
        if q is not None:
            common += "&q=" + q

        urlBase = Utils.base_url(req)

        count = len(items)

        if total is not None and ps is not None:
            pages = -1 * (-total // ps)
        else:
            pages = None

        if p is None:
            p = 1

        if p > 1:
            if count != 0:
                navigation.prev = urlBase + "?p=" + str(p - 1) + common
            elif total != 0 and pages is not None:
                navigation.prev = urlBase + "?p=" + str(pages) + common

        if total is None or (ps is not None and (p * ps < total)):
            navigation.next = urlBase + "?p=" + str(p + 1) + common

        if total is not None:
            navigation.total = total

        navigation.items = count
        navigation.page = p
        navigation.pageSize = ps

        if pages is not None:
            navigation.pages = pages

        if not items_pre_paged:
            page_start_pos: int = (p-1) * ps
            page_end_pos: int = page_start_pos + ps if page_start_pos + ps - 1 < len(items) - 1 else len(items)
            items = items[page_start_pos:page_end_pos]
            navigation.items = len(items)

        page.items = items
        page.navigation = navigation

        return page


PageModel.update_forward_refs()
