# coding: utf-8

from typing import Any
from fastapi.testclient import TestClient

import json

HEADERS = {
    "Authorization": "Bearer DISABLED",
    "Content-Type": "application/json"
}


def test_get_package(client: TestClient):
    """Test case for get_package

    Gets a specific package
    """

    response = client.get(
        "/packages/{package_name}".format(package_name='fastapi'),
        headers=HEADERS,
    )

    # uncomment below to assert the status code of the HTTP response
    assert response.status_code == 200
    assert response.json()['name'] == "fastapi"


def test_list_packages(client: TestClient):
    """Test case for list_packages

    Gets the list of packages available
    """
    response = client.get(
        "/packages",
        headers=HEADERS,
    )

    assert response.status_code == 200

    data: Any = json.loads(response.content)

    assert data["navigation"]["items"] > 0
    assert len(data["items"]) > 0
