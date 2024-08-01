# coding: utf-8

import threading
import xml.etree.ElementTree as ET
from typing import List, Optional, Tuple

from fastapi import HTTPException

from common.domain.level_path import LevelPath
from common.domain.status_exception import StatusException
from common.domain.user import User
from common.logger import log
from common.service.levels_remote_service import LevelsRemoteService
from common.utils import Utils
from dependency.api.model.bundle_model import BundleModel
from dependency.api.model.full_profile_model import FullProfileModel
from dependency.api.model.import_summary_model import (ImportReport,
                                                       InvalidBundle,
                                                       InvalidPackageReference)
from dependency.api.model.new_profile_comment_model import \
    NewProfileCommentModel
from dependency.api.model.new_profile_model import NewProfileModel
from dependency.api.model.package_reference_model import PackageReferenceModel
from dependency.api.model.patch_profile_model import PatchProfileModel
from dependency.api.model.profile_comment_model import ProfileCommentModel
from dependency.api.model.profile_model import (PROFILE_STATUS_PENDING,
                                                ProfileModel)
from dependency.dependency_settings import DependencySettings
from dependency.service.aws.dependency_ddb import DependencyDdb
from dependency.service.events_service import EventsService
from dependency.service.package_service import PackageService

settings = DependencySettings.load()

package_service: PackageService = PackageService(settings)
events_service: EventsService = EventsService(settings)
levels_service: LevelsRemoteService = LevelsRemoteService(settings)


# f = open(package_service.get_packages_filename())
# mock_packages = json.load(f)


class ProfileService:
    """Contains methods to list, search, create, edit profiles and to calculate effective profiles.

    An effective profile is a profile where its packages and bundles may be inherited from one or several profilesattached to ancestors in the hierarchy of levels.
    """

    _settings: DependencySettings
    _ddb: DependencyDdb

    def __init__(self, settings: DependencySettings = DependencySettings.load()):

        self._settings = settings
        self._ddb = DependencyDdb(settings)

    def get_profile(self, profile_id: str) -> FullProfileModel:

        profile = (
            self._ddb.find_profile_db(profile_id) if profile_id is not None else None
        )

        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        return profile

    def change_profile_status(self, profile_id: str, validation_result: str, result_reason: Optional[str],
                              rxt: Optional[str]) -> None:
        if validation_result is None:
            return

        self._ddb.change_profile_status_db(profile_id=profile_id, validation_result=validation_result,
                                          result_reason=result_reason, rxt=rxt, check_exist=True)

    def get_effective_profile(
            self, profile_id: str, exclude_deletions: bool = False
    ) -> FullProfileModel:

        profile = (
            self._ddb.find_profile_db(profile_id) if profile_id is not None else None
        )

        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        e_profile = self._get_effective_profile_at_path(profile.path)

        if e_profile is None or e_profile.id != profile_id:
            raise HTTPException(
                status_code=404, detail="Profile not found at expected path"
            )

        if exclude_deletions:
            e_profile.packages = list(
                filter(lambda p: not p.is_deleted(), e_profile.packages)
            )
            e_profile.bundles = list(
                filter(lambda b: not b.is_empty(), e_profile.bundles)
            )

        return e_profile

    def get_effective_profile_by_path(
            self, path: str, exclude_deletions: bool = False
    ) -> FullProfileModel:

        e_profile = self._get_effective_profile_at_path(path)

        if e_profile is None:
            raise HTTPException(
                status_code=404, detail="Profile not found at path: " + path
            )

        if exclude_deletions:
            e_profile.packages = list(
                filter(lambda p: not p.is_deleted(), e_profile.packages)
            )
            e_profile.bundles = list(
                filter(lambda b: not b.is_empty(), e_profile.bundles)
            )

        return e_profile

    def list_profiles(self, p: int, ps: int, q: str) -> Tuple[List[ProfileModel], int]:
        items, total = self._ddb.list_profiles_db(p, ps, q)

        profiles: List[ProfileModel] = list(map(lambda x: ProfileModel(**x), items))  # type: ignore
        return profiles, total

    def detach_from_path(self, path: str, force: bool = False) -> List[ProfileModel]:

        if path is None:
            return []

        if not force and (path.strip() == "" or path.strip() == "/"):
            raise HTTPException(
                status_code=400, detail="Unable to delete the root profile"
            )

        deleted = self._ddb.delete_profiles_by_path_db(path)

        self._on_path_changed_by_profile(path, profile_deleted=True)

        return deleted

    def create_profile(self, path: str, new_profile: NewProfileModel, operator: Optional[User]):

        if new_profile is None:
            raise HTTPException(status_code=422, detail="Empty body")

        path = LevelPath.canonize(path)

        if not levels_service.is_visible(path=path, token=operator.token if operator is not None else None):
            raise HTTPException(
                status_code=400, detail="Level not found at path"
            )

        profile_at_path: Optional[FullProfileModel] = self.get_profile_by_path(path)

        if profile_at_path is not None:
            raise HTTPException(
                status_code=409,
                detail="There is already a profile attached to path " + path,
            )
        
        profile_id: str = Utils.derive_profile_id_from_path(path)

        profile = self._ddb.find_profile_db(profile_id) # find if there is one already

        if profile is not None:
            raise HTTPException(
                status_code=409, detail="A profile with the same id already exist"
            )

        response = self._ddb.create_profile_db(path, new_profile, user=operator)

        self._on_path_changed_by_profile(path)

        return response

    def get_profile_by_path(self, path: str) -> Optional[FullProfileModel]:
        profiles = self._get_profiles_by_path(path)
        return profiles[0] if len(profiles) > 0 else None

    def _get_profiles_by_path(self, path: str) -> List[FullProfileModel]:
        if path is None:
            return []        

        return self._ddb.find_profiles_by_path_db(path)

    def get_profiles_under_path(self, path: str) -> List[ProfileModel]:
        if path is None:
            return []

        return self._ddb.find_profiles_under_path_db(path)

    # internal recursive:
    def _get_effective_profile_at_path(self, path: str = "/") -> Optional[FullProfileModel]:

        path = "/" if path == "" else path

        p_at_path = self.get_profile_by_path(path)

        # if path == "/" and p_at_path is None:
        #     raise HTTPException(status_code=404, detail="Root profile not found")

        if (
                path == "/"
        ):  # if current path is root then this is the (top) effective profile
            return p_at_path

        parent_path = path[0: path.rfind("/")]

        ep_parent = self._get_effective_profile_at_path(
            parent_path
        )  # effective profile at parent path

        if (
                p_at_path is None
        ):  # if no profile at path then use parent as the effective, unless there is no effective in parent (empty
            # ancestors)
            return ep_parent if ep_parent is not None else None

        l_id = p_at_path.id if p_at_path is not None else "root"
        l_name = p_at_path.name if p_at_path is not None else "root"
        l_desc = p_at_path.description if p_at_path is not None else ""
        l_created_at = p_at_path.created_at if p_at_path is not None else ""
        l_created_by = p_at_path.created_by if p_at_path is not None else ""
        l_status = (
            p_at_path.profile_status
            if p_at_path is not None
            else ep_parent.profile_status
            if ep_parent is not None
            else PROFILE_STATUS_PENDING
        )

        ep = FullProfileModel(
            name=l_name,
            description=l_desc,
            id=l_id,
            created_at=l_created_at,
            created_by=l_created_by,
            path=path,
            profile_status=l_status,
        )  # effective at current

        # using ep_parent as base, calculate overrides in p_at_path, and leave effective calc at ep

        ep.packages = list(
            ep_parent.packages if ep_parent is not None else []
        )  # start using the effective parent packages

        p_to_exclude: List[str] = []

        for p in p_at_path.packages:
            p_found: Optional[PackageReferenceModel] = next(
                filter(lambda xep: xep.name == p.name, ep.packages), None
            )
            if p_found is None:
                ep.packages.append(p)
            elif p.name is not None and p.version is not None:
                if p.version.strip() == "!":
                    p_to_exclude.append(p.name)
                elif p.version.strip() != "":
                    p_found.version = p.version

        ep.packages = list(filter(lambda n: n.name not in p_to_exclude, ep.packages))
        ep.bundles = []

        for b in ep_parent.bundles if ep_parent is not None else []:
            b_found: Optional[BundleModel] = next(
                filter(lambda xb: xb.name == b.name, p_at_path.bundles), None
            )  # found at child
            if b_found is not None:  # when found in child, use it
                ep.bundles.append(b_found)
            else:  # when not in child use the one in parent
                ep.bundles.append(b)

        for b in p_at_path.bundles:  # add bundles in child, not found in parent
            b_found2: Optional[BundleModel] = next(
                filter(lambda xb: xb.name == b.name, ep.bundles), None
            )  # already in effective bundles
            if b_found2 is None:  # when not already considered, add
                ep.bundles.append(b)

        # ep.bundles = list(ep_parent.bundles if ep_parent is not None else [])
        # for b in p_at_path.bundles:
        #  b_found : Optional[Bundle] = next(filter(lambda xb: xb.name == b.name, ep.bundles), None) # found at parent
        #  if b_found is None:
        #     ep.bundles.append(b) # add the bundle
        #  else:
        #     b_found.packages = b.packages # set new package list to already found bundle

        return ep

    def patch_profile(self, profile_id: str, patch_profile: PatchProfileModel, user: User) -> ProfileModel:

        profile = self._ddb.find_profile_db(profile_id)

        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        if patch_profile is None:
            raise HTTPException(status_code=400, detail="Bad request")

        patch_profile.name = patch_profile.name or profile.name

        patch_profile.description = patch_profile.description or profile.description

        patch_profile.path = patch_profile.path or profile.path

        old_path = LevelPath.canonize(profile.path)
        new_path = LevelPath.canonize(patch_profile.path)

        path_changed: bool = old_path != new_path

        if not path_changed:

            profile = self._ddb.patch_profile_db(profile_id, patch_profile.name, patch_profile.description)

            if profile is None:
                raise HTTPException(status_code=404, detail="Profile not found")
            
            return profile
        
        else: # if path do changed:
             
            if not levels_service.is_visible(new_path, user.token):
                raise HTTPException(status_code=409, detail=f"Target path not found: {new_path}")    
             
            old_path = profile.path

            new_profile_model: NewProfileModel = NewProfileModel(name=patch_profile.name, description=patch_profile.description)

            try:
                new_profile = self._ddb.create_profile_db(path=new_path, new_profile=new_profile_model, pkr_list=profile.packages, bundle_list=profile.bundles, user=user)
            except StatusException as se:                
                raise HTTPException(status_code=se.code, detail=se.message)
                
            if new_profile is None:
                raise HTTPException(status_code=500, detail="Failed to create profile at new path")
                    
            # delete old profile and return the new one
            try:
                self._ddb.delete_profile_db(profile_id=profile_id)
            except BaseException as be:
                log.error(f"Unable to delete profile {profile_id} at previous path {old_path}. {be}")

            if new_path.startswith(
                    old_path + '/'):  # if new path is descendant of the old, trigger from old_path only:
                self._on_path_changed_by_profile(path=old_path, profile_deleted=True)
            elif old_path.startswith(
                    new_path + '/'):  # if old path is descendant of the new, trigger from new_path only:
                self._on_path_changed_by_profile(path=new_path)
            else:  # if path are not one above the other, trigger for both affected branches:
                self._on_path_changed_by_profile(path=old_path, profile_deleted=True)
                self._on_path_changed_by_profile(path=new_path)

            return new_profile

    def set_profile_packages(
            self, profile_id: str, pkr_list: List[PackageReferenceModel]
    ) -> List[PackageReferenceModel]:

        profile = self._ddb.find_profile_db(profile_id)

        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        if pkr_list is None:
            raise HTTPException(status_code=400, detail="Bad request")

        self.error_if_any_package_ref_invalid(pkr_list)

        packages = self._ddb.set_profile_packages_db(profile_id, pkr_list)

        self._on_path_changed_by_profile(profile.path)

        return packages

    def delete_profile_package(self, profile_id: str, package_name: str) -> None:

        profile = self._ddb.find_profile_db(profile_id)

        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        if package_name is None:
            raise HTTPException(status_code=400, detail="Bad request")

        e_profile: Optional[FullProfileModel] = self._get_effective_profile_at_path(
            profile.path
        )

        if e_profile is None or e_profile.id != profile_id:  # just in case
            raise HTTPException(
                status_code=404, detail="Profile not found at expected path"
            )

        found_ref_p: Optional[PackageReferenceModel] = next(
            filter(lambda p: p.name == package_name, profile.packages), None
        )  # search package name in profile
        found_ref_ep: Optional[PackageReferenceModel] = next(
            filter(lambda p: p.name == package_name, e_profile.packages), None
        )  # search package name in effective profile

        if (
                found_ref_ep is None
        ):  # if not in the effective profile then its also not on the profile:
            raise HTTPException(status_code=404, detail="Package not found")
        elif found_ref_ep.is_deleted():  # already marked deleted
            return None
        else:  # not deleted:
            if found_ref_p is None:  # inherited:
                profile.packages.append(
                    PackageReferenceModel(name=package_name, version="!")
                )  # add to profile packages as deleted
            else:  # local:
                found_ref_p.mark_deleted()  # replace version with deleted mark

        self._ddb.set_profile_packages_db(
            profile_id, profile.packages
        )  # set the updated package list in the profile

        self._on_path_changed_by_profile(profile.path)

    def error_if_any_package_ref_invalid(self, pk_ref_list: List[PackageReferenceModel]):

        if pk_ref_list is None or len(pk_ref_list) == 0:
            raise HTTPException(
                status_code=422,
                detail=f"the package list is missing or empty",
            )

        for p in pk_ref_list:
            if p.name is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"a referenced package is missing the package name attribute",
                )
            elif p.name.strip() == "":
                raise HTTPException(
                    status_code=422,
                    detail=f"a referenced package has empty package name attribute",
                )
            if p.version is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"a referenced package is missing the package version attribute",
                )
            elif p.version.strip() == "":
                raise HTTPException(
                    status_code=422,
                    detail=f"a referenced package has empty package version attribute",
                )
            elif p.version.strip() == "!":
                raise HTTPException(
                    status_code=422,
                    detail=f"a referenced package version can't be '!'",
                )

                # check package is not duplicated
        names = list(map(lambda n: n.name, pk_ref_list))
        dups = [x for x in names if names.count(x) > 1]

        if len(dups) > 0:
            raise HTTPException(
                status_code=422,
                detail=f"there are multiple references to a same package name for {dups}",
            )

        # check package exists
        # for p in pk_ref_list:
        #     if not package_service.exists(p.name or "", p.version or ""):
        #         raise HTTPException(
        #             status_code=422,
        #             detail=f"referenced package is unknown. name: {p.name}, version: {p.version}",
        #         )

    def add_profile_bundle(
            self,
            profile_id: str,
            bundle_name: str,
            bundle_description: str,
            pkr_list: List[PackageReferenceModel],
            assume_bundle_in_library: bool = False,
            replace_allowed: bool = False,
    ) -> Optional[BundleModel]:

        profile = self._ddb.find_profile_db(profile_id)

        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        if bundle_name is None or bundle_name.strip() == "":
            raise HTTPException(status_code=422, detail="Bundle name empty or missing")

        if pkr_list is None:
            raise HTTPException(status_code=400, detail="Bad request")

        e_profile: Optional[FullProfileModel] = self._get_effective_profile_at_path(
            profile.path
        )

        if e_profile is None or e_profile.id != profile_id:  # just in case
            raise HTTPException(
                status_code=404, detail="Profile not found at expected path"
            )

        self.error_if_any_package_ref_invalid(pkr_list)

        library_bundle: Optional[BundleModel] = (
            BundleModel(name=bundle_name, description=bundle_description, packages=pkr_list)
            if assume_bundle_in_library
            else self._ddb.find_bundle_db(bundle_name)
        )

        found_ref_p: Optional[BundleModel] = next(
            filter(lambda b: b.name == bundle_name, profile.bundles), None
        )  # search bundle name in profile
        found_ref_ep: Optional[BundleModel] = next(
            filter(lambda b: b.name == bundle_name, e_profile.bundles), None
        )  # search bundle name in effective profile

        if (
                found_ref_ep is None
        ):  # if not in the effective profile then its also not on the profile, so we can add in principle:
            if library_bundle is None:  # if not in bundles library
                raise HTTPException(
                    status_code=404,
                    detail=f"Bundle '{bundle_name}' missing from library",
                )
            else:
                if library_bundle.packages_match(pkr_list):  # has same packages
                    profile.bundles.append(
                        BundleModel(
                            name=library_bundle.name, description=library_bundle.description, packages=library_bundle.packages
                        )
                    )  # add library bundle to profile
                else:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Attempting to re-attach bundle '{bundle_name}' to profile with a package set not matching the one on library",
                    )
        elif (
                found_ref_ep.is_empty()
        ):  # exists locally or inherited and its empty (deleted):
            # if previously used, lets assume already in library.
            if found_ref_p is None:  # inherited empty:
                profile.bundles.append(
                    BundleModel(name=bundle_name, description=bundle_description, packages=pkr_list)
                )  # re-add undeleted, as is given
            else:  # locally empty:
                found_ref_p.packages = pkr_list  # re-use locally deleted and set new package list as is given
        else:  # exists and is not empty:
            if not found_ref_ep.packages_match(pkr_list):  # differents package set:
                if replace_allowed:
                    if (
                            found_ref_p is None
                    ):  # if inherited, add locally to override inherited:
                        profile.bundles.append(
                            BundleModel(name=bundle_name, description=bundle_description, packages=pkr_list)
                        )  # add to override
                    else:  # if local, replace locally:
                        found_ref_p.packages = pkr_list
                else:
                    raise HTTPException(
                        status_code=409,
                        detail="Bundle with the same name and different package set already in profile",
                    )
            else:
                raise HTTPException(
                        status_code=409,
                        detail="Bundle already in profile",
                    )
                #  return found_ref_ep  # ignore: already present (in local or inherited) and identical

        bundle: Optional[BundleModel] = self._ddb.set_profile_bundle_packages_db(
            profile_id, bundle_name, profile.bundles
        )  # set the updated bundles list in the profile

        self._on_path_changed_by_profile(profile.path)

        return bundle

    # def update_profile_bundle_packages(
    #     self, profile_id: str, bundle_name: str, pkr_list: List[PackageReference]
    # ) -> Optional[Bundle]:

    #     profile = self.ddb.find_profile_db(profile_id)

    #     if profile == None:
    #         raise HTTPException(status_code=404, detail="Profile not found")

    #     if pkr_list is None:
    #         raise HTTPException(status_code=400, detail="Bad request")

    #     bundles = profile.bundles or []

    #     # find bundle with same name, if not found then raise error (unable to update)
    #     b = next(filter(lambda x: x.name == bundle_name, bundles), None)

    #     self.error_if_any_package_ref_invalid(pkr_list)

    #     packages = list(map(lambda p: {"name": p.name, "version": p.version}, pkr_list))

    #     if b is None:
    #         raise HTTPException(
    #             status_code=404,
    #             detail="Profile does not contains a bundle using that name",
    #         )

    #     b.packages = list(map(lambda p: PackageReference(**p), packages))

    #     bundle = self.ddb.set_profile_bundle_packages_db(
    #         profile_id, bundle_name, bundles
    #     )

    #     self.on_path_changed_by_profile_updated(profile.path)

    #     return bundle

    def delete_profile_bundle(self, profile_id: str, bundle_name: str) -> None:

        profile = self._ddb.find_profile_db(profile_id)

        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        if bundle_name is None:
            raise HTTPException(status_code=400, detail="Bad request")

        e_profile: Optional[FullProfileModel] = self._get_effective_profile_at_path(
            profile.path
        )

        if e_profile is None or e_profile.id != profile_id:  # just in case
            raise HTTPException(
                status_code=404, detail="Profile not found at expected path"
            )

        found_ref_p: Optional[BundleModel] = next(
            filter(lambda b: b.name == bundle_name, profile.bundles), None
        )  # search bundle name in profile
        found_ref_ep: Optional[BundleModel] = next(
            filter(lambda b: b.name == bundle_name, e_profile.bundles), None
        )  # search bundle name in effective profile

        if (
                found_ref_ep is None
        ):  # if not in the effective profile then its also not on the profile:
            raise HTTPException(status_code=404, detail="Bundle not found")
        elif found_ref_ep.is_empty():  # already marked empty (deleted)
            return None
        else:  # not empty (not deleted):
            if found_ref_p is None:  # inherited:
                profile.bundles.append(
                    BundleModel(name=bundle_name, packages=[])
                )  # add to profile bundle empty (deleted)
            else:  # local:
                found_ref_p.packages = (
                    []
                )  # set empty packages list, to mark as "deleted"

        self._ddb.set_profile_bundle_packages_db(
            profile_id, bundle_name, profile.bundles
        )  # set the updated bundles list in the profile

        self._on_path_changed_by_profile(profile.path)

    def add_profile_comment(
            self, profile_id: str, new_profile_comment: NewProfileCommentModel
    ) -> ProfileCommentModel:

        profile_comment = self._ddb.add_profile_comment_db(
            profile_id, new_profile_comment
        )

        if profile_comment is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        return profile_comment

    def list_profile_comments(
            self, profile_id: str, p: int, ps: int
    ) -> Tuple[Optional[List[ProfileCommentModel]], Optional[int]]:

        t = self._ddb.find_profile_comments_db(profile_id, p, ps) or None

        if t is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        return t

    def delete_profile(self, profile_id: str):

        profile = self._ddb.find_profile_db(profile_id)

        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")

        if profile.path.strip() == "" or profile.path.strip() == "/":
            raise HTTPException(
                status_code=400, detail="Unable to delete the root profile"
            )

        response = self._ddb.delete_profile_db(profile_id)

        self._on_path_changed_by_profile(profile.path, profile_deleted=True)

        return response

    def import_profile(
            self, operator_user: User, path: str, xml: bytes, replace: bool = False, strict: bool = False
    ) -> ImportReport:

        path = LevelPath.canonize(path)

        if not levels_service.is_visible(path, operator_user.token):
            raise HTTPException(
                status_code=409,
                detail="Level not found at path " + path,
            )

        profile_at_path: Optional[ProfileModel] = self.get_profile_by_path(path)

        if path != '/':
            e_profile_at_path: Optional[ProfileModel] = self._get_effective_profile_at_path(path)
        else:
            e_profile_at_path = None  # no effective (local is the root)

        if not replace and profile_at_path is not None:
            raise HTTPException(
                status_code=409,
                detail="There is already a profile attached to path " + path,
            )

        if replace and profile_at_path is None:
            raise HTTPException(
                status_code=409,
                detail="There is no profile currently attached to path " + path,
            )

        pc = ET.fromstring(xml)

        if pc is None or pc.tag != "package_configuration":
            raise HTTPException(
                status_code=422,
                detail="xml document contains no <package_configuration> node",
            )

        ver: str = pc.get("version") or ""
        if ver.strip() == "":
            raise HTTPException(
                status_code=422,
                detail="xml document contains <package_configuration> node with a missing/empty version attribute",
            )

        if ver.strip() != "1":
            raise HTTPException(
                status_code=422,
                detail="xml document <package_configuration> node refers to an unknown version in its version attribute",
            )

        profiles = pc.iterfind("profile")

        p = next(profiles, None)

        if p is None:
            raise HTTPException(
                status_code=422, detail="xml document contains no <profile> node"
            )

        p_name = p.attrib.get("name")

        if p_name is None or p_name.strip() == "":
            raise HTTPException(
                status_code=422,
                detail="xml document contains a profile <profile> node with a missing or empty attribute 'name'",
            )

        p_name = p_name.strip()

        import_report: ImportReport = ImportReport()

        import_report.summary.profileName = p_name

        if next(profiles, None) is not None:
            issue: str = "doc has more than one <profile> node, ignoring others"
            log.info(issue)
            import_report.errors.append(issue)

        log.info(f"profile[{p_name}]: parsing")

        packages = p.iterfind("package")

        pkref_list: List[PackageReferenceModel] = []
        full_pkref_list: List[PackageReferenceModel] = []

        pk_count = 0
        for pk in packages:
            pk_name = pk.attrib.get("name")
            pk_version = pk.attrib.get("version")
            if pk_name is None or pk_name.strip() == "":
                issue = "package ref has no name"
                log.info(f"profile[{p_name}]: {issue}")
                import_report.packages.ignored.append(issue)
                continue
            pk_name = pk_name.strip()
            if pk_version is None or pk_version.strip() == "":
                issue = f"package ref to '{pk_name}' has no version set"
                log.info(f"profile[{p_name}]: {issue}")
                import_report.packages.ignored.append(issue)
                continue
            pk_version = pk_version.strip()

            found_ep_ref = next(filter(lambda p: p.name == pk_name, e_profile_at_path.packages),
                                None) if e_profile_at_path else None
            # found_p_ref = next(filter(lambda p: p.name == pk_name, profile_at_path.packages), None) if
            # profile_at_path else None

            skip_override = False

            if found_ep_ref and found_ep_ref.version == pk_version:  # ignore if already in effective (local or inherited) -- not checking actual existence
                msg = f"profile[{p_name}]: detected a package+version already referenced, skipping override. name '{pk_name}', version: '{pk_version}'"
                log.info(msg)
                import_report.packages.previous.append(found_ep_ref)
                skip_override = True
            else:
                if not package_service.exists(pk_name, pk_version):
                    issue = f"missing package, name: '{pk_name}', version: '{pk_version}'"
                    log.info(f"profile[{p_name}]: {issue}")
                    import_report.packages.missed.append(
                        InvalidPackageReference(name=pk_name, version=pk_version, issue=issue))
                    continue

            pk_count = pk_count + 1
            log.info(f"profile[{p_name}].package[{pk_name},{pk_version}]")

            pk_ref = PackageReferenceModel(name=pk_name, version=pk_version)

            full_pkref_list.append(
                pk_ref)  # add to list to all valid packages, some of them may not be added to the local profile
            import_report.packages.included.append(pk_ref)

            if not skip_override:
                pkref_list.append(pk_ref)  # add to list wich will be actually set in profile

        log.info(f"profile[{p_name}].packages = {pk_count}")

        bundle_list: List[BundleModel] = []

        bundles = p.iterfind("bundle")

        b_names: List[str] = []

        b_count = 0
        for pb in bundles:
            pb_name = pb.attrib.get("name")

            if pb_name is None or pb_name.strip() == "":
                issue = f"profile has bundle with no name"
                log.info(f"profile[{p_name}]: {issue}")
                import_report.bundles.ignored.append(issue)
                continue

            pb_name = pb_name.strip()

            bundle_pkref_list: List[PackageReferenceModel] = []
            bundle_packages = list(pb.iterfind("package") or [])

            package_candidates = list(map(lambda p: InvalidPackageReference(name=p.attrib.get("name") or None,
                                                                            version=p.attrib.get("version") or None,
                                                                            issue=None), bundle_packages))

            if pb_name in b_names:
                issue = f"found a previous bundle using same name '{pb_name}'"
                log.info(f"profile[{p_name}]: {issue}")
                import_report.bundles.missed.append(
                    InvalidBundle(name=pb_name, packages=package_candidates, issue=issue))
                continue

            log.info(f"profile[{p_name}].bundle[{pb_name}]: parsing")

            if len(bundle_packages) == 0:
                issue = f"bundle '{pb_name}' has missing or empty package ref list"
                log.info(f"profile[{p_name}].bundle[{pb_name}]: {issue}")
                import_report.bundles.ignored.append(issue)
                bp_count = -1
            else:
                bp_count = 0
                for bp in bundle_packages:
                    bp_name = bp.attrib.get("name")
                    bp_version = bp.attrib.get("version")

                    if bp_name is None or bp_name.strip() == "":
                        issue = f"bundle '{pb_name}' has a package ref with no name"
                        log.info(f"profile[{p_name}].bundle[{pb_name}]: {issue}")
                        import_report.bundles.ignored.append(issue)
                        bp_count = -1
                        break

                    if bp_version is None or bp_version.strip() == "":
                        listed_package = next(filter(lambda p: p.name == bp_name, full_pkref_list), None)
                        if listed_package is None:
                            issue = f"package ref to '{bp_name}' with no usable version"
                            log.info(f"profile[{p_name}].bundle[{pb_name}]: {issue}")
                            import_report.bundles.missed.append(
                                InvalidBundle(name=pb_name, packages=package_candidates, issue=issue))
                            bp_count = -1
                            break
                        else:
                            bp_version = listed_package.version
                            msg = f"profile[{p_name}].bundle[{pb_name}]: package ref to '{bp_name}': version resolved to {listed_package.version}"
                            log.info(msg)

                    bp_name = bp_name.strip()
                    bp_version = bp_version.strip() if bp_version is not None else ''

                    if not package_service.exists(bp_name, bp_version):
                        issue = f"missing package ref to name: '{bp_name}', version: '{bp_version}'"
                        log.info(f"profile[{p_name}].bundle[{pb_name}]: {issue}")
                        import_report.bundles.missed.append(
                            InvalidBundle(name=pb_name, packages=package_candidates, issue=issue))
                        bp_count = -1
                        break

                    bp_count = bp_count + 1

                    log.info(
                        f"profile[{p_name}].bundle[{pb_name}].package[{bp_name},{bp_version}]"
                    )

                    bundle_pkref_list.append(
                        PackageReferenceModel(name=bp_name, version=bp_version)
                    )

            if bp_count != -1:
                b = BundleModel(name=pb_name, packages=bundle_pkref_list)
                library_bundle: Optional[BundleModel] = self._ddb.find_bundle_db(pb_name)

                bundle_import_failed: bool = False
                if library_bundle is None:  # import into library
                    try:
                        library_bundle = self._ddb.create_bundle_db(b)
                        log.info(f"profile[{p_name}].bundle[{pb_name}]: imported into library")
                        import_report.bundles.imported.append(b)
                    except:
                        issue = f"failed to be imported into library"
                        log.info(f"profile[{p_name}].bundle[{pb_name}]: {issue}")
                        import_report.bundles.missed.append(
                            InvalidBundle(name=pb_name, packages=package_candidates, issue=issue))
                        bundle_import_failed = True

                if not bundle_import_failed and library_bundle is not None:
                    if library_bundle.packages_match(b.packages):  # same packages? then may be used
                        log.info(f"profile[{p_name}].bundle[{pb_name}]: matches the one in library")
                        found_ep_bundle = next(filter(lambda b: b.name == pb_name, e_profile_at_path.bundles),
                                               None) if e_profile_at_path is not None else None
                        found_p_bundle = next(filter(lambda b: b.name == pb_name, profile_at_path.bundles),
                                              None) if profile_at_path is not None else None

                        if found_ep_bundle is not None and found_p_bundle is None:  # is inherited:
                            if found_ep_bundle.packages_match(b.packages):  # no need to append, inherited matches
                                log.info(f"profile[{p_name}].bundle[{pb_name}]: already inherited (and matches)")
                                import_report.bundles.previous.append(b)
                            else:  # the one inherited does not match the incoming
                                bundle_list.append(
                                    b)  # append because is different from inherited
                        else:  # not inherited, then append
                            bundle_list.append(b)  # append only if needed (if not inherited)

                        import_report.bundles.included.append(b)
                        b_names.append(pb_name)
                        b_count = b_count + 1  # count as included...
                        log.info(f"profile[{p_name}].bundle[{pb_name}].packages = {bp_count}")

                    else:  # different package set compared to the one in the library, complain:
                        issue = "package ref list differs from the one in the library"
                        log.info(f"profile[{p_name}].bundle[{pb_name}]: {issue}")
                        import_report.bundles.missed.append(
                            InvalidBundle(name=pb_name, packages=package_candidates, issue=issue))

        log.info(f"profile[{p_name}].bundles = {b_count}")

        if pk_count == 0 and b_count == 0:
            issue = f"profile is empty"
            log.info(f"profile[{p_name}]: {issue}")
            import_report.errors.append(issue)
        
        new_profile = NewProfileModel(
            name=p_name,
            description="imported from xml without issues"
            if not import_report.has_issues()
            else f"imported from xml, but had issues",
        )

        if import_report.has_issues() and strict:
            issue = f"profile[{p_name}]: has issues, not importing as strict mode was requested"
            log.info(issue)
            import_report.errors.append(issue)
            import_report.count()
            return import_report

        # TODO: this will briefly create two profiles at path, until next statements deletes the previous (is it better to have zero instead of two?)
        profile: Optional[FullProfileModel] = self._ddb.create_profile_db(
            path, new_profile, pkref_list, bundle_list, user=operator_user
        )

        if (
                profile_at_path is not None and replace
        ):  # delete previous if it is a replacement profile
            self._ddb.delete_profile_db(profile_at_path.id)

        self._on_path_changed_by_profile(path)

        if profile is not None:
            profile.packages = full_pkref_list or []

        import_report.count()
        return import_report

    def _update_descendent_profiles(self, descendent_profiles: List[ProfileModel]):
        if descendent_profiles is None:
            return

        for p in descendent_profiles:
            if self._ddb.change_profile_status_db(p.id, PROFILE_STATUS_PENDING, check_exist=False):
                events_service.on_profile_validate(
                    self._get_effective_profile_at_path(LevelPath.canonize(p.path))
                )

        return

    def _request_descendants_validation(self, path: str):
        log.debug(f"Starting descendants validation for path: {path}")
        descendent_profiles = self.get_profiles_under_path(path)
        self._update_descendent_profiles(descendent_profiles)
        log.debug(f"Finishing descendants validation for path: {path}")
        return

    def _on_path_changed_by_profile(self, path: str, profile_deleted: bool = False):

        if not profile_deleted:
            events_service.on_profile_validate(
                self._get_effective_profile_at_path(LevelPath.canonize(path))
            )

        if self._settings.DEP_SKIP_DESCENDANT_UPDATES:
            return

        # exec descendant profiles validation requests in thread
        log.info(f"Requesting validation for profiles under path: {path}")
        t = threading.Thread(target=self._request_descendants_validation, args=(path))
        t.start()

        return
