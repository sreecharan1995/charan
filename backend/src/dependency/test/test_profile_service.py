# coding: utf-8

from typing import List, Optional

from common.utils import Utils
from dependency.api.model.full_profile_model import FullProfileModel
from dependency.api.model.new_profile_model import NewProfileModel
from dependency.api.model.package_reference_model import PackageReferenceModel
from dependency.api.model.profile_model import ProfileModel
from dependency.service.profile_service import ProfileService

profile_service = ProfileService()


def test_effective_packages(test_tables: None):

    # make sure there is no profile at parents

    profile_service.detach_from_path("/mumbai")
    profile_service.detach_from_path("/", force=True)

    random = Utils.randomword(5)

    new_root_profile = NewProfileModel(name="root", description="root profile")

    root_profile = profile_service.create_profile(
        new_profile=new_root_profile, path="/", operator=None
    )

    assert root_profile is not None

    root_profile_id = root_profile.id

    pk_refs = [
        {"name": "alabaster", "version": "0.7.12"},
    ]

    profile_service.set_profile_packages(
        profile_id=root_profile_id,
        pkr_list=list(map(lambda x: PackageReferenceModel(**x), pk_refs)),
    )

    random_path1 = f"/mumbai/{random}"

    new_profile1 = NewProfileModel(name="profile_1", description="desc of profile 1")

    profile1 = profile_service.create_profile(
        new_profile=new_profile1, path=random_path1, operator=None
    )

    assert profile1 is not None

    pk_refs1 = [
        {"name": "anyio", "version": "3.5.0"},
        {"name": "fastapi", "version": "0.73"},
        {"name": "sphinx", "version": "4.5.0"},
    ]

    profile_service.set_profile_packages(
        profile_id=profile1.id,
        pkr_list=list(map(lambda x: PackageReferenceModel(**x), pk_refs1)),
    )

    ep1: Optional[FullProfileModel] = profile_service.get_effective_profile_by_path(
        random_path1, exclude_deletions=True
    )

    assert ep1 is not None
    assert ep1.id == profile1.id
    assert len(ep1.packages) == len(pk_refs1) + 1  # one taken from root

    assert ep1.packages[0].name == "alabaster"
    assert ep1.packages[0].version == "0.7.12"
    assert ep1.packages[1].name == "anyio"
    assert ep1.packages[1].version == "3.5.0"
    assert ep1.packages[2].name == "fastapi"
    assert ep1.packages[2].version == "0.73"
    assert ep1.packages[3].name == "sphinx"
    assert ep1.packages[3].version == "4.5.0"

    random_path2 = f"/mumbai/{random}/d/c"

    new_profile2 = NewProfileModel(name="profile_2", description="desc of profile 2")

    profile2 = profile_service.create_profile(
        new_profile=new_profile2, path=random_path2, operator=None
    )

    assert profile2 is not None

    pk_refs2 = [
        {"name": "alabaster", "version": "0.7.17"},
        {"name": "anyio", "version": "3.5.1"},
        {"name": "sphinx", "version": "4.5.0"},
        {"name": "fastapi", "version": "0.75.1"},
    ]

    profile_service.set_profile_packages(
        profile_id=profile2.id,
        pkr_list=list(map(lambda x: PackageReferenceModel(**x), pk_refs2)),
    )

    profile_service.delete_profile_package(
        profile_id=profile2.id, package_name="sphinx"
    )  # mark a delete for sphinx from this child down

    ep2: Optional[FullProfileModel] = profile_service.get_effective_profile_by_path(
        random_path2, exclude_deletions=True
    )

    assert ep2 is not None
    assert ep2.id == profile2.id
    assert len(ep2.packages) == 3  # sphinx should not be present

    assert ep2.packages[0].name == "alabaster"
    assert ep2.packages[0].version == "0.7.17"
    assert ep2.packages[1].name == "anyio"
    assert ep2.packages[1].version == "3.5.1"
    assert ep2.packages[2].name == "fastapi"
    assert ep2.packages[2].version == "0.75.1"


def test_effective_bundles(test_tables: None):

    # make sure there is no profile at parents

    profile_service.detach_from_path("/toronto")
    profile_service.detach_from_path("/", force=True)

    random = Utils.randomword(5)

    new_root_profile = NewProfileModel(
        name="root_profile", description="desc of root profile"
    )

    root_profile = profile_service.create_profile(
        path="/",
        new_profile=new_root_profile, operator=None
    )

    assert root_profile is not None
    root_profile_id: str = root_profile.id

    root_bundle1_packages = [
        {"name": "alabaster", "version": "0.7.12"},
        {"name": "anyio", "version": "3.5.0"},
    ]

    root_bundle2_packages = [
        {"name": "sphinx", "version": "4.5.0"},
        {"name": "anyio", "version": "3.5.1"},
    ]

    profile_service.add_profile_bundle(
        profile_id=root_profile_id,
        bundle_name="bundle_1",
        bundle_description="desc1",
        pkr_list=[PackageReferenceModel(**x) for x in root_bundle1_packages],
        assume_bundle_in_library=True
    )

    profile_service.add_profile_bundle(
        profile_id=root_profile_id,
        bundle_name="bundle_2",
        bundle_description="desc2",
        pkr_list=[PackageReferenceModel(**x) for x in root_bundle2_packages],
        assume_bundle_in_library=True
    )

    r_profile = profile_service.get_profile(root_profile_id)

    # assert bundles and order in non-effective root profile
    assert len(r_profile.bundles) == 2
    assert r_profile.bundles[0].name == "bundle_1"
    assert r_profile.bundles[0].description == "desc1"
    assert r_profile.bundles[1].name == "bundle_2"
    assert r_profile.bundles[1].description == "desc2"

    toronto_path = f"/toronto"

    new_profile_toronto = NewProfileModel(
        name="profile_toronto", description="desc of profile toronto"
    )

    toronto_profile = profile_service.create_profile(
        new_profile=new_profile_toronto, path=toronto_path, operator=None
    )

    assert toronto_profile is not None

    toronto_profile_id = toronto_profile.id

    toronto_bundle1_packages = [
        {"name": "anyio", "version": "3.5.0"},
        {"name": "fastapi", "version": "0.73"},
        {"name": "sphinx", "version": "4.5.0"},
    ]

    toronto_bundle2_packages: List[dict[str, str]] = [
        {"name": "sphinx", "version": "4.5.0"}
    ]

    toronto_bundle3_packages = [
        {"name": "fastapi", "version": "0.75.1"},
    ]

    profile_service.add_profile_bundle(
        profile_id=toronto_profile_id,
        bundle_name="bundle_1",
        bundle_description="desc1",
        pkr_list=[PackageReferenceModel(**x) for x in toronto_bundle1_packages],
        assume_bundle_in_library=True,
        replace_allowed=True
    )

    profile_service.add_profile_bundle(
        profile_id=toronto_profile_id,
        bundle_name="bundle_2",
        bundle_description="desc2",
        pkr_list=[PackageReferenceModel(**x) for x in toronto_bundle2_packages],
        assume_bundle_in_library=True,
        replace_allowed=True
    )

    profile_service.add_profile_bundle(
        profile_id=toronto_profile_id,
        bundle_name="bundle_3",
        bundle_description="desc3",
        pkr_list=[PackageReferenceModel(**x) for x in toronto_bundle3_packages],
        assume_bundle_in_library=True
    )

    under_toronto_path = f"/toronto/{random}/x/y/z/{random}"

    new_profile_under_toronto = NewProfileModel(
        name="under_toronto", description="desc of profle under toronto"
    )

    under_toronto_profile = profile_service.create_profile(
        new_profile=new_profile_under_toronto, path=under_toronto_path, operator=None
    )

    assert under_toronto_profile is not None

    under_toronto_profile_id = under_toronto_profile.id

    under_toronto_bundle2_packages = [
        {"name": "fastapi", "version": "0.75.75"},
    ]

    under_toronto_bundle3_packages: List[dict[str, str]] = [
        {"name": "sphinx", "version": "4.5.0"}
    ]

    under_toronto_bundle4_packages = [
        {"name": "sphinx", "version": "4.5.0"},
    ]

    profile_service.add_profile_bundle(
        profile_id=under_toronto_profile_id,
        bundle_name="bundle_2",
        bundle_description="desc2",
        pkr_list=[PackageReferenceModel(**x) for x in under_toronto_bundle2_packages],
        assume_bundle_in_library=True,
        replace_allowed=True
    )

    profile_service.add_profile_bundle(
        profile_id=under_toronto_profile_id,
        bundle_name="bundle_3",
        bundle_description="desc3",
        pkr_list=[
            PackageReferenceModel(**x) for x in under_toronto_bundle3_packages
        ],  # xtype: ignore
        assume_bundle_in_library=True,
        replace_allowed=True
    )

    profile_service.add_profile_bundle(
        profile_id=under_toronto_profile_id,
        bundle_name="bundle_4",
        bundle_description="desc4",
        pkr_list=[PackageReferenceModel(**x) for x in under_toronto_bundle4_packages],
        assume_bundle_in_library=True
    )

    ep_r: Optional[FullProfileModel] = profile_service.get_effective_profile_by_path(
        "/", exclude_deletions=True
    )

    assert ep_r is not None
    assert len(ep_r.bundles) == 2

    assert ep_r.bundles[0].name == "bundle_1"
    assert len(ep_r.bundles[0].packages) == 2
    assert ep_r.bundles[0].packages[0].name == "alabaster"
    assert ep_r.bundles[0].packages[0].version == "0.7.12"
    assert ep_r.bundles[0].packages[1].name == "anyio"
    assert ep_r.bundles[0].packages[1].version == "3.5.0"

    assert ep_r.bundles[1].name == "bundle_2"
    assert len(ep_r.bundles[1].packages) == 2
    assert ep_r.bundles[1].packages[0].name == "sphinx"
    assert ep_r.bundles[1].packages[0].version == "4.5.0"
    assert ep_r.bundles[1].packages[1].name == "anyio"
    assert ep_r.bundles[1].packages[1].version == "3.5.1"

    ep_toronto: Optional[FullProfileModel] = profile_service.get_effective_profile_by_path(
        toronto_path, exclude_deletions=True
    )

    assert ep_toronto is not None
    assert len(ep_toronto.bundles) == 3

    assert ep_toronto.bundles[0].name == "bundle_1"
    assert len(ep_toronto.bundles[0].packages) == 3
    assert ep_toronto.bundles[0].packages[0].name == "anyio"
    assert ep_toronto.bundles[0].packages[0].version == "3.5.0"
    assert ep_toronto.bundles[0].packages[1].name == "fastapi"
    assert ep_toronto.bundles[0].packages[1].version == "0.73"
    assert ep_toronto.bundles[0].packages[2].name == "sphinx"
    assert ep_toronto.bundles[0].packages[2].version == "4.5.0"

    assert ep_toronto.bundles[1].name == "bundle_2"
    assert len(ep_toronto.bundles[1].packages) == 1
    assert ep_toronto.bundles[1].packages[0].name == "sphinx"
    assert ep_toronto.bundles[1].packages[0].version == "4.5.0"

    assert ep_toronto.bundles[2].name == "bundle_3"
    assert len(ep_toronto.bundles[2].packages) == 1
    assert ep_toronto.bundles[2].packages[0].name == "fastapi"
    assert ep_toronto.bundles[2].packages[0].version == "0.75.1"

    ep_under_toronto: Optional[
        FullProfileModel
    ] = profile_service.get_effective_profile_by_path(
        under_toronto_path, exclude_deletions=True
    )

    assert ep_under_toronto is not None
    assert len(ep_under_toronto.bundles) == 4

    assert ep_under_toronto.bundles[0].name == "bundle_1"
    assert len(ep_under_toronto.bundles[0].packages) == 3
    assert ep_under_toronto.bundles[0].packages[0].name == "anyio"
    assert ep_under_toronto.bundles[0].packages[0].version == "3.5.0"
    assert ep_under_toronto.bundles[0].packages[1].name == "fastapi"
    assert ep_under_toronto.bundles[0].packages[1].version == "0.73"
    assert ep_under_toronto.bundles[0].packages[2].name == "sphinx"
    assert ep_under_toronto.bundles[0].packages[2].version == "4.5.0"

    assert ep_under_toronto.bundles[1].name == "bundle_2"
    assert len(ep_under_toronto.bundles[1].packages) == 1
    assert ep_under_toronto.bundles[1].packages[0].name == "fastapi"
    assert ep_under_toronto.bundles[1].packages[0].version == "0.75.75"

    assert ep_under_toronto.bundles[2].name == "bundle_3"
    assert len(ep_under_toronto.bundles[2].packages) == 1
    assert ep_under_toronto.bundles[2].packages[0].name == "sphinx"
    assert ep_under_toronto.bundles[2].packages[0].version == "4.5.0"

    assert ep_under_toronto.bundles[3].name == "bundle_4"
    assert len(ep_under_toronto.bundles[3].packages) == 1
    assert ep_under_toronto.bundles[3].packages[0].name == "sphinx"
    assert ep_under_toronto.bundles[3].packages[0].version == "4.5.0"

def test_profiles_under_path(test_tables: None) -> None:
    
    random = Utils.randomword(6)
    
    profile_service.create_profile(f"/mumbai/{random}/a", NewProfileModel(name=f"{random}_a"), operator=None)
    profile_service.create_profile(f"/mumbai/{random}/c", NewProfileModel(name=f"{random}_c"), operator=None)
    profile_service.create_profile(f"/mumbai/{random}/c/d", NewProfileModel(name=f"{random}_c_d"), operator=None)
    profile_service.create_profile(f"/mumbai/{random}/c/d/x/y/z", NewProfileModel(name=f"{random}_c_d_x_y_z"), operator=None)
    profile_service.create_profile(f"/mumbai/{random}/c/e", NewProfileModel(name=f"{random}_c_e"), operator=None)
    profile_service.create_profile(f"/mumbai/{random}/c/e/f", NewProfileModel(name=f"{random}_c_e_f"), operator=None)

    profiles : List[ProfileModel] = profile_service.get_profiles_under_path(f"/mumbai/{random}/a")
    assert len(profiles) == 0   

    profiles : List[ProfileModel] = profile_service.get_profiles_under_path(f"/mumbai/{random}/c")
    assert len(profiles) == 4   

    profiles : List[ProfileModel] = profile_service.get_profiles_under_path(f"/mumbai/{random}/c/d")
    assert len(profiles) == 1

    profiles : List[ProfileModel] = profile_service.get_profiles_under_path(f"/mumbai/{random}/c/d/x/y")
    assert len(profiles) == 1

    profiles : List[ProfileModel] = profile_service.get_profiles_under_path(f"/mumbai/{random}/c/d/x/y/z")
    assert len(profiles) == 0

    profiles : List[ProfileModel] = profile_service.get_profiles_under_path(f"/mumbai/{random}/c/e")
    assert len(profiles) == 1

    profiles : List[ProfileModel] = profile_service.get_profiles_under_path(f"/mumbai/{random}/c/e/f")
    assert len(profiles) == 0

    profiles : List[ProfileModel] = profile_service.get_profiles_under_path(f"/mumbai/{random}/z/q/w/e")
    assert len(profiles) == 0
    



