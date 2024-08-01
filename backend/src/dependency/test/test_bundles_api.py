# coding: utf-8

import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

from common.utils import Utils
from dependency.dependency_settings import DependencySettings
from dependency.service.bundle_service import BundleService

settings = DependencySettings.load()

bundle_service = BundleService()

HEADERS = { "Authorization": "Bearer DISABLED", "Content-Type": "application/json"}

def test_get_missing_bundle(test_tables : None, client: TestClient):
    """Test case for getting a bundle that does not exist"""

    random = Utils.randomword(5)

    response = client.get(
        f"/bundles/bundle_{random}",
        headers=HEADERS,
    )

    assert response.status_code == 404


def test_create_bundle(test_tables : None, client: TestClient):
    """Test case for creating a bundle (add bundle to library)"""

    random = Utils.randomword(5)

    bundle_name = "bundle_" + random

    b_response = client.post(
        "/bundles",
        headers=HEADERS,
        json={
            "name": bundle_name,
            "packages": [
                {"name": "anyio", "version": "3.5.0", "use_legacy": False},
                {"name": "alabaster", "version": "0.7.17", "use_legacy": True},
                {"name": "fastapi", "version": "0.75.1"},
            ],
        },
    )

    assert b_response.status_code == 201

    g_response = client.get(
        f"/bundles/{bundle_name}",
        headers=HEADERS,
    )

    assert g_response.status_code == 200

    g = json.loads(g_response.content, object_hook=lambda d: SimpleNamespace(**d))

    assert g.name == bundle_name
    assert len(g.packages) == 3
    assert g.packages[0].name == "anyio"
    assert g.packages[0].version == "3.5.0"
    assert g.packages[0].use_legacy == False
    assert g.packages[1].name == "alabaster"
    assert g.packages[1].version == "0.7.17"
    assert g.packages[1].use_legacy == True
    assert g.packages[2].name == "fastapi"
    assert g.packages[2].version == "0.75.1"
    assert g.packages[2].use_legacy == False

    b2_response = client.post(
        "/bundles",
        headers=HEADERS,
        json={
            "name": bundle_name,
            "packages": [
                {"name": "sphinx", "version": "4.5.0"},
                {"name": "anyio", "version": "3.5.0"},
            ],
        },
    )

    assert b2_response.status_code == 409

    b2 = json.loads(b2_response.content, object_hook=lambda d: SimpleNamespace(**d))

    assert b2.detail == "There is already a bundle using the same name"


def test_create_bundle_reused_name_after_delete(test_tables : None, client: TestClient):
    """Test case for creating a bundle (add bundle to library), deleting it and the create another one reusing the name"""

    random = Utils.randomword(5)

    bundle_name = "bundle_" + random

    b_response = client.post(
        "/bundles",
        headers=HEADERS,
        json={
            "name": bundle_name,
            "packages": [
                {"name": "anyio", "version": "3.5.0", "use_legacy": False},
                {"name": "alabaster", "version": "0.7.17", "use_legacy": True},
                {"name": "fastapi", "version": "0.75.1"},
            ],
        },
    )

    assert b_response.status_code == 201

    d_response = client.delete(f"/bundles/{bundle_name}", headers=HEADERS)

    assert d_response.status_code == 204

    b2_response = client.post(
        "/bundles",
        headers=HEADERS,
        json={
            "name": bundle_name,
            "packages": [
                {"name": "sphinx", "version": "4.5.0", "use_legacy": True},
                {"name": "anyio", "version": "3.5.0", "use_legacy": False},
            ],
        },
    )

    assert b2_response.status_code == 201

    b2 = json.loads(b2_response.content, object_hook=lambda d: SimpleNamespace(**d))

    assert b2.name == bundle_name
    assert len(b2.packages) == 2
    assert b2.packages[0].name == "sphinx"
    assert b2.packages[0].version == "4.5.0"
    assert b2.packages[0].use_legacy == True


def test_create_invalid_bundle(test_tables : None, client: TestClient):

    invalid_bundles = [ # type: ignore
        {  # test for missing bundle name
            "packages": [
                {"name": "somehting", "version": "1.1.1"},
                {"name": "else", "version": ""},
            ]
        },
        {
            "name": "a b",  # test for invalid name
            "packages": [
                {"name": "somehting", "version": "1.1.1"},
                {"name": "else", "version": ""},
            ],
        },
        {
            "name": "a_b",
            # test for invalid packages list
            "packages": 10,
        },
        {
            "name": "abc",
            "packages": [
                {"version": "1.1.1"},  # test for invalid package with no name
                {"name": "else", "version": ""},
            ],
        },
        {
            "name": "abcd",
            "packages": [
                {"name": "invalid*name"},  # test for invalid package name
                {"name": "else", "version": ""},
            ],
        },
        {
            "name": "no-packs",
            "packages": [], # test for empty package list
        },
        {
            "name": "missing-packs"
        },
    ]

    for b in invalid_bundles: # type: ignore
        i_response = client.post("/bundles", headers=HEADERS, json=b) # type: ignore
        assert (
            i_response.status_code == 422
        ), "profile bundle should not be accepted: " + str(b) # type: ignore

    assert True

def test_list_bundles(test_tables : None, client: TestClient):
    """Test case for list_bundles

    Gets the list of bundles available
    """

    random = Utils.randomword(5)

    bundle_name = "bundle_" + random

    b_response = client.post(
        "/bundles",
        headers=HEADERS,
        json={
            "name": bundle_name,
            "packages": [{"name": "fastapi", "version": "0.73", "use_legacy": True}],
        },
    )

    assert b_response.status_code == 201

    response = client.get(
        "/bundles",
        headers=HEADERS,
    )

    assert response.status_code == 200

    p = json.loads(response.content, object_hook=lambda d: SimpleNamespace(**d))

    assert p.navigation.total >= 1

def test_update_bundle_invalid_packages(test_tables : None, client: TestClient):

    random = Utils.randomword(5)

    bundle_name = "bundle_" + random

    b_response = client.post(
        "/bundles",
        headers=HEADERS,
        json={
            "name": bundle_name,
            "packages": [{"name": "alabaster", "version": "0.7.17", "use_legacy": True}],
        },
    )

    assert b_response.status_code == 201

    invalid_packages = [
        [
            {"name": "somehting", "version": "1.1.1"},
            {"name": "else", "version": ["1.1.1"]}, # test for invalid version type
        ],
        [
            {"name": 123, "version": "1.1.1"}, # test for invalid name attr type
            {"name": "else", "version": ["1.1.1"]},
        ],
        [
            {"name": "", "version": "1.1.1"}, # test for empty package name
            {"name": "else", "version": ""},
        ],
        [
            {"version": "1.1.1"},  # test for invalid package with no name
            {"name": "else", "version": ""},
        ],
        [
            {"name": "emptyver", "version": ""}, # test for empty version
        ],
        [
            {"name": "missingver"}, # test for missing version
        ],
        [
            {"name": "invalid*name"},  # test for invalid package name
            {"name": "else", "version": ""},
        ],
        [
            {"name": "alabaster", "version": "0.7.12"},  # test for package name repeated (different versions)
            {"name": "alabaster", "version": "6.12b"},
        ],
        # [
        #     {"name": "anyio", "version": "3.5.0"},  # test for package name repeated same version
        #     {"name": "anyio", "version": "3.5.0"},
        # ],
        [
            {"name": "anyio", "version": "3.5.0"},  # test for package name repeated, one of them for deletion
            {"name": "anyio", "version": "!"},
        ],
        [
            {"name": "sphinx"},  # test for package name repeated, same implicit version
            {"name": "sphinx", "version": ""},
        ],
    ]

    for p in invalid_packages:
        i_response = client.put(f"/bundles/{bundle_name}", headers=HEADERS, json=p)
        assert (
            i_response.status_code == 422
        ), "bundle packages should not be accepted: " + str(p)

    assert True

def test_update_bundle_packages(test_tables : None, client: TestClient):

    random = Utils.randomword(5)

    bundle_name = "bundle_" + random

    b_response = client.post(
        "/bundles",
        headers=HEADERS,
        json={
            "name": bundle_name,
            "packages": [{"name": "anyio", "version": "3.5.0", "use_legacy": True}],
        },
    )

    assert b_response.status_code == 201

    b = json.loads(b_response.content, object_hook=lambda d: SimpleNamespace(**d))

    assert len(b.packages) == 1

    response = client.put(f"/bundles/{bundle_name}", headers=HEADERS, json=[
        {"name": "anyio", "version": "3.5.1", "use_legacy": True},
        {"name": "fastapi", "version": "0.75.1", "use_legacy": False},
        {"name": "alabaster", "version": "0.7.12"}
    ])

    assert response.status_code == 200

    r = json.loads(response.content, object_hook=lambda d: SimpleNamespace(**d))

    assert len(r.packages) == 3
    assert r.packages[0].name == "anyio"
    assert r.packages[0].version == "3.5.1"
    assert r.packages[0].use_legacy == True
    assert r.packages[1].name == "fastapi"
    assert r.packages[1].version == "0.75.1"
    assert r.packages[1].use_legacy == False
    assert r.packages[2].name == "alabaster"
    assert r.packages[2].version == "0.7.12"
    assert r.packages[2].use_legacy == False


def test_update_bundle_valid_packages(test_tables : None, client: TestClient):

    random = Utils.randomword(5)

    bundle_name = "bundle_" + random

    b_response = client.post(
        "/bundles",
        headers=HEADERS,
        json={
            "name": bundle_name,
            "packages": [{"name": "anyio", "version": "3.5.0", "use_legacy": True}],
        },
    )

    assert b_response.status_code == 201

    valid_packages = [
        [
            {"name": "anyio", "version": "3.5.1"} # existing versions
        ],
        [
            {"name": "sphinx", "version": "4.5.0"}, # existing versions
            {"name": "fastapi", "version": "0.75.1"}
        ],
        [
            {"name": "fastapi",  "version": "0.75.1"},  # test for existing package versions
            {"name": "alabaster", "version": "0.7.12"}
        ],
        [
            {"name": "anyio", "version": "3.5.0" }  # test a single correct reference
        ],
        [
            {"name": "alabaster", "version": "0.7.17" },  # another correct set
            {"name": "fastapi",  "version": "0.75.1"},
            {"name": "sphinx", "version": "4.5.0"},
        ]
    ]

    for p in valid_packages:
        i_response = client.put(f"/bundles/{bundle_name}", headers=HEADERS, json=p)
        assert (
            i_response.status_code == 200
        ), "bundle packages should be accepted: " + str(p)

    assert True

def test_update_missing_packages(test_tables : None, client: TestClient):

    random = Utils.randomword(5)

    bundle_name = "bundle_" + random

    b_response = client.post(
        "/bundles",
        headers=HEADERS,
        json={
            "name": bundle_name,
            "packages": [{"name": "fastapi", "version": "0.75.1", "use_legacy": True}],
        },
    )

    assert b_response.status_code == 201

    valid_packages = [
        # [
        #     {"name": "anyio", "version": "9.999"}, # test for missing version ref
        # ],
        [
            {"name": "alabaox"}, # test for a missing package
            {"name": "fastapi", "version": "0.75.1"}
        ],
        [
            {"name": "fastapi", "version": "!"} # test for a deletion mark with valid name
        ],
        [
            {"name": "missingname", "version": "!"} # test for a deletion mark with invalid name
        ],
        [
            {"name": "xxyyzz" }  # test a single missing package name with no version explicited
        ]
    ]

    for p in valid_packages:
        i_response = client.put(f"/bundles/{bundle_name}", headers=HEADERS, json=p)
        assert (
            i_response.status_code == 422
        ), "bundle packages should not be accepted: " + str(p)

    assert True