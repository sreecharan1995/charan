## coding: utf-8

import jsonpickle  # type: ignore
from common.domain.division import Division
from level.domain.node.asset_node import AssetNode
from level.domain.node.asset_type_node import AssetTypeNode
from level.domain.node.division_node import DivisionNode
from level.domain.node.project_node import ProjectNode
from level.domain.node.root_node import RootNode
from level.domain.node.sequence_node import SequenceNode
from level.domain.node.shot_node import ShotNode


def test_jsonpicke_serialize():

    seq = SequenceNode(id=123, code="code123")

    seq.set_shots([ShotNode(id=1, name="shot1"), ShotNode(id=2, name="shot2")])

    ass1 = AssetNode(id=9, code="a123", type="vehicle")
    ass2 = AssetNode(id=9, code="a123", type="room")

    prj = ProjectNode(id=100, division=Division.TELEVISION, name="ptest")

    prj.get_pathtype_sequence().set_sequences([seq])

    ast1 = AssetTypeNode()

    ast1.set_asset_type(ass1.get_type())
    ast1.add_asset(ass1)

    ast2 = AssetTypeNode()

    ast2.set_asset_type(ass2.get_type())
    ast2.add_asset(ass2)

    prj.get_pathtype_asset().set_asset_types([ast1, ast2])

    div = DivisionNode(division=Division.FILM)

    div.set_projects([prj])

    obj = RootNode(divisions=[div])

    json_data: str = jsonpickle.encode(obj, unpicklable=True, keys=True, warn=True)  # type: ignore

    assert json_data is not None    

    root_node: RootNode = jsonpickle.decode(json_data) # type: ignore

    assert root_node.divisions_count() == 1
    assert root_node.projects_count() == 1
    assert root_node.assets_count() == 2
    assert root_node.asset_types_count() == 2
    assert root_node.sequences_count() == 1
    assert root_node.shots_count() == 2


