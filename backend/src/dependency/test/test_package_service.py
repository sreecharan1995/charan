# coding: utf-8

# from deepdiff import DeepDiff # type: ignore
from dependency.service.package_service import PackageService
from dependency.dependency_settings import DependencySettings


def get_settings_override() -> DependencySettings:
    dep_settings = DependencySettings()
    dep_settings.DEP_PACKAGES_DIRECTORY_PATH = ""
    return dep_settings

package_service = PackageService(settings=get_settings_override())


def test_building_packages():
    packages = package_service.packages

    assert len(packages) == 4

    # assert not DeepDiff(packages,
    #                     [Package(name='alabaster', versions=['0.7.12', '0.7.17'], category='category_a'),
    #                      Package(name='anyio', versions=['3.5.0', '3.5.1'], category='category_a'),
    #                      Package(name='sphinx', versions=['4.5.0'], category='category_b'),
    #                      Package(name='fastapi', versions=['0.75.75', '0.75.1', '0.73'], category='category_b')],
    #                     ignore_order=True,
    #                     exclude_regex_paths=r"root\[\d+\]\[3\]\[1\]"
    #                     )


def test_get_package_by_name():
    package = package_service.get_package("fastapi")
    assert package is not None
    assert package.name == "fastapi"


def test_exists():
    assert package_service.exists("fastapi", "0.75.1")
    assert package_service.exists("fastapi", "0.73")
    assert not package_service.exists("unknown package", "unknown version")
    assert not package_service.exists("unknown package")
