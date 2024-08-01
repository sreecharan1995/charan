# coding: utf-8

import json
from types import SimpleNamespace
from typing import List

from fastapi.testclient import TestClient

from common.utils import Utils
from dependency.api.model.new_profile_model import NewProfileModel
from dependency.api.model.package_reference_model import PackageReferenceModel
from dependency.service.bundle_service import BundleService
from dependency.service.profile_service import ProfileService

profile_service = ProfileService()
bundle_service = BundleService()

HEADERS = {
    "Authorization": "Bearer DISABLED",
    "Content-Type": "application/json"
}


def test_list_profiles(test_tables: None, client: TestClient):
    """Test case for listing profiles

    Gets the first page of available profiles
    """

    random = Utils.randomword(5)
    random_path = "/test/" + random
    name = "Profile_name_is_" + random

    response = client.post(
        "/profiles?path=" + random_path,
        headers=HEADERS,
        json={
            "name": name,
            "description": "a short description",
        },
    )

    assert response.status_code == 201

    response = client.get("/profiles", headers=HEADERS)

    assert response.status_code == 200

    p = json.loads(response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    assert p.navigation is not None
    assert p.navigation.page == 1
    assert p.navigation.pages >= 1
    assert p.navigation.items >= 1

    assert p.items is not None
    assert len(p.items) == p.navigation.items

    for p in p.items:
        assert p.name is not None
        assert p.path is not None

    assert True


def test_create_profile(test_tables: None, client: TestClient):
    """Test case for creating a profile

    Create a new profile and checks the response
    """

    random = Utils.randomword(5)
    random_path = "/test/" + random
    name = "Profile_name_is_" + random

    response = client.post(
        "/profiles?path=" + random_path,
        headers=HEADERS,
        json={
            "name": name,
            "description": "a short description",
        },
    )

    assert response.status_code == 201

    p = json.loads(response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    assert p.id != ''
    assert p.name == name
    assert p.path == random_path
    assert p.description == "a short description"
    assert p.profile_status == "pending"
    assert p.created_at is not None


def test_create_profiles_at_path(test_tables: None, client: TestClient):
    """Test case for creating more than one profile at a specific path

    Create a new profile at a path, then attempt to create another one at same path, should fail. Delete the original and attempt at same path, should suceed
    """

    random = Utils.randomword(5)

    name = "Profile_name_is_" + random

    random_path: str = "/mumbai/" + random + '/abc'

    response = client.post(
        "/profiles?path=" + random_path,
        headers=HEADERS,
        json={
            "name": name,
            "description": "a short description",
        },
    )

    assert response.status_code == 201

    p = json.loads(response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    assert p.path == random_path

    response2 = client.post(
        "/profiles?path=" + random_path,
        headers=HEADERS,
        json={
            "name": name,
            "description": "a short description",
        },
    )

    assert response2.status_code == 409

    r2 = json.loads(response2.content,
                    object_hook=lambda d: SimpleNamespace(**d))

    assert r2.detail == "There is already a profile attached to path " + random_path

    response3 = client.post(
        "/profiles?path=" + random_path.upper(),  # upper case the path
        headers=HEADERS,
        json={
            "name": name,
            "description": "a short description",
        },
    )

    assert response3.status_code == 201

    # delete the original attached profile and retest creation

    d_response = client.delete("/profiles/" + p.id, headers=HEADERS)

    assert d_response.status_code == 204

    response4 = client.post(
        "/profiles?path=" + random_path,
        headers=HEADERS,
        json={
            "name": name,
            "description": "a short description",
        },
    )

    assert response4.status_code == 201


def test_get_missing_profile_at_root(test_tables: None, client: TestClient):
    """Test case for retrieving the effective root profile and any other deeper path when the root profile does not exist

    Forces a service-level deletion of the root profile, then attempts gets by path, it should fail to get an efective profile because there is no root profile
    """

    profile_service.detach_from_path(
        '/', force=True)  # force deletion of root profile so the test work
    profile_service.detach_from_path('/toronto')
    profile_service.detach_from_path('/toronto/abc')

    response1 = client.get("/effective-profile?path=/", headers=HEADERS)

    assert response1.status_code == 404

    r1 = json.loads(response1.content,
                    object_hook=lambda d: SimpleNamespace(**d))

    assert r1.detail == 'Profile not found at path: /'

    response2 = client.get("/effective-profile?path=/toronto", headers=HEADERS)

    assert response2.status_code == 404

    r2 = json.loads(response2.content,
                    object_hook=lambda d: SimpleNamespace(**d))

    assert r2.detail == 'Profile not found at path: /toronto'

    response3 = client.get("/effective-profile?path=/toronto/abc",
                           headers=HEADERS)

    assert response3.status_code == 404

    r3 = json.loads(response3.content,
                    object_hook=lambda d: SimpleNamespace(**d))

    assert r3.detail == 'Profile not found at path: /toronto/abc'


def test_profile_at_root_undeletable(test_tables: None, client: TestClient):
    """Test case for checking a profile at root can not be deleted

    Forces a service-level deletion of the root profile, creates a new profile at the root and attempts to delete it. It should fail.
    """

    profile_service.detach_from_path(
        '/', force=True)  # force deletion of root profile so the test work

    response = client.post(
        "/profiles?path=/",
        headers=HEADERS,
        json={
            "name": "the_root_profile",
            "description": "a short description",
        },
    )

    assert response.status_code == 201

    p = json.loads(response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    assert p.path == '/'  # make sure it was attached to root

    # d1_response = client.delete( # attempt deletion by path
    #     "/effective-profile?path=/",
    #     headers=HEADERS
    # )

    # assert d1_response.status_code == 400

    # d1 = json.loads(d1_response.content, object_hook=lambda d: SimpleNamespace(**d))

    # assert d1.detail == "Unable to delete the root profile"

    d2_response = client.delete(  # attempt deletion by profile id
        f"/profiles/{p.id}",
        headers=HEADERS)

    assert d2_response.status_code == 400

    d2 = json.loads(d2_response.content,
                    object_hook=lambda d: SimpleNamespace(**d))

    assert d2.detail == "Unable to delete the root profile"


# def test_profile_at_root_unreplaceable_when_missing(test_tables : None, client: TestClient):
#     """Test case for checking a profile at root can not be replaced when is missing

#     Forces a service-level deletion of the root profile, then attempts to replace (PUT) a profile ther, it should faild
#     """

#     profile_service.deattach_from_path('/', force=True) # force deletion of root profile so the test work

#     headers = {"Content-Type": "application/xml"}

#     response = client.put(
#         "/effective-profile?path=/",
#         headers=HEADERS,
#         data=''
#     )

#     assert response.status_code == 404


def test_create_profile_at_root(test_tables: None, client: TestClient):
    """Test case for creating a profile at the root (default path)

    Create a new profile and checks the response
    """

    profile_service.detach_from_path(
        '/',
        force=True)  # make sure there is no profile at root so the test works

    random = Utils.randomword(5)
    name = "name_" + random

    response = client.post(
        "/profiles?path=/",  # NO implicit path = / when creating
        headers=HEADERS,
        json={
            "name": name,
            "description": "a short description",
        },
    )

    assert response.status_code == 201

    p = json.loads(response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    assert p.id != ''
    assert p.name == name
    assert p.path == "/"  # should be the root
    assert p.description == "a short description"
    assert p.profile_status == "pending"
    assert p.created_at is not None


# def test_profile_set_packages(test_tables : None, client: TestClient):
#     """Test case for setting profile packages

#     Create a profile, then sets a package list, then retrieves and checks the response matches
#     """

#     random = Utils.randomword(5)
#     random_path = '/testp/' + random
#     name = "name_" + random

#
#     response = client.post(
#         "/effective-profile?path=" + random_path,
#         headers=HEADERS,
#         json={
#             "name": name,
#             "description": "a short description",
#         },
#     )

#     assert response.status_code == 201

#     r = json.loads(response.content, object_hook=lambda d: SimpleNamespace(**d))

#     p_response = client.put(
#         "/profiles/" + r.id + "/packages",
#         headers=HEADERS,
#         json=[
#             {"name": "alabaster", "version": "0.7.12"},
#             {"name": "fastapi", "version": ""},
#         ],
#     )

#     assert p_response.status_code == 200

#     p = json.loads(p_response.content, object_hook=lambda d: SimpleNamespace(**d))

#     assert len(p) == 2

#     assert p[0].name == "alabaster"
#     assert p[0].version == "0.7.12"
#     assert p[1].name == "fastapi"
#     assert p[1].version == ""

#     g_response = client.get("/profiles/" + r.id + "/packages", headers=HEADERS)

#     g = json.loads(g_response.content, object_hook=lambda d: SimpleNamespace(**d))

#     assert len(g) == 2

#     assert g[0].name == "alabaster"
#     assert g[0].version == "0.7.12"
#     assert g[1].name == "fastapi"
#     assert g[1].version == ""

# def test_profile_set_invalid_packages(test_tables : None, client: TestClient):
#     """Test case for setting profile packages with some of them invalid

#     Create a profile, then attempt setting an invalid package list, repeat for various invalid lists
#     """

#     random = Utils.randomword(5)
#     random_path = '/test' + Utils.randomword(5)
#     name = "name_" + random

#
#     response = client.post(
#         "/effective-profile?path=" + random_path,
#         headers=HEADERS,
#         json={
#             "name": name,
#             "description": "a short description",
#         },
#     )

#     assert response.status_code == 201

#     r = json.loads(response.content, object_hook=lambda d: SimpleNamespace(**d))

#     invalid_packages = [ # type: ignore
#         [
#             {"name": "alabaster", "version": "0.7.12"},
#             {"name": "anyio", "version": "3.5 .0"},
#         ],  # contains a package with invalid version
#         [
#             {"name": "alabaster", "version": "0.7.12"},
#             {"name": "anyio", "version": []},
#         ],  # contains a package with invalid version
#         [
#             {"name": "alabaster", "version": "0.7.12"},
#             {"xname": "anyio", "version": "3.5.0"},
#         ],  # contains a package with no name
#         [
#             {"name": "ala  baster", "version": "0.7.12"},
#             {"name": "anyio", "version": "3.5.0"},
#         ],  # contains a package with invalid name
#         [
#             {"name": "anyio", "version": "0.7.12"},
#             {"name": "anyio", "version": "3.5.0"},
#         ],  # contains a repeated package name ref, different versions
#         [
#             {"name": "anyio", "version": "3.5.0"},
#             {"name": "anyio", "version": "3.5.0"},
#         ],  # contains a repeated package name ref, same versions
#         [
#             {"name": "anyio", "version": ""},
#             {"name": "anyio"},
#         ],  # contains a repeated package name ref, same implicit versions
#     ]

#     for pl in invalid_packages: # type: ignore
#         p_response = client.put(
#             "/profiles/" + r.id + "/packages", headers=HEADERS, json=pl  # type: ignore
#         )
#         assert (
#             p_response.status_code == 422
#         ), "package list should be unprocessable " + str(pl) # type: ignore

#     assert True

# def test_profile_set_missing_packages(test_tables : None, client: TestClient):
#     """Test case for setting profile package references with some of them poting to missing package names or missing versions

#     Create a profile, then attempt setting an missing package ref list, repeat for various invalid cases
#     """

#     random = Utils.randomword(5)
#     random_path = '/test/' + random
#     name = "name_" + random

#
#     response = client.post(
#         "/effective-profile?path=" + random_path,
#         headers=HEADERS,
#         json={
#             "name": name,
#             "description": "a short description",
#         },
#     )

#     assert response.status_code == 201

#     r = json.loads(response.content, object_hook=lambda d: SimpleNamespace(**d))

#     bad_packages = [
#         [
#             {"name": "alabaster", "version": "0.7"},
#             {"name": "anyio", "version": "3.5.0"},
#         ],  # alabaster refs missing version
#         [
#             {"name": "alabaster", "version": ""},
#             {"name": "anyio", "version": "9.99"},
#         ],  # anyio refs missing version
#         [
#             {"name": "anyio", "version": "3.5.0"},
#             {"name": "alabao", "version": "0.7.12"},
#         ],  # alabao is missing
#     ]

#     for pl in bad_packages:
#         p_response = client.put(
#             "/profiles/" + r.id + "/packages", headers=HEADERS, json=pl
#         )
#         assert (
#             p_response.status_code == 422
#         ), "package refs list should be unprocessable " + str(pl)
#         p = json.loads(p_response.content, object_hook=lambda d: SimpleNamespace(**d))
#         assert str(p.detail).startswith("referenced package is unknown.")

#     assert True

# def test_missing_profile_set_packages(test_tables : None, client: TestClient):
#     """Test case for setting profile packages for a profile that does not exist

#     Attempt setting a package list for a profile with random name, it should fail
#     """

#     random = Utils.randomword(5)
#

#     p_response = client.put(
#         "/profiles/" + random + "/packages",
#         headers=HEADERS,
#         json=[
#             {"name": "first_package", "version": "1.1.1"},
#             {"name": "package2", "version": ""},
#         ],
#     )

#     assert p_response.status_code == 404

#     p = json.loads(p_response.content, object_hook=lambda d: SimpleNamespace(**d))

#     assert p.detail == "Profile not found"


def test_get_profile_effective(test_tables: None, client: TestClient):
    """Test case for getting an effective profile at a path

    Creates a profile at root then creates a profiles in a child node, then gets the effective profile in paths and check properties
    """

    # force removal of profiles so the test can work
    profile_service.detach_from_path('/', force=True)
    profile_service.detach_from_path('/mumbai/a/b')

    r_random = Utils.randomword(5)

    r_profile = profile_service.create_profile('/',
                                               new_profile=NewProfileModel(
                                                   name=r_random,
                                                   description="root desc"),
                                               operator=None)

    assert r_profile is not None

    r_pk_refs: List[PackageReferenceModel] = [
        PackageReferenceModel(name="fastapi", version="0.73"),
        PackageReferenceModel(name="anyio", version="3.5.0")
    ]

    profile_service.set_profile_packages(r_profile.id, r_pk_refs)

    mab_random = Utils.randomword(5)

    mab_profile = profile_service.create_profile(
        '/mumbai/a/b',
        new_profile=NewProfileModel(name=mab_random,
                                    description="mumbai a b desc"),
        operator=None)

    assert mab_profile is not None

    m_pk_refs: List[PackageReferenceModel] = [
        PackageReferenceModel(name="fastapi", version="0.75.1")
    ]

    profile_service.set_profile_packages(mab_profile.id, m_pk_refs)

    # get the effective profile at /mumbai and check

    m_response = client.get(
        f"/effective-profile?path=/mumbai",
        headers=HEADERS,
    )

    assert m_response.status_code == 200

    m = json.loads(m_response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    assert m.id == r_profile.id
    assert m.name == r_random
    assert m.description == "root desc"

    # get the effective profile at /mumbai/xyz and check

    mx_response = client.get(
        f"/effective-profile?path=/mumbai/xyz",
        headers=HEADERS,
    )

    assert mx_response.status_code == 200

    mx = json.loads(mx_response.content,
                    object_hook=lambda d: SimpleNamespace(**d))

    assert mx.id == r_profile.id
    assert mx.name == r_random
    assert mx.description == "root desc"

    # get the effective profile at /mumbai/a/b and check

    mab_response = client.get(
        f"/effective-profile?path=/mumbai/a/b",
        headers=HEADERS,
    )

    assert mab_response.status_code == 200

    mab = json.loads(mab_response.content,
                     object_hook=lambda d: SimpleNamespace(**d))

    assert mab.id == mab_profile.id
    assert mab.name == mab_random
    assert mab.description == "mumbai a b desc"

    # get the effective profile at /mumbai/a/b/x/y/zzz and check

    mabx_response = client.get(
        f"/effective-profile?path=/mumbai/a/b/x/y/z",
        headers=HEADERS,
    )

    assert mabx_response.status_code == 200

    mabx = json.loads(mabx_response.content,
                      object_hook=lambda d: SimpleNamespace(**d))

    assert mabx.id == mab_profile.id
    assert mabx.name == mab_random
    assert mabx.description == "mumbai a b desc"


def test_get_profile_effective_packages(test_tables: None, client: TestClient):
    """Test case for getting the list of effective packages using a profile id

    Creates a profile at root then creates a profiles in a child node, then gets the package list and checks the list.
    """

    # force removal of profiles so the test can work
    profile_service.detach_from_path('/', force=True)
    profile_service.detach_from_path('/mumbai/a/b')

    r_random = Utils.randomword(5)

    r_profile = profile_service.create_profile(
        '/', new_profile=NewProfileModel(name=r_random), operator=None)

    assert r_profile is not None

    r_pk_refs: List[PackageReferenceModel] = [
        PackageReferenceModel(name="fastapi", version="0.73"),
        PackageReferenceModel(name="anyio", version="3.5.0")
    ]

    profile_service.set_profile_packages(r_profile.id, r_pk_refs)

    m_random = Utils.randomword(5)

    m_profile = profile_service.create_profile(
        '/mumbai/a/b',
        new_profile=NewProfileModel(name=m_random),
        operator=None)

    assert m_profile is not None

    m_pk_refs: List[PackageReferenceModel] = [
        PackageReferenceModel(name="fastapi", version="0.75.1")
    ]

    profile_service.set_profile_packages(m_profile.id, m_pk_refs)

    # get the effective profile via api and check

    g_response = client.get(
        f"/profiles/{m_profile.id}/packages",
        headers=HEADERS,
    )

    assert g_response.status_code == 200

    g = json.loads(g_response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    assert len(g) == 2
    assert g[0].name == "fastapi"
    assert g[0].version == "0.75.1"
    assert g[1].name == "anyio"
    assert g[1].version == "3.5.0"

    # delete a package from the effective

    d_response = client.delete(
        f"/profiles/{m_profile.id}/packages/anyio",
        headers=HEADERS,
    )

    assert d_response.status_code == 204

    # get the effective profile via api and check

    g_response = client.get(
        f"/profiles/{m_profile.id}/packages",
        headers=HEADERS,
    )

    assert g_response.status_code == 200

    g = json.loads(g_response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    assert len(g) == 1
    assert g[0].name == "fastapi"
    assert g[0].version == "0.75.1"

    # delete a package from the local-effective

    d_response = client.delete(
        f"/profiles/{m_profile.id}/packages/fastapi",
        headers=HEADERS,
    )

    assert d_response.status_code == 204

    # get the effective profile via api and check

    g_response = client.get(
        f"/profiles/{m_profile.id}/packages",
        headers=HEADERS,
    )

    assert g_response.status_code == 200

    g = json.loads(g_response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    assert len(g) == 0

    d_response = client.delete(
        f"/profiles/{m_profile.id}/packages/fastapi_xyz",
        headers=HEADERS,
    )

    assert d_response.status_code == 404


def test_get_profile_effective_full_package_list(test_tables: None, client: TestClient):
    """Test case for getting the list of full effective package list using a profile id
    """

    # force removal of profiles so the test can work
    profile_service.detach_from_path('/', force=True)
    profile_service.detach_from_path('/mumbai', force=True)
    profile_service.detach_from_path('/mumbai/a', force=True)
    profile_service.detach_from_path('/mumbai/a/b', force=True)

    r_random = Utils.randomword(5)

    r_profile = profile_service.create_profile(
        '/', new_profile=NewProfileModel(name=r_random), operator=None)

    assert r_profile is not None

    r_pk_refs: List[PackageReferenceModel] = [
        PackageReferenceModel(name="fastapi", version="0.73")
    ]

    profile_service.set_profile_packages(r_profile.id, r_pk_refs)

    m_random = Utils.randomword(5)

    m_profile = profile_service.create_profile(
        '/mumbai/a/b',
        new_profile=NewProfileModel(name=m_random),
        operator=None)

    assert m_profile is not None

    m_pk_refs: List[PackageReferenceModel] = [
        PackageReferenceModel(name="fastapi", version="0.75.1")
    ]

    profile_service.set_profile_packages(m_profile.id, m_pk_refs)

    b_pk_refs: List[PackageReferenceModel] = [
        PackageReferenceModel(name="anyio", version="3.5.0")
    ]

    profile_service.add_profile_bundle(profile_id=m_profile.id, bundle_name="test_bundle", bundle_description="", pkr_list=b_pk_refs, assume_bundle_in_library=True, replace_allowed=False)

    # get the full effective list

    g_response = client.get(
        f"/profiles/{m_profile.id}/all",
        headers=HEADERS,
    )

    assert g_response.status_code == 200

    g = json.loads(g_response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    assert len(g) == 2
    assert g[0] == "fastapi-0.75.1"
    assert g[1] == "anyio-3.5.0"


def test_get_profile_effective_bundles(test_tables: None, client: TestClient):
    """Test case for getting the list of effective bundles using a profile id

    Creates a profile at root then creates a profiles in a child node, then gets the bundles and checks the list contents.
    """

    # force removal of profiles so the test can work
    profile_service.detach_from_path('/', force=True)
    profile_service.detach_from_path('/mumbai/a/b')

    r_random = Utils.randomword(5)

    r_profile = profile_service.create_profile(
        '/', new_profile=NewProfileModel(name=r_random), operator=None)

    assert r_profile is not None

    r_bundle1_pkrefs: List[PackageReferenceModel] = [
        PackageReferenceModel(name="fastapi", version="0.73"),
        PackageReferenceModel(name="anyio", version="3.5.0")
    ]

    r_bundle2_pkrefs: List[PackageReferenceModel] = [
        PackageReferenceModel(name="sphinx", version="4.5.0"),
    ]

    c_bundle_pkrefs: List[PackageReferenceModel] = [
        PackageReferenceModel(name="alabaster", version="0.7.17"),
    ]

    profile_service.add_profile_bundle(r_profile.id,
                                       "bundle1",
                                       "desc1",
                                       r_bundle1_pkrefs,
                                       assume_bundle_in_library=True)
    profile_service.add_profile_bundle(r_profile.id,
                                       "bundle2",
                                       "desc2",
                                       r_bundle2_pkrefs,
                                       assume_bundle_in_library=True)
    profile_service.add_profile_bundle(r_profile.id,
                                       "bundle3",
                                       "desc3",
                                       c_bundle_pkrefs,
                                       assume_bundle_in_library=True)

    profile_service.delete_profile_bundle(r_profile.id, "bundle3")

    m_random = Utils.randomword(5)

    m_profile = profile_service.create_profile(
        '/mumbai/a/b',
        new_profile=NewProfileModel(name=m_random),
        operator=None)

    assert m_profile is not None

    m_bundle1_pkrefs: List[PackageReferenceModel] = [
        PackageReferenceModel(name="fastapi", version="0.75.1")
    ]

    m_bundle4_pkrefs: List[PackageReferenceModel] = [
        PackageReferenceModel(name="alabaster", version="0.7.12")
    ]

    profile_service.add_profile_bundle(m_profile.id,
                                       "bundle1",
                                       "desc1",
                                       m_bundle1_pkrefs,
                                       assume_bundle_in_library=True,
                                       replace_allowed=True)
    profile_service.add_profile_bundle(m_profile.id,
                                       "bundle2",
                                       "desc2",
                                       c_bundle_pkrefs,
                                       assume_bundle_in_library=True,
                                       replace_allowed=True)
    profile_service.add_profile_bundle(m_profile.id,
                                       "bundle4",
                                       "desc4",
                                       m_bundle4_pkrefs,
                                       assume_bundle_in_library=True)

    profile_service.delete_profile_bundle(m_profile.id, "bundle2")

    # get the effective profile via api and check

    g_response = client.get(
        f"/profiles/{m_profile.id}/bundles",
        headers=HEADERS,
    )

    assert g_response.status_code == 200

    g = json.loads(g_response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    items = g.items

    assert len(items) == 2

    assert items[0].name == "bundle1"
    assert items[0].description == "desc1"
    assert len(items[0].packages) == 1
    assert items[0].packages[0].name == "fastapi"
    assert items[0].packages[0].version == "0.75.1"

    assert items[1].name == "bundle4"
    assert items[1].description == "desc4"
    assert len(items[1].packages) == 1
    assert items[1].packages[0].name == "alabaster"
    assert items[1].packages[0].version == "0.7.12"

    # delete the bundle1 (inherited) and check if missing from the effective

    d_response = client.delete(
        f"/profiles/{m_profile.id}/bundles/bundle1",
        headers=HEADERS,
    )

    assert d_response.status_code == 204

    # get the effective profile via api and check

    g_response = client.get(
        f"/profiles/{m_profile.id}/bundles",
        headers=HEADERS,
    )

    assert g_response.status_code == 200

    g = json.loads(g_response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    items = g.items
    assert len(items) == 1
    assert items[0].name == "bundle4"
    assert items[0].description == "desc4"
    assert len(items[0].packages) == 1
    assert items[0].packages[0].name == "alabaster"
    assert items[0].packages[0].version == "0.7.12"

    # delete the bundle4 (local) and check if also missing from the effective

    d_response = client.delete(
        f"/profiles/{m_profile.id}/bundles/bundle4",
        headers=HEADERS,
    )

    assert d_response.status_code == 204

    # get the effective profile via api and check

    g_response = client.get(
        f"/profiles/{m_profile.id}/bundles",
        headers=HEADERS,
    )

    assert g_response.status_code == 200

    g = json.loads(g_response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    assert len(g.items) == 0

    d_response = client.delete(
        f"/profiles/{m_profile.id}/bundles/bundle_xyz",
        headers=HEADERS,
    )

    assert d_response.status_code == 404


def test_profile_delete_bundle(test_tables: None, client: TestClient):
    """Test case for deleting a bundle from a profile

    Create a profile, create a bundle, then add bundle to profile using bundle name. Attempt add a bundle not know in library to profile, it should fail.
    """

    random = Utils.randomword(5)
    random_path = "/test/" + random
    name = "name_" + random

    response = client.post(
        "/profiles?path=" + random_path,
        headers=HEADERS,
        json={
            "name": name,
            "description": "a short description",
        },
    )

    assert response.status_code == 201

    r = json.loads(response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    bundle_name = "bundle_" + random
    bundle_desc = f"bundle desc {bundle_name}"

    b_response = client.post(
        "/bundles",
        headers=HEADERS,
        json={
            "name": bundle_name,
            "description": bundle_desc,
            "packages": [
                {
                    "name": "alabaster",
                    "version": "0.7.12",
                    "use_legacy": True
                },
                {
                    "name": "fastapi",
                    "version": "0.73",
                    "use_legacy": False
                },
            ],
        },
    )

    assert b_response.status_code == 201

    a_response = client.post(
        f"/profiles/{r.id}/bundles/{bundle_name}",
        headers=HEADERS,
    )

    assert a_response.status_code == 201

    a = json.loads(a_response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    assert a.name == bundle_name
    assert a.description == bundle_desc
    assert len(a.packages) == 2

    d1_response = client.delete(f"/profiles/{r.id}/bundles/{bundle_name}",
                                headers=HEADERS)

    assert d1_response.status_code == 204

    d2_response = client.delete(f"/profiles/{r.id}/bundles/{bundle_name}",
                                headers=HEADERS)

    assert d2_response.status_code == 204  # is known and already marked deleted

    d3_response = client.delete("/profiles/" + r.id + "/bundles/bundle_xyz_" +
                                random,
                                headers=HEADERS)

    assert d3_response.status_code == 404  # is not known

    d3 = json.loads(d3_response.content,
                    object_hook=lambda d: SimpleNamespace(**d))

    assert d3.detail == "Bundle not found"


def test_missing_profile_delete_bundle(test_tables: None, client: TestClient):
    """Test case for deleting a bundle from a profile which does not exist

    Attempt to delete a bundle with random name for a profile with random name, should fail
    """

    random = Utils.randomword(5)

    d2_response = client.delete("/profiles/" + random + "/bundles/" + random,
                                headers=HEADERS)

    assert d2_response.status_code == 404

    d2 = json.loads(d2_response.content,
                    object_hook=lambda d: SimpleNamespace(**d))

    assert d2.detail == "Profile not found"


def test_profile_add_bundles(test_tables: None, client: TestClient):
    """Test case for adding bundles to a profile

    Create a profile and a bundle, then add bundle to profile, then add again (same name) so it should fail
    """

    random = Utils.randomword(5)
    random_path = '/test/' + random
    name = "name_" + random

    response = client.post(
        "/profiles?path=" + random_path,
        headers=HEADERS,
        json={
            "name": name,
            "description": "a short description",
        },
    )

    assert response.status_code == 201

    r = json.loads(response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    bundle_name = "bundle_" + random

    b_response = client.post(
        "/bundles",
        headers=HEADERS,
        json={
            "name":
            bundle_name,
            "packages": [
                {
                    "name": "alabaster",
                    "version": "0.7.12",
                    "use_legacy": True
                },
                {
                    "name": "fastapi",
                    "version": "0.73",
                    "use_legacy": False
                },
            ],
        },
    )

    assert b_response.status_code == 201

    b1_response = client.post(f"/profiles/{r.id}/bundles/{bundle_name}",
                              headers=HEADERS)

    assert b1_response.status_code == 201, "response: " + str(
        b1_response.content)

    # b2_response = client.post(
    #     f"/profiles/{r.id}/bundles/{bundle_name}",
    #     headers=HEADERS
    # )

    # assert b2_response.status_code == 201, "response: " + str(b2_response.content) # same package list is accepted

    # change the bundle package list in the library:
    new_pkg_ref_list: List[PackageReferenceModel] = [
        PackageReferenceModel(name="alabaster", version="0.7.12")
    ]
    bundle_service.update_bundle_packages(bundle_name, new_pkg_ref_list)

    b3_response = client.post(f"/profiles/{r.id}/bundles/{bundle_name}",
                              headers=HEADERS)

    assert b3_response.status_code == 409, "response: " + str(
        b3_response.content)  # different package list should fail


def test_missing_profile_add_bundle(test_tables: None, client: TestClient):
    """Test case for adding a bundle for a profile which does not exist

    Attempt to add a bundle with an arbitrary name for a profile with a random name, it should fail
    """

    random = Utils.randomword(5)

    u_response = client.post("/profiles/" + random + "/bundles/" + random,
                             headers=HEADERS)

    assert u_response.status_code == 404

    u = json.loads(u_response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    assert u.detail == "Bundle not found"


def test_add_invalid_bundles(test_tables: None, client: TestClient):
    """Test case for adding invalid bundles to the library

    Test adding invalid bundles which should be unaceptable
    """

    # random = Utils.randomword(5)

    invalid_bundles = [
        {  # test for missing id
            "packages": [
                {
                    "name": "somehting",
                    "version": "1.1.1"
                },
                {
                    "name": "else",
                    "version": "9.9.9"
                },
            ]
        },
        {
            "name":
            "a b",  # test for invalid name
            "packages": [
                {
                    "name": "somehting",
                    "version": "1.1.1"
                },
                {
                    "name": "else",
                    "version": "4.8.9"
                },
            ],
        },
        {
            "name":
            "abx11",
            "packages": [
                {
                    "name": "somehting",
                    "version": "1.1.1"
                },
                {
                    "name": "else",
                    "version": ""
                },  # test for empty version
            ],
        },
        {
            "name":
            "abx12",
            "packages": [
                {
                    "name": "somehting",
                    "version": "1.1.1"
                },
                {
                    "name": "else"
                },  # test for version not present
            ],
        },
        {
            "name": "a_b",
            # test for invalid packages list
            "packages": 10,
        },
        {
            "name":
            "abc",
            "packages": [
                {
                    "version": "1.1.1"
                },  # test for invalid package with no name
                {
                    "name": "else",
                    "version": "1.122"
                },
            ],
        },
        {
            "name":
            "abcd",
            "packages": [
                {
                    "name": "invalid*name",
                    "version": "99.44"
                },  # test for invalid package name
                {
                    "name": "else",
                    "version": "129_bcd"
                },
            ],
        },
        {
            "name":
            "abcdxyz_9999",
            "packages": [
                {
                    "name": "sphinx",
                    "version": "4.5.0"
                },  # test for repeated package ref, same version
                {
                    "name": "sphinx",
                    "version": "4.5.0"
                },
            ],
        },
        {
            "name":
            "abcdxyz_av",
            "packages": [
                {
                    "name": "fastapi",
                    "version": "0.73"
                },  # test for repeated package ref, different version
                {
                    "name": "fastapi",
                    "version": "0.75.1"
                },
            ],
        },
    ]

    for b in invalid_bundles:
        i_response = client.post("/bundles", headers=HEADERS, json=b)
        assert (i_response.status_code == 422
                ), "bundle should not be accepted: " + str(b)

    assert True


def test_get_profile(test_tables: None, client: TestClient):
    """Test case for getting an existing profile

    Tests getting a profile after it is created, then checks the response
    """

    random = Utils.randomword(5)
    random_path = '/test/' + random
    name = "profile_name_" + random

    c_response = client.post(
        "/profiles?path=" + random_path,
        headers=HEADERS,
        json={
            "name": name,
            "description": "something to say"
        },
    )

    assert c_response.status_code == 201

    c = json.loads(c_response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    g_response = client.get(
        "/profiles/" + c.id,
        headers=HEADERS,
    )

    g = json.loads(g_response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    assert g.id == c.id
    assert g.name == c.name
    assert g.path == random_path
    assert g.name == c.name
    assert g.description == c.description
    assert g.profile_status == c.profile_status
    assert g.created_at == c.created_at


def test_get_missing_profile(test_tables: None, client: TestClient):
    """Test case for getting a non existing profile

    Tests getting a profile after it is created, then checks the response
    """

    random = Utils.randomword(5)

    g_response = client.get("/profiles/" + random, headers=HEADERS)

    assert g_response.status_code == 404

    g = json.loads(g_response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    assert g.detail == "Profile not found"


def test_patch_profile(test_tables: None, client: TestClient):
    """Test case for patching an existing profile (basic properties only)

    Create a new profile, then performs a patch
    """

    random = Utils.randomword(5)
    random_path = '/testp/' + random
    name = "Profile_name_is_" + random

    response = client.post(
        "/profiles?path=" + random_path,
        headers=HEADERS,
        json={
            "name": name,
        },
    )

    assert response.status_code == 201

    r = json.loads(response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    p_response = client.patch(
        "/profiles/" + r.id,
        headers=HEADERS,
        json={
            "name": "other " + name,
            "description": "new description",
        },
    )

    assert p_response.status_code == 200

    p = json.loads(p_response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    assert p.id == r.id
    assert p.name == "other " + name
    assert p.description == "new description"
    assert p.created_at is not None


def test_patch_profile_path(test_tables: None, client: TestClient):
    """Test case for patching the path of an existing profile

    Create a new profile, then performs a patch that changes the path
    """

    random = Utils.randomword(5)
    random_path = '/testp1/' + random
    dest_path = '/testp2/' + random
    name = "Profile_name_is_" + random

    response = client.post(
        "/profiles?path=" + random_path,
        headers=HEADERS,
        json={
            "name": name,
        },
    )

    assert response.status_code == 201

    r = json.loads(response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    p_response = client.patch(
        "/profiles/" + r.id,
        headers=HEADERS,
        json={
            "path": dest_path  # change the profile path
        },
    )

    assert p_response.status_code == 200

    p = json.loads(p_response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    assert p.id != r.id
    assert p.path == dest_path  # path is updated...

    profile_old_path = profile_service.get_profile_by_path(random_path)

    assert profile_old_path is None  # no profile at old path

    profile_dest_path = profile_service.get_profile_by_path(dest_path)

    assert profile_dest_path is not None  # profile present at dest path

    assert profile_dest_path.id == p.id  # is the expected new profile id
    assert profile_dest_path.path == dest_path

    # get effective profile at dest path and see if matches:

    g2_response = client.get(
        "/effective-profile?path=" + dest_path,
        headers=HEADERS,
    )

    assert g2_response.status_code == 200

    g2 = json.loads(g2_response.content,
                    object_hook=lambda d: SimpleNamespace(**d))

    assert g2.id == p.id  # id is kept (as the new id)
    assert g2.path == dest_path  # path is the new one


def test_patch_missing_profile(test_tables: None, client: TestClient):
    """Test case for patching a profile which does not exist

    Tests patching a profile which a name that does not exist
    """

    random = Utils.randomword(5)

    p_response = client.patch(
        "/profiles/" + random,
        headers=HEADERS,
        json={
            "name": "other 12121",
            "description": "new description xxxxx",
        },
    )

    assert p_response.status_code == 404


def test_add_comment_to_profile(test_tables: None, client: TestClient):
    """Test case for adding a comment to a profile

    Create a new profile, then add a comment, check the response
    """

    random = Utils.randomword(5)
    random_path = '/testc/' + random
    name = "Profile_name_is_" + random

    response = client.post(
        "/profiles?path=" + random_path,
        headers=HEADERS,
        json={
            "name": name,
            "description": "a short description",
        },
    )

    assert response.status_code == 201

    r = json.loads(response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    c_response = client.post(
        "/profiles/" + r.id + "/comments",
        headers=HEADERS,
        json={"comment": "this is a comment for " + r.name},
    )

    assert c_response.status_code == 201

    c = json.loads(c_response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    assert c.comment == "this is a comment for " + r.name
    assert c.created_by == "system"
    assert c.created_at is not None

    c2_response = client.post(
        "/profiles/" + r.id + "/comments",
        headers=HEADERS,
        json={"comment": "this is another comment for " + r.name},
    )

    assert c2_response.status_code == 201

    c2 = json.loads(c2_response.content,
                    object_hook=lambda d: SimpleNamespace(**d))

    assert c2.comment == "this is another comment for " + r.name
    assert c2.created_by == "system"
    assert c2.created_at is not None


def test_list_comments_of_profile(test_tables: None, client: TestClient):
    """Test case for listing the comments of a profile

    Create a new profile, then add a two comment, the get the likst and check the paginated response
    """

    random = Utils.randomword(5)
    random_path = '/test/' + random
    name = "Profile_name_is_" + random

    response = client.post(
        "/profiles?path=" + random_path,
        headers=HEADERS,
        json={
            "name": name,
            "description": "a short description",
        },
    )

    assert response.status_code == 201

    r = json.loads(response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    c_response = client.post(
        "/profiles/" + r.id + "/comments",
        headers=HEADERS,
        json={"comment": "this is a comment for " + r.name},
    )

    assert c_response.status_code == 201

    c2_response = client.post(
        "/profiles/" + r.id + "/comments",
        headers=HEADERS,
        json={"comment": "this is another comment for " + r.name},
    )

    assert c2_response.status_code == 201

    p_response = client.get("/profiles/" + r.id + "/comments",
                                      headers=HEADERS)

    assert p_response.status_code == 200

    p = json.loads(p_response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    assert p.navigation is not None
    assert p.navigation.page == 1
    assert p.navigation.pages == 1
    assert p.navigation.items == 2
    assert p.items is not None
    assert len(p.items) == p.navigation.items

    assert p.items[0].comment == "this is a comment for " + r.name
    assert p.items[1].comment == "this is another comment for " + r.name


def test_list_comments_of_missing_profile(test_tables: None,
                                          client: TestClient):
    """Test case for listing the comments of a profile that does not exist

    Attempt adding a comment to a non-existing profile
    """

    random = Utils.randomword(5)

    c_response = client.post(
        "/profiles/" + random + "/comments",
        headers=HEADERS,
        json={"comment": "this is a comment"},
    )

    assert c_response.status_code == 404


def test_add_comment_to_missing_profile(test_tables: None, client: TestClient):
    """Test case for adding a comment to a profile which does not exist"""

    random = Utils.randomword(5)

    c_response = client.post(
        "/profiles/" + random + "/comments",
        headers=HEADERS,
        json={"comment": "this is a comment too"},
    )

    assert c_response.status_code == 404

    c = json.loads(c_response.content,
                   object_hook=lambda d: SimpleNamespace(**d))

    assert c.detail == "Profile not found"
