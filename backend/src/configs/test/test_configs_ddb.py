## coding: utf-8

from typing import Any, List, Optional

from common.utils import Utils
from configs.configs_settings import ConfigsSettings
from configs.domain.config_item import ConfigItem
from configs.service.aws.configs_ddb import ConfigsDdb

settings: ConfigsSettings = ConfigsSettings.load_configs()

config_ddb: ConfigsDdb = ConfigsDdb(settings=settings)

def test_create_retrieve_config(test_tables: Any):

    config_item: Optional[ConfigItem] = config_ddb.create_config(
        path="/a/b/c", name="config1", description="", inherits=True, created_by="")

    assert config_item is not None
    assert config_item.name == "config1"
    assert config_item.path == "/a/b/c"
    assert config_item.active == False

    config_item2: Optional[ConfigItem] = config_ddb.get_config_by_id(
        config_item.id)

    assert config_item2 is not None
    assert config_item2.name == config_item.name
    assert config_item2.path == config_item.path
    assert config_item2.active == config_item.active

def test_create_delete_config(test_tables: Any):

    config_item1: Optional[ConfigItem] = config_ddb.create_config(
        path="/a/b/c/d", name="config1", description="", inherits=True, created_by="")

    assert config_item1 is not None

    config_item2: Optional[ConfigItem] = config_ddb.create_config(
        path="/a/b/c/d", name="config1", description="", inherits=True, created_by="")

    assert config_item2 is not None

    deleted_item1: Optional[ConfigItem] = config_ddb.delete_config_by_id(config_item1.id)

    assert deleted_item1 is not None
    assert deleted_item1.id == config_item1.id

    deleted_item1 = config_ddb.delete_config_by_id(config_item1.id)

    assert deleted_item1 is None

    deleted_item2: Optional[ConfigItem] = config_ddb.delete_config_by_id(config_item2.id)

    assert deleted_item2 is not None
    assert deleted_item2.id == config_item2.id

    deleted_item2 = config_ddb.delete_config_by_id(config_item2.id)

    assert deleted_item2 is None


def test_find_by_path(test_tables: Any):

    random_word: str = Utils.randomword(12)
    path: str = f"/Mumbai/television/test_{random_word}"

    config_ddb.create_config(path=path, name="config1", description="", inherits=True, created_by="")
    config_ddb.create_config(path=path, name="config2", description="", inherits=True,  created_by="")
    config_ddb.create_config(path=path, name="config3", description="", inherits=True,  created_by="")

    config_items: Optional[List[ConfigItem]] = config_ddb.find_by_path(path)

    assert config_items is not None
    assert len(config_items) == 3
    assert config_items[0].name == "config1"
    assert config_items[1].name == "config2"
    assert config_items[2].name == "config3"


def test_find_by_path_and_name(test_tables: Any):

    random_word: str = Utils.randomword(12)
    
    path1: str = f"/Global/television/test_{random_word}"
    path2: str = f"/Global/film/test_{random_word}"
    path3: str = f"/Toronto/television/test_{random_word}"

    name1: str = f"config_1_{random_word}"
    name2: str = f"config_2_{random_word}"
    name3: str = f"config_3_{random_word}"

    config_ddb.create_config(path=path1, name=name1, description="", inherits=True, created_by="")
    config_ddb.create_config(path=path1, name=name1, description="", inherits=True, created_by="")
    config_ddb.create_config(path=path2, name=name1, description="", inherits=True, created_by="")
    config_ddb.create_config(path=path2, name=name2, description="", inherits=True, created_by="")    

    config_items: Optional[List[ConfigItem]] = config_ddb.find_by_path_and_name(path1, name1)

    assert config_items is not None
    assert len(config_items) == 2

    config_items: Optional[List[ConfigItem]] = config_ddb.find_by_path_and_name(path1, name2)

    assert config_items is not None
    assert len(config_items) == 0

    config_items: Optional[List[ConfigItem]] = config_ddb.find_by_path_and_name(path2, name1)

    assert config_items is not None
    assert len(config_items) == 1

    config_items: Optional[List[ConfigItem]] = config_ddb.find_by_path_and_name(path2, name2)

    assert config_items is not None
    assert len(config_items) == 1

    config_items: Optional[List[ConfigItem]] = config_ddb.find_by_path_and_name(path3, name1)

    assert config_items is not None
    assert len(config_items) == 0

    config_items: Optional[List[ConfigItem]] = config_ddb.find_by_path_and_name(path3, name2)

    assert config_items is not None
    assert len(config_items) == 0

    config_items: Optional[List[ConfigItem]] = config_ddb.find_by_path_and_name(path1, name3)

    assert config_items is not None
    assert len(config_items) == 0


def test_find_by_name(test_tables: Any):

    random_word: str = Utils.randomword(12)
    path1: str = f"/Mumbai/film/test_{random_word}"
    path2: str = f"/Toronto/television/test_{random_word}"

    config_name: str = f"config_{random_word}"

    config_ddb.create_config(path=path1, name=config_name, description="", inherits=True, created_by="")
    config_ddb.create_config(path=path1, name=config_name, description="", inherits=True, created_by="")
    config_ddb.create_config(path=path2, name=config_name, description="", inherits=True, created_by="")

    config_items: Optional[List[ConfigItem]] = config_ddb.find_by_name(
        config_name)

    assert config_items is not None
    assert len(config_items) == 3
    assert config_items[0].name == config_name
    assert config_items[1].name == config_name
    assert config_items[2].name == config_name

    assert 2 == len(list(filter(lambda i: i.path == path1, config_items)))
    assert 1 == len(list(filter(lambda i: i.path == path2, config_items)))

    none_config_items: Optional[List[ConfigItem]] = config_ddb.find_by_name(config_name, False, False)

    assert none_config_items is not None
    assert len(none_config_items) == 0

    all_config_items: Optional[List[ConfigItem]] = config_ddb.find_by_name(config_name, True, True)

    assert all_config_items is not None
    assert len(all_config_items) == 3

    active_config_items: Optional[List[ConfigItem]] = config_ddb.find_by_name(config_name, True, False)

    assert active_config_items is not None
    assert len(active_config_items) == 0

    inactive_config_items: Optional[List[ConfigItem]] = config_ddb.find_by_name(config_name, False, True)

    assert inactive_config_items is not None
    assert len(inactive_config_items) == 3

    total: int
    inactive_config_items, total = config_ddb.find_all(name=f"~{config_name.upper()}", path=None, page_number=1, page_size=10, allowed_projects=None)

    assert inactive_config_items is not None
    assert len(inactive_config_items) == 3
    assert total == 3


def test_find_ancestors_by_name_from_path(test_tables: Any):

    random_word: str = Utils.randomword(12)
    
    path1: str = f"/Global/television/test_{random_word}"
    path2: str = f"{path1}/deeper"
    path3: str = f"{path2}/x/and_deeper"
    path3d: str = f"{path3}/z/even_deeper"
    path3di: str = f"{path3d}/waaay_deeper/a/b/c/d"
    path4: str = f"/Global/film/test_{random_word}"
    path4i: str = f"{path4}/a/b/c"
    path5: str = f"/Mumbai/film/test_{random_word}/xyz"

    name1: str = f"config_1_{random_word}"    
    name2: str = f"config_2_{random_word}"

    # create out of order regarding depth:
    config3d: Optional[ConfigItem] = config_ddb.create_config(path=path3d, name=name1, description="", inherits=True, created_by="")
    config1: Optional[ConfigItem] =  config_ddb.create_config(path=path1, name=name1, description="", inherits=True, created_by="")
    config3: Optional[ConfigItem] = config_ddb.create_config(path=path3, name=name1, description="", inherits=True, created_by="")
    config2: Optional[ConfigItem] = config_ddb.create_config(path=path2, name=name1, description="", inherits=True, created_by="")    
    config4: Optional[ConfigItem] = config_ddb.create_config(path=path4, name=name1, description="", inherits=True, created_by="")
    config5: Optional[ConfigItem] = config_ddb.create_config(path=path1, name=name2, description="", inherits=True, created_by="")

    assert config1 is not None
    assert config2 is not None
    assert config3 is not None
    assert config3d is not None
    assert config4 is not None
    assert config5 is not None

    config_items: Optional[List[ConfigItem]] = config_ddb.find_active_ancestors_at_path_for_name(path3, name1)

    assert config_items is not None
    assert len(config_items) == 0

    config_ddb.activate_config_by_id(config1.id)
    config_ddb.activate_config_by_id(config2.id)
    config_ddb.activate_config_by_id(config3.id)
    config_ddb.activate_config_by_id(config3d.id)

    config_items: Optional[List[ConfigItem]] = config_ddb.find_active_ancestors_at_path_for_name(path3, name1)

    assert config_items is not None
    assert len(config_items) == 3

    config_items: Optional[List[ConfigItem]] = config_ddb.find_active_ancestors_at_path_for_name(path3d, name1)

    assert config_items is not None
    assert len(config_items) == 4

    # check paths are ordered from top to deepest:
    assert config_items[0].path == path1
    assert config_items[1].path == path2
    assert config_items[2].path == path3
    assert config_items[3].path == path3d
    
    config_items: Optional[List[ConfigItem]] = config_ddb.find_active_ancestors_at_path_for_name(path3di, name1)

    assert config_items is not None
    assert len(config_items) == 4

    # inactivate one of the parents and check again
    config_ddb.inactivate_config_by_id(config2.id)

    config_items: Optional[List[ConfigItem]] = config_ddb.find_active_ancestors_at_path_for_name(path3di, name1)

    assert config_items is not None
    assert len(config_items) == 3

    # check paths are ordered from top to deepest:
    assert config_items[0].path == path1    
    assert config_items[1].path == path3
    assert config_items[2].path == path3d    

    config_items: Optional[List[ConfigItem]] = config_ddb.find_active_ancestors_at_path_for_name(path4i, name1)

    assert config_items is not None
    assert len(config_items) == 0

    config_ddb.activate_config_by_id(config4.id)

    config_items: Optional[List[ConfigItem]] = config_ddb.find_active_ancestors_at_path_for_name(path4i, name1)

    assert config_items is not None
    assert len(config_items) == 1

    config_items: Optional[List[ConfigItem]] = config_ddb.find_active_ancestors_at_path_for_name(path4, name1)

    assert config_items is not None
    assert len(config_items) == 1

    config_items: Optional[List[ConfigItem]] = config_ddb.find_active_ancestors_at_path_for_name(path4, name2)

    assert config_items is not None
    assert len(config_items) == 0

    config_items: Optional[List[ConfigItem]] = config_ddb.find_active_ancestors_at_path_for_name(path5, name2)

    assert config_items is not None
    assert len(config_items) == 0

def test_set_current_config(test_tables: Any):

    random_word: str = Utils.randomword(12)
    
    path: str = f"/Global/film/test_{random_word}/qwerty"
    
    name: str = f"config_same_{random_word}"     

    config1: Optional[ConfigItem] =  config_ddb.create_config(path=path, name=name, description="", inherits=True, created_by="")
    config2: Optional[ConfigItem] = config_ddb.create_config(path=path, name=name, description="", inherits=True, created_by="")
    config3: Optional[ConfigItem] = config_ddb.create_config(path=path, name=name, description="", inherits=True, created_by="")
    
    assert config1 is not None
    assert config2 is not None
    assert config3 is not None

    config_items: Optional[List[ConfigItem]] = config_ddb.find_by_name(config_name=name, include_active_ones=True, include_inactive_ones=False)

    assert config_items is not None
    assert len(config_items) == 0

    config_ddb.set_current_by_id(config1.id)

    config_items: Optional[List[ConfigItem]] = config_ddb.find_by_name(config_name=name, include_active_ones=True, include_inactive_ones=False)

    assert config_items is not None
    assert len(config_items) == 1
    assert config_items[0].id == config1.id

    config_ddb.set_current_by_id(config3.id)

    config_items: Optional[List[ConfigItem]] = config_ddb.find_by_name(config_name=name, include_active_ones=True, include_inactive_ones=False)

    assert config_items is not None
    assert len(config_items) == 1
    assert config_items[0].id == config3.id

    config_ddb.set_current_by_id(config1.id)
    config_ddb.set_current_by_id(config2.id)
    config_ddb.set_current_by_id(config3.id)
    config_ddb.set_current_by_id(config2.id)

    config_items: Optional[List[ConfigItem]] = config_ddb.find_by_name(config_name=name, include_active_ones=True, include_inactive_ones=False)

    assert config_items is not None
    assert len(config_items) == 1
    assert config_items[0].id == config2.id

    config_ddb.inactivate_config_by_id(config2.id)

    config_items: Optional[List[ConfigItem]] = config_ddb.find_by_name(config_name=name, include_active_ones=True, include_inactive_ones=False)

    assert config_items is not None
    assert len(config_items) == 0

    config_ddb.activate_config_by_id(config1.id)
    config_item: Optional[ConfigItem] = config_ddb.find_current_by_level_and_name(level_path=path, config_name=name)

    assert config_item is not None
    assert config_item.id == config1.id

    config_ddb.activate_config_by_id(config3.id)
    config_ddb.activate_config_by_id(config2.id)
    config_item: Optional[ConfigItem] = config_ddb.find_current_by_level_and_name(level_path=path, config_name=name)

    assert config_item is not None
    assert config_item.id == config2.id

    config_ddb.set_current_by_id(config1.id)    
    config_item: Optional[ConfigItem] = config_ddb.find_current_by_level_and_name(level_path=path, config_name=name)

    assert config_item is not None
    assert config_item.id == config1.id

    config_ddb.inactivate_config_by_id(config1.id)
    config_item: Optional[ConfigItem] = config_ddb.find_current_by_level_and_name(level_path=path, config_name=name)

    assert config_item is None

def test_patch_config(test_tables: Any):
    
    random_word: str = Utils.randomword(12)
    
    path1: str = f"/Global/film/test_{random_word}/qwerty"    
    name1: str = f"config_name_{random_word}"     
    desc1: str = "first desc"
    author1: str = "joseph"

    config1: Optional[ConfigItem] = config_ddb.create_config(path=path1, name=name1, description=desc1, inherits=True, created_by=author1)

    assert config1 is not None

    path2: str = f"/Mumbai/television/test_{random_word}/asdfg"    
    name2: str = f"another_config_{random_word}"     
    desc2: str = "second desc"

    config2: Optional[ConfigItem] = config_ddb.patch_config(id=config1.id, path=path2, name=name2, description=desc2, inherits=True, active=0)

    assert config2 is not None
    assert config2.id == config1.id    
    assert config2.name == name2
    assert config2.path == path2
    assert config2.description == desc2
    assert config2.created_by == config1.created_by
    assert config2.created == config1.created
    assert config2.updated > config1.updated

    config3: Optional[ConfigItem] = config_ddb.get_config_by_id(config1.id)

    assert config3 is not None

    assert config3 is not None
    assert config3.id == config2.id    
    assert config3.name == name2
    assert config3.path == path2
    assert config3.description == desc2
    assert config3.created_by == config2.created_by
    assert config3.created == config2.created
    assert config3.updated == config2.updated

