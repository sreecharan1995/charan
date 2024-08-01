from typing import List, Optional

from common.domain.division import Division
from common.domain.path_type import PathType
from common.domain.site import Site


class TreeLevel():
    """Class to internally represent a tree level
    """

    label: Optional[str] = None
    path: Optional[str] = None
    site: Optional[Site] = None
    division: Optional[Division] = None
    project: Optional[str] = None
    sublevels: List['TreeLevel'] = []
    has_sublevels: bool
    type: Optional[PathType] = None
    
    # for type 'asset'
    asset_type: Optional[str] = None
    asset_code: Optional[str] = None

    # for type 'sequence'
    sequence_name: Optional[str] = None
    shot_name: Optional[str] = None

    