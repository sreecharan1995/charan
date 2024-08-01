# coding: utf-8

from typing import List, Optional, Tuple

from fastapi import HTTPException

from dependency.api.model.bundle_model import BundleModel
from dependency.api.model.package_reference_model import PackageReferenceModel
from dependency.dependency_settings import DependencySettings
from dependency.service.aws.dependency_ddb import DependencyDdb
from dependency.service.package_service import PackageService
from dependency.service.profile_service import ProfileService

package_service = PackageService()
profile_service = ProfileService()


class BundleService:
    """Methods used internally to access, create or modify bundles.

    Bundles are stored in a "library of bundles" and are later accesible by name when associating them with profiles.
    """

    _settings: DependencySettings
    _ddb: DependencyDdb

    def __init__(self, settings: DependencySettings = DependencySettings.load()):
        # self.directory_path = pathlib.Path(__file__).parent.absolute().parent
        # f = open(self.directory_path.as_posix() + '/mocks/bundles.json')
        # self.bundles = json.load(f)

        self._settings = settings
        self._ddb = DependencyDdb(settings)

    def get_bundle(self, name: str) -> BundleModel:
        bundle = self._ddb.find_bundle_db(name)
        if bundle is None:
            raise HTTPException(status_code=404, detail="Bundle not found")
        return bundle

    def list_bundles(self, p: int, ps: int, q: Optional[str]) -> Tuple[List[BundleModel], int]:
        return self._ddb.list_bundles_db(p, ps, q)

    def delete_bundle(self, name: str) -> BundleModel:
        bundle = self._ddb.find_bundle_db(name)
        if bundle is None:
            raise HTTPException(status_code=404, detail="Bundle not found")
        return self._ddb.delete_bundle_db(name)

    def update_bundle_packages(self, bundle_name: str, pkr_list: List[PackageReferenceModel]) -> BundleModel:

        bundle = self._ddb.find_bundle_db(bundle_name)

        if bundle == None:
            raise HTTPException(status_code=404, detail="Bundle not found")

        if pkr_list is None:
            raise HTTPException(status_code=400, detail="Bad request")

        profile_service.error_if_any_package_ref_invalid(pkr_list)

        packages = list(
            map(lambda p: PackageReferenceModel(name=p.name, version=p.version or '', use_legacy=p.use_legacy or False), pkr_list))

        bundle = self._ddb.set_bundle_packages_db(bundle_name, packages)

        return bundle

    def create_bundle(self, bundle: BundleModel) -> Optional[BundleModel]:
        if bundle.name is not None and len(bundle.name) > 0:
            profile_service.error_if_any_package_ref_invalid(bundle.packages)

            prev = self._ddb.find_bundle_db(bundle.name)
            if prev is not None:
                raise HTTPException(
                    status_code=409,
                    detail="There is already a bundle using the same name",
                )

            response: Optional[BundleModel] = self._ddb.create_bundle_db(bundle)
            return response

        raise HTTPException(status_code=422, detail="Bundle name cannot be null.")
