import datetime
import json
import time
from typing import Any, List, Optional, Tuple

from boto3.dynamodb.conditions import Attr  # type: ignore
from fastapi import HTTPException
from common.domain.status_exception import StatusException

from common.utils import Utils
from common.api.utils import Utils as ApiUtils
from common.domain.level_path import LevelPath
from common.domain.user import User
from common.logger import log
from common.service.aws.base_ddb import BaseDdb
from common.service.aws.ddb_table import DdbTable
from dependency.api.model.bundle_model import BundleModel
from dependency.api.model.full_profile_model import FullProfileModel
from dependency.api.model.new_profile_comment_model import \
    NewProfileCommentModel
from dependency.api.model.new_profile_model import NewProfileModel
from dependency.api.model.package_reference_model import PackageReferenceModel
from dependency.api.model.profile_comment_model import ProfileCommentModel
from dependency.api.model.profile_model import (PROFILE_STATUS_PENDING,
                                                ProfileModel)
from dependency.dependency_settings import DependencySettings


class DependencyDdb(BaseDdb):
    """Contains methods to access data for packages and bundles which are stored in aws dynamodb tables.
    """

    _dependency_settings: DependencySettings

    TABLE_BUNDLES_ALIAS: str = "BUNDLES"
    TABLE_PROFILES_ALIAS: str = "PROFILES"

    def __init__(self, settings: DependencySettings):

        self._dependency_settings = settings

        current_bundles_table_name: str = settings.current_bundles_table()

        TABLE_BUNDLES = DdbTable(self.TABLE_BUNDLES_ALIAS,
                                current_bundles_table_name,
                                key_schema=[{"AttributeName": "name", "KeyType": "HASH"}],
                                attr_defs=[{"AttributeName": "name", "AttributeType": "S"}],
                                read_capacity=20 if current_bundles_table_name.startswith("build-dev-") else 5,
                                write_capacity=10 if current_bundles_table_name.startswith("build-dev-") else 5)

        current_profiles_table_name: str = settings.current_profiles_table()

        TABLE_PROFILE = DdbTable(self.TABLE_PROFILES_ALIAS,
                                settings.current_profiles_table(),
                                key_schema=[{"AttributeName": "id", "KeyType": "HASH"}],
                                attr_defs=[{"AttributeName": "id", "AttributeType": "S"}],
                                read_capacity=50 if current_profiles_table_name.startswith("build-dev-") else 5,
                                write_capacity=25 if current_profiles_table_name.startswith("build-dev-") else 5)

        super(DependencyDdb, self).__init__(settings,
                                        ddb_tables=[TABLE_BUNDLES, TABLE_PROFILE])

    def table_bundles(self):
        return super().ddb_table(self.TABLE_BUNDLES_ALIAS)

    def table_profiles(self):
        return super().ddb_table(self.TABLE_PROFILES_ALIAS)

    def create_profile_db(
            self,
            path: str,
            new_profile: NewProfileModel,
            pkr_list: List[PackageReferenceModel] = [],
            bundle_list: List[BundleModel] = [],
            user: Optional[User] = None
    ) -> Optional[FullProfileModel]:

        table = self.table_profiles()

        profile_id: str = Utils.derive_profile_id_from_path(path)

        try:
            response = table.put_item(  # type: ignore
                Item={
                    "id": profile_id,
                    "name": new_profile.name,
                    "name_searchable": new_profile.name.lower(),
                    "description": new_profile.description,
                    "created_at": datetime.datetime.now().strftime("%Y-%b-%dT%H:%M:%S"),
                    "created_by": user.full_name if user is not None else "system",
                    "profile_status": "pending",
                    "path": path,
                    "packages": list(
                        map(lambda p: {"name": p.name, "version": p.version}, pkr_list)
                    ),
                    "bundles": list(
                        map(
                            lambda b: {
                                "name": b.name,
                                "packages": list(
                                    map(
                                        lambda x: {"name": x.name, "version": x.version},
                                        b.packages,
                                    )
                                ),
                            },  # type: ignore
                            bundle_list,
                        )
                    ),
                },
                ConditionExpression='attribute_not_exists(id)'
            )
        except BaseException as be:
            log.error(f"Error trying to create a profile with id {profile_id} at {path}. {be}")

            if str(be).find("ConditionalCheckFailedException") >= 0:
                raise StatusException(code=409, message="Attempted creation of profile at same path (same id)")
            
            return None
        
        response = table.get_item(Key={"id": profile_id})

        retries_left: int = 2

        while (
                retries_left > 0
        ):  # deal with fetches not yet returning a successfully created item

            profile_model: Optional[FullProfileModel] = self.find_profile_db(profile_id)

            if profile_model is None:
                log.warning(
                    f"Created profile but still missing. id: '{profile_id}'. response: '{json.dumps(response)}'"
                )
                retries_left = retries_left - 1
                if retries_left > 0:
                    time.sleep(1)
            else:
                return profile_model

        return None

    def find_profile_comments_db(
            self, profile_id: str, page_number: int, page_size: int
    ) -> Tuple[Optional[List[ProfileCommentModel]], Optional[int]]:

        item = self.find_profile_db(profile_id)

        if item is None:
            return None, None

        comments = item.comments or []

        if page_size is None:
            page_size = self._dependency_settings.DEFAULT_PAGE_SIZE
        if page_number is None:
            page_number = 1

        total = len(comments)

        start_index, end_index = ApiUtils.page_selector(
            page_number, page_size, total
        )

        return comments[start_index:end_index], total

    def add_profile_comment_db(
            self, profile_id: str, new_profile_comment: NewProfileCommentModel
    ) -> Optional[ProfileCommentModel]:

        table = self.table_profiles()

        profile = self.find_profile_db(profile_id)

        if profile is None:
            return None

        comments: List[ProfileCommentModel] = profile.comments or []

        comments.append(
            ProfileCommentModel(
                comment=new_profile_comment.comment,
                created_by=new_profile_comment.created_by or "",
                created_at=datetime.datetime.now().strftime("%Y-%b-%dT%H:%M:%S"),
            )
        )

        response = table.update_item(  # type: ignore
            Key={"id": profile_id},
            UpdateExpression="set comments = :c",
            ExpressionAttributeValues={
                ":c": list(
                    map(
                        lambda c: {
                            "comment": c.comment,
                            "created_by": c.created_by,
                            "created_at": c.created_at,
                        },
                        comments,
                    )
                )
            },
            ReturnValues="UPDATED_NEW",
        )

        items = response["Attributes"]["comments"]  # type: ignore
        dict = items[-1]  # type: ignore
        return ProfileCommentModel(**dict) if dict is not None else None  # type: ignore

    def find_profile_db(self, profile_id : str) -> Optional[FullProfileModel]:

        if profile_id is None:
            return None

        table = self.table_profiles()

        response: dict[str, str] = table.get_item(Key={"id": profile_id})  # type: ignore

        dict1 = response.get("Item")
        return FullProfileModel(**dict1) if dict1 is not None else None # type: ignore

    # def find_child_profiles_under_path_db(
    #     self, path: str
    # ) -> List[LevelProfile]:

    #     table = self.table_profiles()

    #     filter = Attr("path").eq(path)

    #     response = table.scan(FilterExpression=filter)

    #     items = response.get("Items")

    #     if items is None:
    #         return []

    #     for i in items:
    #         bundles = i.get('bundles')
    #         if bundles is None:
    #             break
    #         for b in bundles:
    #             b['name'] = b.get('id') if b.get('name') is None else b.get('name')             

    #     level_profiles = list(map(lambda i: LevelProfile(**i), items))

    #     return level_profiles

    def find_profiles_by_path_db(
            self, path: str
    ) -> List[FullProfileModel]:

        table = self.table_profiles()

        filter = Attr("path").eq(path)  # type: ignore

        response = table.scan(FilterExpression=filter)  # type: ignore

        items = response.get("Items")  # type: ignore

        if items is None:
            return []

        for i in items:  # type: ignore
            bundles = i.get('bundles')  # type: ignore
            if bundles is None:
                break
            for b in bundles:  # type: ignore
                b['name'] = b.get('id') if b.get('name') is None else b.get('name')  # type: ignore

        level_profiles = list(map(lambda i: FullProfileModel(**i), items)) # type: ignore

        return level_profiles

    def patch_profile_db(
            self, profile_id: str, new_name: str, new_description: Optional[str] = ""
    ) -> Optional[ProfileModel]:

        table = self.table_profiles()

        response = table.update_item(  # type: ignore
            Key={"id": profile_id},
            UpdateExpression="set description=:d, #N=:n, #NS=:ns", # , #P=:p",
            ExpressionAttributeValues={
                ":n": new_name,
                ":ns": new_name.lower() if new_name is not None else None,
                ":d": new_description
                # , ":p": patch_profile.path,
            },
            ExpressionAttributeNames={
                '#N': 'name', '#NS': 'name_searchable' # , '#P': 'path'
            },
            ReturnValues="ALL_NEW",
        )

        dict = response["Attributes"]  # type: ignore

        return ProfileModel(**dict) if dict is not None else None  # type: ignore

    def delete_profiles_by_path_db(self, path: str) -> List[ProfileModel]:

        profiles: List[FullProfileModel] = self.find_profiles_by_path_db(path)

        deleted_list: List[ProfileModel] = []

        for p in profiles:
            deleted = self.delete_profile_db(p.id)
            if deleted is not None:
                deleted_list.append(deleted)

        return deleted_list

    def find_profiles_under_path_db(self, path: str) -> List[ProfileModel]:

        table = self.table_profiles()

        path = LevelPath.canonize(path)

        if path != '/':
            path = path + '/'

        filter = Attr("path").begins_with(path)  # type: ignore

        response = table.scan(FilterExpression=filter)  # type: ignore

        items = response.get("Items")  # type: ignore

        if items is None:
            return []

        level_profiles: List[ProfileModel] = list(map(lambda i: ProfileModel(**i), items))  # type: ignore

        # level_profiles = filter(lambda p: Level.canonize(p.path) != path, level_profiles)

        return level_profiles

    def set_profile_packages_db(
            self, profile_id: str, pkr_list: List[PackageReferenceModel]
    ) -> List[PackageReferenceModel]:

        table = self.table_profiles()

        response = table.update_item(  # type: ignore
            Key={"id": profile_id},
            UpdateExpression="set packages=:p",
            ExpressionAttributeValues={
                ":p": list(
                    map(
                        lambda p: {"name": p.name, "version": p.version or ""}, pkr_list  # type: ignore
                    )
                ),
            },
            ReturnValues="ALL_NEW",
        )

        return response["Attributes"]["packages"]  # type: ignore

    def set_profile_bundle_packages_db(
            self, profile_id: str, bundle_name: str, bundle_list: List[BundleModel]
    ) -> Optional[BundleModel]:

        table = self.table_profiles()

        response = table.update_item(  # type: ignore
            Key={"id": profile_id},
            UpdateExpression="set bundles=:b",
            ExpressionAttributeValues={
                ":b": list(
                    map(
                        lambda xb: {
                            "name": xb.name,  # type: ignore
                            "description": xb.description,
                            "packages": list(
                                map(
                                    lambda p: {"name": p.name, "version": p.version, "use_legacy": p.use_legacy},
                                    xb.packages
                                )
                            ),
                        },
                        bundle_list
                    )
                ),
            },
            ReturnValues="ALL_NEW",
        )

        bundles = response["Attributes"]["bundles"]  # type: ignore

        dict = next(filter(lambda b2: b2.get("name") == bundle_name, bundles))  # type: ignore

        return BundleModel(**dict) if dict is not None else None  # type: ignore

    def set_bundle_packages_db(
            self, bundle_name: str, package_list: List[PackageReferenceModel]
    ) -> BundleModel:

        table = self.table_bundles()

        response = table.update_item(  # type: ignore
            Key={"name": bundle_name},
            UpdateExpression="set packages=:l",
            ExpressionAttributeValues={
                ":l": list(
                    map(
                        lambda p: {"name": p.name, "version": p.version or "", "use_legacy": p.use_legacy or False},  # type: ignore
                        package_list,  # type: ignore
                    )
                ),
            },
            ReturnValues="ALL_NEW",
        )

        bundle = response["Attributes"]  # type: ignore

        return bundle  # type: ignore

    def list_profiles_db(
            self, page_number: int, page_size: int, query_string: str
    ) -> Tuple[List[ProfileModel], int]:
        if page_size is None:
            page_size = self._dependency_settings.DEFAULT_PAGE_SIZE
        if page_number is None:
            page_number = 1

        try:
            table = self.table_profiles()

            if query_string is not None:
                response = table.scan(  # type: ignore
                    FilterExpression=Attr("name_searchable").contains(query_string.lower())  # type: ignore
                )
            else:
                response = table.scan()  # type: ignore

            total = response["Items"].__len__()  # type: ignore
            start_index, end_index = ApiUtils.page_selector(
                page_number, page_size, total  # type: ignore
            )
            result = response["Items"]  # type: ignore
            log.debug(f"Found profiles: {result}")
            return result[start_index:end_index], total  # type: ignore
        except Exception as e:
            log.error(f"Error reading profiles {e}.")
            return [], 0

    def create_bundle_db(self, bundle: BundleModel) -> Optional[BundleModel]:

        table = self.table_bundles()

        table.put_item(  # type: ignore
            Item={
                "name": bundle.name,
                "name_searchable": bundle.name.lower(),
                "description": bundle.description or '',
                "packages": list(
                    map(
                        lambda p: {"name": p.name, "version": p.version, "use_legacy": p.use_legacy},
                        bundle.packages,
                    )
                ),
            }
        )

        response = table.get_item(Key={"name": bundle.name})  # type: ignore

        retries_left: int = 2

        while (
            retries_left > 0
        ):  # deal with fetches not yet returning a successfully created item

            bundle_model: Optional[BundleModel] = self.find_bundle_db(bundle.name)

            if bundle_model is None:
                log.warning(
                    f"Created bundle but still missing. id: '{id}'. response: '{json.dumps(response)}'"
                )
                retries_left = retries_left - 1
                if retries_left > 0:
                    time.sleep(1)
            else:
                return bundle_model

        return None

    def list_bundles_db(self, page_number: int, page_size: int, query_string: Optional[str]) -> Tuple[
        List[BundleModel], int]:
        if page_size is None:
            page_size = self._dependency_settings.DEFAULT_PAGE_SIZE
        if page_number is None:
            page_number = 1
        table = self.table_bundles()
        if query_string is not None:
            response = table.scan(  # type: ignore
                FilterExpression=Attr("name_searchable").contains(query_string.lower())  # type: ignore
            )
        else:
            response = table.scan()  # type: ignore

        total: int = len(response["Items"])  # type: ignore
        start_index, end_index = ApiUtils.page_selector(
            page_number, page_size, total
        )
        result = response["Items"]  # type: ignore
        return result[start_index:end_index], total  # type: ignore

    def change_profile_status_db(self, profile_id: str, validation_result: str = PROFILE_STATUS_PENDING,
                                 result_reason: Optional[str] = '', rxt: Optional[str] = '',
                                 check_exist: bool = False) -> bool:

        table = self.table_profiles()

        if check_exist:
            if self.find_profile_db(profile_id) is None:
                raise HTTPException(status_code=404, detail="Profile not found")

        response: Any = table.update_item(  # type: ignore
            Key={"id": profile_id},
            UpdateExpression="set profile_status = :c, profile_rxt = :r",
            ExpressionAttributeValues={
                ":c": validation_result,
                ":r": rxt if validation_result == 'valid' else '',
            },
            ReturnValues="UPDATED_NEW",
        )

        item: Any = response["Attributes"]["profile_status"]

        self.add_profile_comment_db(profile_id=profile_id, new_profile_comment=NewProfileCommentModel(
            comment=f"validation detail: {result_reason}"))

        return item is not None

    def delete_profile_db(self, profile_id: str) -> Optional[ProfileModel]:

        table = self.table_profiles()

        response = table.delete_item(  # type: ignore
            Key={"id": profile_id},
            ReturnValues="ALL_OLD",
        )

        dict = response.get("Attributes")  # type: ignore

        return ProfileModel(**dict) if dict is not None else None  # type: ignore

    def delete_profile_bundle_db(
            self, profile_id: str, bundles: List[BundleModel], bundle_name: str
    ) -> List[BundleModel]:

        table = self.table_profiles()

        up_bundles = list(filter(lambda b: b.name != bundle_name, bundles))

        if len(bundles) == len(up_bundles):
            raise HTTPException(
                status_code=404,
                detail="Profile does not contains a bundle with that name",
            )

        response = table.update_item(
            Key={"id": profile_id},
            UpdateExpression="set bundles=:b",
            ExpressionAttributeValues={":b": up_bundles},
            ReturnValues="UPDATED_NEW",
        )

        return response["Attributes"]["bundles"]  # type: ignore

    def find_bundle_db(self, bundle_name: str) -> Optional[BundleModel]:

        if bundle_name is None:
            return None

        table = self.table_bundles()

        response = table.get_item(Key={"name": bundle_name})  # type: ignore

        dict = response.get("Item")  # type: ignore

        return BundleModel(**dict) if dict is not None else None  # type: ignore

    def delete_bundle_db(self, bundle_name: str) -> BundleModel:

        table = self.table_bundles()

        response = table.delete_item(  # type: ignore
            Key={"name": bundle_name},
            ReturnValues="ALL_OLD",
        )

        dict = response.get("Attributes")  # type: ignore

        if dict is None:
            raise HTTPException(status_code=404, detail="Bundle not found")

        return BundleModel(**dict)  # type: ignore
