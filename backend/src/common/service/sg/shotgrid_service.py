from typing import Any, Dict, List, Optional

from shotgun_api3 import Fault, Shotgun # type: ignore
from common.domain.division import Division # type: ignore
from common.domain.level_path import LevelPath # type: ignore
from common.domain.parsed_level_path import ParsedLevelPath
from common.domain.sg.shotgrid_project import ShotgridProject
from common.domain.sg.shotgrid_asset import ShotgridAsset
from common.domain.sg.shotgrid_publishedfile import ShotgridPublishedFile
from common.domain.sg.shotgrid_sequence import ShotgridSequence
from common.domain.sg.shotgrid_event import ShotgridEvent
from common.domain.sg.shotgrid_task import ShotgridTask # type: ignore

from common.logger import log
from common.service.sg.sg_settings import SgSettings


class ShotgridService:
    """Provides the methods to operate agains the remote shotgrid service api.

    This class implementation internally uses the shotgun library to talk to shotgrid api.
    """


    _settings: SgSettings
    _sg: Optional[Shotgun] = None

    def __init__(self, settings: SgSettings):
        self._settings = settings

    def __shotgun(self) -> Optional[Shotgun]:

        # TODO: sync access to this method

        if self._sg is not None:
            return self._sg

        try:
            self._sg = Shotgun(
                self._settings.SG_URL,
                script_name=self._settings.SG_SCRIPT_NAME,
                api_key=self._settings.SG_API_KEY,
                connect=False,
                http_proxy=self._settings.SG_PROXY
                if len(self._settings.SG_PROXY) != 0
                else None,
            )
        except BaseException as be:
            log.error(be)
            self._sg = None
            log.warning("Unable to create shotgun")

        return self._sg

    def list_fields(self, entity_type: str):
        
        try:
            schema = self.__shotgun().schema_field_read(entity_type) # type: ignore
            if schema is None:
                log.error(f"shotgun failed: schema_field_read '{entity_type}' failed")
                return None
            log.debug(f"sg node: schema_field_read '{entity_type}': {schema}")
        except Fault as be:
            self._sg = None
            log.error(be)
            return None
        except BaseException as pe:
            self._sg = None
            log.error(f"shotgun error: {pe}")
            return None

        return None

    def find_projects(self, tags_to_avoid: List[str], restrict_to_projects: Optional[List[str]] = None) -> Optional[List[ShotgridProject]]:

        e_type : str = "Project"
                   
        project_filters = [
            {
                "filter_operator": "all",
                "filters": [
                    ["tag_list", "not_in", tags_to_avoid],
                    ["sg_status", "is", "Active"]
                ]
            }
        ]

        if restrict_to_projects is not None:
            restrict_to_projects_filter: Optional[List[int]] = list(map(lambda e: int(e), restrict_to_projects))
        else:
            restrict_to_projects_filter = None

        if restrict_to_projects_filter is not None and len(restrict_to_projects_filter) > 0:
             project_filters[0].get("filters").append(["id", "in", restrict_to_projects_filter ]) # type: ignore
             log.warning(f"Project universe is being restricted to: {restrict_to_projects}")

        try:
            log.debug(f"Finding {e_type} entities")
            projects = self.__shotgun().find(e_type, filters=project_filters, fields=["id", "type", "sg_type", "name", "tag_list"])  # type: ignore
            if projects is None:
                log.error(f"Find {e_type} entities - Shotgun failed")
                return None
        except Fault as be:
            self._sg = None
            log.error(be)
            return None
        except BaseException as pe:
            self._sg = None            
            log.error(f"Find {e_type} entities - Shotgun error: {pe}")
            return None

        return list( filter( lambda p: p is not None, map(lambda i: ShotgridProject(i), projects) ))  # type: ignore
    
    def find_project(self, project_id: int)-> Optional[ShotgridProject]:
                   
        project_filters = [ # auto-restrict to active projects even if project_id is valid
            {
                "filter_operator": "all",
                "filters": [
                    ["sg_status", "is", "Active"]
                ]
            }
        ]

        project_filters[0].get("filters").append(["id", "in", [ project_id ] ]) # type: ignore

        try:
            log.debug(f"Finding project {project_id} entities")
            projects = self.__shotgun().find("Project", filters=project_filters, fields=["id", "type", "sg_type", "name", "tag_list", "meta"])  # type: ignore
            if projects is None or len(projects) != 1: # type: ignore
                log.error(f"Finding project {project_id} entities - Shotgun failed")
                return None
            return ShotgridProject(projects[0]) # type: ignore
        except Fault as be: 
            self._sg = None
            log.error(be)
            return None
        except BaseException as pe:
            self._sg = None            
            log.error(f"Finding project {project_id} entities - Shotgun error: {pe}")
            return None

    def find_project_assets(self, project_id: int) -> Optional[List[ShotgridAsset]]:

        entities: Optional[List[Dict[str,Any]]] = self._get_project_entities(project_id=project_id,
                                                                       entity_type="Asset",
                                                                       fields=["id", "code", "sg_asset_type"])
        
        if entities is None:
            return None
        
        return list(map(lambda i: ShotgridAsset(i), entities))
    
    def find_project_sequences(self, project_id: int) -> Optional[List[ShotgridSequence]]:

        entities: Optional[List[Dict[str,Any]]] = self._get_project_entities(project_id=project_id, 
                                                                             entity_type="Sequence", 
                                                                             fields=["id", "code", "project", "sg_sequence_type", "shots"])

        if entities is None:
            return None
        
        return list(map(lambda i: ShotgridSequence(i), entities))

    def find_project_publishedfile(self, project_id: int, file_id: int)-> Optional[ShotgridPublishedFile]:

        entities: Optional[List[Dict[str,Any]]] = self._get_project_entities(project_id=project_id, entity_type="PublishedFile", fields=["id", "code", "project", "sg_asset", "task"])
        
        filtered: List[Dict[str, Any]] = list(filter(lambda s: s.get("id", None) == file_id, entities or []))

        if len(filtered) == 1:
            return ShotgridPublishedFile(filtered[0])
        
        return None

    def find_project_task(self, project_id: int, task_id: int)-> Optional[ShotgridTask]:

        entities: Optional[List[Dict[str,Any]]] = self._get_project_entities(project_id=project_id, entity_type="Task", fields=["id", "code", "project", "sg_asset", "task", "keys", "product", "sg_variant_set", "sg_production_phase"])
        
        filtered: List[Dict[str, Any]] = list(filter(lambda s: s.get("id", None) == task_id, entities or []))

        if len(filtered) == 1:
            return ShotgridTask(filtered[0])
        
        return None
    
    def _get_project_entities(self, project_id: int, entity_type: str, fields: List[str] = ["*"]) -> Optional[List[Dict[str, Any]]]:

        filters = [
            ["project", "is", {"type": "Project", "id": project_id}],
        ]

        try:
            log.debug(f"Project {project_id} - Finding {entity_type} entities")
            entities = self.__shotgun().find(entity_type, filters=filters, fields=fields)  # type: ignore
            return entities # type: ignore
        except Fault as be:
            self._sg = None
            log.error(be)
            return None
        except BaseException as pe:
            self._sg = None
            log.error(f"Project {project_id} - Find {entity_type} entities - Shotgun error: {pe}")
            return None

    def get_event_level(self, sg_event: ShotgridEvent)-> Optional[ParsedLevelPath]:
        
        project_id: Optional[int] = sg_event.get_project_id()

        if project_id is None:
            log.warning(f"Unable to resolve project id. event: {sg_event.dict()}")
            return None

        sg_project: Optional[ShotgridProject] = self.find_project(project_id)

        if sg_project is None:
            log.warning(f"Unable to resolve project with id: {project_id}.")
            return None

        project_site: Optional[str] = sg_project.get_site()

        if project_site is None:
            log.warning(f"Unable to determine project site. Using default site. event: {sg_event.dict()}")
            project_site: Optional[str] = sg_event.get_site() # event site from event prop if present or default

        project_division_name: Optional[str] = sg_project.get_division_name()

        if project_division_name is None:
            log.warning(f"Unable to resolve project division name. project: {sg_project.project_dict()}")
            return None
        
        project_division: Optional[Division] = Division.get_division_from_text(project_division_name, False)

        if project_division is None:
            log.warning(f"Unknown division with name {project_division_name}")
            return None

        project_name: Optional[str] = sg_project.get_name()

        if project_name is None:
            log.warning(f"Project has no name {sg_project.project_dict()}")
            return None

        log.debug(f"Resolved project level as: /{project_site}/{project_division.name}/{project_name}")
        return ParsedLevelPath.from_level_path(LevelPath.from_path(f"/{project_site}/{project_division.name}/{project_name}"))