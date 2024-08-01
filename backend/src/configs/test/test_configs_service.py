## coding: utf-8

from typing import Any, Dict, Optional

from common.api.model.level_path_model import LevelPathModel
from common.domain.level_path import LevelPath
from common.domain.user import User
from configs.api.model.config_model import ConfigModel
from configs.api.model.config_status_model import ConfigStatusModel
from configs.api.model.create_config_model import CreateConfigModel
from configs.api.model.patch_config_model import PatchConfigModel
from configs.configs_settings import ConfigsSettings
from configs.service.configs_service import ConfigsService

settings: ConfigsSettings = ConfigsSettings.load_configs()

configs_service: ConfigsService = ConfigsService(settings=settings)

current_true: Dict[str, Any] = {"current": True}
current_false: Dict[str, Any] = {"current": False}


def test_create_get_delete_config(test_tables: Any):
    config_json: Dict[str, Any] = {}  # TODO: test with real config

    level_path_model: LevelPathModel = LevelPathModel.from_level_path(LevelPath.from_path("/"))

    create_config_model: CreateConfigModel = CreateConfigModel(name="a_name", description="a description",
                                                               level=level_path_model, configuration=config_json)

    operator: User = User(username="operator1", full_name="Operator 1", email="operator@test.local", groups=set(),
                          token="")

    config_model: Optional[ConfigModel] = configs_service.create_config(operator_user=operator,
                                                                        create_config_model=create_config_model)

    assert config_model is not None
    assert config_model.current is False
    assert config_model.path == level_path_model.to_level_path().get_path()
    assert config_model.level is not None
    assert config_model.level == level_path_model
    assert config_model.configuration == config_json
    assert config_model.created is not None
    assert config_model.created_by == operator.username
    assert config_model.updated is not None
    assert config_model.updated == config_model.created
    assert config_model.description == "a description"
    assert config_model.name == "a_name"

    config_model2: Optional[ConfigModel] = configs_service.get_config(operator_user=operator, id=config_model.id,
                                                                      token_dict=None)

    assert config_model2 is not None
    assert config_model2 == config_model

    deleted_config: Optional[bool] = configs_service.delete_config(operator_user=operator, id=config_model.id)

    assert deleted_config is not None
    assert deleted_config is True

    config_model3: Optional[ConfigModel] = configs_service.get_config(operator_user=operator, id=config_model.id,
                                                                      token_dict=None)

    assert config_model3 is None

    deleted_config2: Optional[bool] = configs_service.delete_config(operator_user=operator, id=config_model.id)

    assert deleted_config2 is None


def test_resolve_config(test_tables: Any):
    config_json: Dict[str, Any] = {"s": "<show>", "d": "<division>", "e1": "x_<bling>", "n": "a number <pin_8>",
                                   "u": "an unreplaceable <<thing>> thing"}

    level_path_model: LevelPathModel = LevelPathModel.from_level_path(LevelPath.from_path("/Mumbai/television/abcshow"))

    create_config_model: CreateConfigModel = CreateConfigModel(name="a_name", description="a description",
                                                               level=level_path_model, configuration=config_json)

    operator: User = User(username="operator1", full_name="Operator 1", email="operator@test.local", groups=set(),
                          token="")

    config_model: Optional[ConfigModel] = configs_service.create_config(operator_user=operator,
                                                                        create_config_model=create_config_model)

    assert config_model is not None

    fetched_model = configs_service.get_config(operator_user=operator, id=config_model.id,
                                               token_dict={"bling": "tiger", "pin_8": "12345678", "thing": "funny"})

    assert fetched_model is not None
    assert fetched_model.configuration.get("s") == "abcshow"
    assert fetched_model.configuration.get("d") == "television"
    assert fetched_model.configuration.get("e1") == "x_tiger"
    assert fetched_model.configuration.get("n") == "a number 12345678"
    assert fetched_model.configuration.get("u") == "an unreplaceable <<thing>> thing"


def test_get_effective_config(test_tables: Any):
    operator: User = User(username="operator1", full_name="Operator 1", email="operator@test.local", groups=set(),
                          token="")

    config_json_1: Dict[str, Any] = {"a": "1", "b": 2, "q": 88,
                                     "d": {"x": "m", "y": {"y1": 0, "y2": "v1", "y4": 11}, "z": "k"}, "h": 7}

    level_path_model_1: LevelPathModel = LevelPathModel.from_level_path(LevelPath.from_path("/Mumbai/television"))

    create_config_model_1: CreateConfigModel = CreateConfigModel(name="a_name", description="a description",
                                                                 level=level_path_model_1, configuration=config_json_1)

    config_model_1: Optional[ConfigModel] = configs_service.create_config(operator_user=operator,
                                                                          create_config_model=create_config_model_1,
                                                                          inherit=True)

    assert config_model_1 is not None

    config_json_2: Dict[str, Any] = {"h": 77, "q": None, "a": "1", "j": "jj",
                                     "d": {"x": "x_changed", "y": {"y1": 0, "y2": "v1_changed", "y3": "y3_added"},
                                           "z_added": "k", "z": None}}

    level_path_model_2: LevelPathModel = LevelPathModel.from_level_path(
        LevelPath.from_path("/Mumbai/television/wonder9"))

    create_config_model_2: CreateConfigModel = CreateConfigModel(name="a_name", description="a description",
                                                                 level=level_path_model_2, configuration=config_json_2)

    config_model_2: Optional[ConfigModel] = configs_service.create_config(operator_user=operator,
                                                                          create_config_model=create_config_model_2,
                                                                          inherit=True)

    assert config_model_2 is not None

    effective_model: Optional[ConfigModel] = configs_service.get_effective_config(operator_user=operator, name="a_name",
                                                                                  level_path="/Mumbai/television/wonder9/asset/qwerty",
                                                                                  token_dict=None)

    assert effective_model is None

    assert configs_service.set_config_status(operator_user=operator, id=config_model_1.id,
                                             status_model=ConfigStatusModel(**current_true))

    effective_model: Optional[ConfigModel] = configs_service.get_effective_config(operator_user=operator, name="a_name",
                                                                                  level_path="/Mumbai/television/wonder9/asset/qwerty",
                                                                                  token_dict=None)

    assert effective_model is not None

    assert effective_model.id == config_model_1.id
    assert effective_model.configuration.get("h", None) == 7

    assert configs_service.set_config_status(operator_user=operator, id=config_model_2.id,
                                             status_model=ConfigStatusModel(**current_true))

    effective_model: Optional[ConfigModel] = configs_service.get_effective_config(operator_user=operator, name="a_name",
                                                                                  level_path="/Mumbai/television/wonder9/asset/qwerty",
                                                                                  token_dict=None)

    assert effective_model is not None

    assert effective_model.id == config_model_2.id
    assert effective_model.configuration is not None
    assert effective_model.configuration.get("a", None) == "1"
    assert effective_model.configuration.get("b", None) == 2
    assert effective_model.configuration.get("j", None) == "jj"
    assert "q" in effective_model.configuration
    assert effective_model.configuration.get("q", None) is None
    assert "d" in effective_model.configuration
    dict_d: Optional[Dict[str, Any]] = effective_model.configuration.get("d", None)
    assert dict_d is not None
    assert dict_d.get("x", None) == "x_changed"
    assert "z" in dict_d
    assert dict_d.get("z", None) is None
    assert dict_d.get("z_added", None) == "k"
    assert "y" in dict_d
    dict_y: Optional[Dict[str, Any]] = dict_d.get("y", None)
    assert dict_y is not None
    assert dict_y.get("y1", None) == 0
    assert dict_y.get("y4", None) == 11
    assert dict_y.get("y2", None) == "v1_changed"
    assert dict_y.get("y3", None) == "y3_added"

    effective_model: Optional[ConfigModel] = configs_service.get_effective_config(operator_user=operator, name="a_name",
                                                                                  level_path="/Mumbai/television/wonder9/asset/qwerty",
                                                                                  token_dict=None, inherit=False)
    assert effective_model is not None

    assert effective_model.id == config_model_2.id
    assert not "b" in effective_model.configuration
    assert effective_model.configuration.get("j", None) == "jj"
    assert effective_model.configuration.get("h", None) == 77

    assert configs_service.set_config_status(operator_user=operator, id=config_model_1.id,
                                             status_model=ConfigStatusModel(**current_false))

    effective_model: Optional[ConfigModel] = configs_service.get_effective_config(operator_user=operator, name="a_name",
                                                                                  level_path="/Mumbai/television/wonder9/asset/qwerty",
                                                                                  token_dict=None)

    assert effective_model is not None

    assert effective_model.id == config_model_2.id
    assert effective_model.configuration.get("h", None) == 77
    assert not "b" in effective_model.configuration

    assert configs_service.set_config_status(operator_user=operator, id=config_model_1.id,
                                             status_model=ConfigStatusModel(**current_true))
    assert configs_service.set_config_status(operator_user=operator, id=config_model_2.id,
                                             status_model=ConfigStatusModel(**current_false))

    effective_model: Optional[ConfigModel] = configs_service.get_effective_config_preview(operator_user=operator, id=config_model_2.id, token_dict=None, inherit=True)

    assert effective_model is not None
    assert effective_model.id == config_model_2.id  # because preview is being forced from a config id, (even if not current)
    assert effective_model.configuration.get("h", None) == 77  # from child, because is a preview
    assert effective_model.configuration.get("b", None) == 2
    assert effective_model.configuration.get("j", None) == "jj"
    assert effective_model.configuration.get("q", None) is None


def test_patch_config(test_tables: Any):
    operator: User = User(username="operator1", full_name="Operator 1", email="operator@test.local", groups=set(),
                          token="")

    config_json_1: Dict[str, Any] = {"a": "1", "b": 2, "q": 88,
                                     "d": {"x": "m", "y": {"y1": 0, "y2": "v1", "y4": 11}, "z": "k"}, "h": 7}
    # config_json_1: Dict[str,Any] = { "h": 7 }

    level_path_model_1: LevelPathModel = LevelPathModel.from_level_path(LevelPath.from_path("/Mumbai/television"))

    create_config_model_1: CreateConfigModel = CreateConfigModel(name="a_name", description="a description",
                                                                 level=level_path_model_1, configuration=config_json_1)

    config_model_1: Optional[ConfigModel] = configs_service.create_config(operator_user=operator,
                                                                          create_config_model=create_config_model_1,
                                                                          inherit=True)

    assert config_model_1 is not None

    config_json_2: Dict[str, Any] = {"h": 77, "q": None, "a": "1", "j": "jj",
                                     "d": {"x": "x_changed", "y": {"y1": 0, "y2": "v1_changed", "y3": "y3_added"},
                                           "z_added": "k", "z": None}}
    # config_json_2: Dict[str,Any] = { "h": 77 } 

    level_path_model_2: LevelPathModel = LevelPathModel.from_level_path(
        LevelPath.from_path("/Mumbai/television/wonder9"))

    create_config_model_2: CreateConfigModel = CreateConfigModel(name="a_name", description="a description",
                                                                 level=level_path_model_2, configuration=config_json_2)

    config_model_2: Optional[ConfigModel] = configs_service.create_config(operator_user=operator,
                                                                          create_config_model=create_config_model_2,
                                                                          inherit=True)

    assert config_model_2 is not None

    assert configs_service.set_config_status(operator_user=operator, id=config_model_1.id,
                                             status_model=ConfigStatusModel(**current_true))

    # patch config 2, use the same name and subpath of config 1

    json_patch: Dict[str, Any] = {"h": 77, "b": 2, "a": 2, "q": 99, "j": None, "d": {"x": "x_changed", "y": 0}}
    # json_patch: Dict[str,Any] = { "h": 77 }

    patch_model: PatchConfigModel = PatchConfigModel()
    # patch_model.name = "a_name"
    # dest_path: str = "/Mumbai/television/wonder9/asset/qwerty1"
    # patch_model.level = LevelPathModel.from_level_path(LevelPath.from_path(dest_path)) 
    patch_model.configuration = json_patch

    patched_config: Optional[ConfigModel] = configs_service.patch_config(operator_user=operator, id=config_model_2.id,
                                                                         patch=patch_model, inherit=True)

    assert patched_config is not None
    assert patched_config.name == "a_name"
    assert patched_config.path == "/Mumbai/television/wonder9"
    assert patched_config.configuration.get("h", None) == 77
    assert patched_config.configuration.get("b", None) == 2
    assert patched_config.configuration.get("a", None) == 2
    assert patched_config.configuration.get("q", None) == 99
    assert "j" in patched_config.configuration
    assert patched_config.configuration.get("j", None) == None
    assert "d" in patched_config.configuration
    dict_d: Optional[Dict[str, Any]] = patched_config.configuration.get("d", None)
    assert dict_d is not None
    assert dict_d.get("x", None) == "x_changed"
    assert dict_d.get("y", None) == 0
    assert not "z_added" in dict_d # removed from child dict
    assert not "z" in dict_d # removed from child dict

    assert configs_service.set_config_status(operator_user=operator, id=config_model_2.id,
                                             status_model=ConfigStatusModel(**current_true))

    effective_model_preview: Optional[ConfigModel] = configs_service.get_effective_config_preview(operator_user=operator, id=config_model_2.id, token_dict=None, inherit=True)


    assert effective_model_preview is not None
    assert effective_model_preview.id == config_model_2.id

    effective_model: Optional[ConfigModel] = configs_service.get_effective_config(operator_user=operator, name="a_name",
                                                                                  level_path="/Mumbai/television/wonder9",
                                                                                  token_dict=None)

    assert effective_model is not None
    # assert effective_model.id == config_model_2.id
    assert effective_model == effective_model_preview


def test_patch_config_deleting(test_tables: Any):

    operator: User = User(username="operator1", full_name="Operator 1", email="operator@test.local", groups=set(),
                          token="")

    config_json_1: Dict[str, Any] = {"parent_prop": "val"}

    level_path_model_1: LevelPathModel = LevelPathModel.from_level_path(LevelPath.from_path("/Mumbai/television"))

    create_config_model_1: CreateConfigModel = CreateConfigModel(name="a_name", description="a description",
                                                                 level=level_path_model_1, configuration=config_json_1)

    config_model_1: Optional[ConfigModel] = configs_service.create_config(operator_user=operator,
                                                                          create_config_model=create_config_model_1,
                                                                          inherit=True)

    assert config_model_1 is not None

    config_json_2: Dict[str, Any] = {"child_prop1": "val1",  "child_prop2": "val2"}
    
    level_path_model_2: LevelPathModel = LevelPathModel.from_level_path(
        LevelPath.from_path("/Mumbai/television/wonder9"))

    create_config_model_2: CreateConfigModel = CreateConfigModel(name="a_name", description="a description",
                                                                 level=level_path_model_2, configuration=config_json_2)

    config_model_2: Optional[ConfigModel] = configs_service.create_config(operator_user=operator,
                                                                          create_config_model=create_config_model_2,
                                                                          inherit=True)

    assert config_model_2 is not None

    assert configs_service.set_config_status(operator_user=operator, id=config_model_1.id,
                                             status_model=ConfigStatusModel(**current_true))

    # patch config 2, use the same name and subpath of config 1

    json_patch: Dict[str, Any] = { "parent_prop":"val", "child_prop1":"val1" }

    patch_model: PatchConfigModel = PatchConfigModel()    
    patch_model.configuration = json_patch

    patched_config: Optional[ConfigModel] = configs_service.patch_config(operator_user=operator, id=config_model_2.id,
                                                                         patch=patch_model, inherit=True)

    assert patched_config is not None

    assert configs_service.set_config_status(operator_user=operator, id=config_model_2.id,
                                             status_model=ConfigStatusModel(**current_true))

    effective_model_preview: Optional[ConfigModel] = configs_service.get_effective_config_preview(operator_user=operator, id=config_model_2.id, token_dict=None, inherit=True)

    assert effective_model_preview is not None
    assert effective_model_preview.id == config_model_2.id

    assert "parent_prop" in effective_model_preview.configuration
    assert "child_prop1" in effective_model_preview.configuration
    assert not "child_prop2" in effective_model_preview.configuration
