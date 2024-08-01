# coding: utf-8

import json
from types import SimpleNamespace
from typing import List, Any

from fastapi.testclient import TestClient

from common.domain.site import Site
from level.api.model.site_model import SiteModel


def test_list_sites(test_tables: None, client: TestClient):
    """Test case for list_sites

    Gets the list of sites available
    """

    headers = {
    }

    response = client.get(
        "/sites",
        headers=headers,
    )

    assert response.status_code == 200

    r: Any = json.loads(response.content, object_hook=lambda d: SimpleNamespace(**d))

    site_list: List[Site] = Site.list()

    assert len(r) == len(site_list)

    for x in r:
        site : List[SiteModel] = list( filter( lambda s: s.value == x.name , site_list) )
        assert len( site ) == 1

    assert True
