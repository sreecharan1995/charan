# coding: utf-8

import os
import pathlib
from typing import List, Optional, Tuple

from common.api.utils import Utils
from common.logger import log
from dependency.api.model.package_model import PackageModel
from dependency.dependency_settings import DependencySettings


class PackageService:
    """Contains methods used internally to access or list existing packages and to verify they exists.
    """

    _directory_path: str
    _packages_filename: str

    def __init__(self, settings: DependencySettings = DependencySettings.load()):

        if not settings.DEP_PACKAGES_DIRECTORY_PATH.strip():
            directory_path = pathlib.Path(__file__).parent.absolute().parent
            self._directory_path = f"{directory_path.as_posix()}/mocks/packages"
            self._packages_filename = f"{directory_path.as_posix()}/mocks/packages.json"
        else:
            self._directory_path = (
                pathlib.Path(settings.DEP_PACKAGES_DIRECTORY_PATH).absolute().as_posix()                
            )
            self._packages_filename = pathlib.Path(self._directory_path, "packages.json").as_posix()

        self.packages: List[PackageModel] = self.read_from_file_system() or []

    def get_package(self, name: str) -> Optional[PackageModel]:
        matching_package = [p for p in self.packages if p.name == name]
        if len(matching_package) == 1:
            return matching_package[0]

        return None

    def exists(self, name: Optional[str], version: Optional[str] = "") -> bool:
        if name is None or name == "":
            return False

        return (
            next(
                (
                    p
                    for p in self.packages
                    if (p.name == name)
                    and ((version or "").strip() is not "")
                    and (version in p.versions)
                ),
                None,
            )
            is not None
        )

    def list_packages(
        self, p: int, ps: int, q: str, c: str
    ) -> Tuple[List[PackageModel], int]:

        result = []
        packages_subset = self.packages

        if c:
            packages_subset = list(
                filter(lambda package: c.lower() == package.category, self.packages)
            )

        if q and len(q):
            result = list(
                filter(lambda package: q.lower() == package.name, packages_subset)
            )
        else:
            result = packages_subset

        start_index, end_index = Utils.page_selector(p, ps, result.__len__())

        return result[start_index:end_index], len(result)

    def get_packages_filename(self) -> str:
        return self._packages_filename

    def read_from_file_system(self) -> List[PackageModel]:
        category_depth = 2
        package_depth = 3
        version_depth = 4 # type: ignore
        packages_dict = {}
        current_category = None
        current_package = None

        for root, _, files in os.walk(self._directory_path): # type: ignore

            _root = root.replace(str(self._directory_path), "")
            depth_levels = _root.split("/")

            depth = len(depth_levels)

            _basename = os.path.basename(_root)

            log.debug(f"Processing path {_root} at depth level {len(depth_levels)}")

            if category_depth == depth:
                current_category = str.lower(_basename)

            if package_depth == depth:
                log.debug(f"Versions are: {_}")
                current_package = str.lower(_basename)
                packages_dict[current_package] = {
                    "path": root,
                    "versions": _[:],
                    "category": current_category,
                }
                _.clear()
                continue

        packages = [
            PackageModel(
                name=key, # type: ignore
                path=packages_dict[key]["path"], # type: ignore
                versions=packages_dict[key]["versions"], # type: ignore
                category=packages_dict[key]["category"], # type: ignore
            ) for key in packages_dict # type: ignore
        ]

        packages.sort(key=lambda p: p.name or "")

        return packages
