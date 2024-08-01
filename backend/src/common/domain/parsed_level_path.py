from typing import List, Optional

from common.domain.division import Division
from common.domain.level_path import LevelPath
from common.domain.path_type import PathType
from common.domain.site import Site


class ParsedLevelPath:
    """Represents a parsed resource path.

    The normalized path structure is read and each section syntax or correctness is verified and represented, but 
    the actual existence of the path is nont guaranteed.
    """

    site: Optional[Site] = None
    division: Optional[Division] = None
    show: Optional[str] = None

    type: Optional[PathType] = None  # this is for:  asset | sequence

    # when type is 'asset':
    asset_type: Optional[str] = None
    asset_code: Optional[str] = None

    # when type is 'sequence':
    sequence_name: Optional[str] = None
    shot_name: Optional[str] = None

    def to_level_path(self) -> LevelPath:
        """Creates a normalized path instance which can be mapped to a string representation.
        """

        if self.type == PathType.ASSET:
            return LevelPath(path=f"/{self.site.value if self.site is not None else ''}/{self.division.value if self.division is not None else ''}/{self.show or ''}/{PathType.ASSET.value}/{self.asset_type or ''}/{self.asset_code or ''}")
        elif self.type == PathType.SEQUENCE:
            return LevelPath(path=f"/{self.site.value if self.site is not None else ''}/{self.division.value if self.division is not None else ''}/{self.show or ''}/{PathType.SEQUENCE.value}/{self.sequence_name or ''}/{self.shot_name or ''}")
        else:
            return LevelPath(path=f"/{self.site.value if self.site is not None else ''}/{self.division.value if self.division is not None else ''}/{self.show or ''}")

    @staticmethod
    def from_level_path(level_path: LevelPath) -> Optional["ParsedLevelPath"]:
        """Returns an instance from a canonized path representation.
        """
        
        canonized_path: str = level_path.get_path()

        canonized_path = canonized_path[1:] # remove the leading / so first segment is site
        
        segments: List[str] = canonized_path.split("/") if canonized_path.find("/") != -1 else [canonized_path]

        parsed_path: ParsedLevelPath = ParsedLevelPath()

        count: int = len(segments)

        if count == 0 or (count == 1 and len(segments[0]) == 0):
            return parsed_path

        if count >= 1:

            site: Optional[Site] = Site.get_site_from_text(segments[0])

            if site is None:
                return None

            parsed_path.site = site

        if count >= 2:

            division: Optional[Division] = Division.get_division_from_text(
                segments[1], True
            )

            if division is None:
                return None

            parsed_path.division = division

        if count >= 3:

            parsed_path.show = segments[2]

        if count >= 4:

            type = PathType.get_type_from_text(segments[3])

            if type is None:
                return None

            parsed_path.type = type

        if count >= 5:

            if parsed_path.type == PathType.ASSET:
                parsed_path.asset_type = segments[4]
                if count >= 6:
                    parsed_path.asset_code = segments[5]

            if parsed_path.type == PathType.SEQUENCE:
                parsed_path.sequence_name = segments[4]
                if count >= 6:
                    parsed_path.shot_name = segments[5]

        return parsed_path

    @staticmethod
    def is_path_acceptable(path: str) -> bool:
        """Validates if a resource path is syntactically correct by normalizing and parsing.
        """
        return  path is not None and ParsedLevelPath.from_level_path(LevelPath.from_path(path)) is not None