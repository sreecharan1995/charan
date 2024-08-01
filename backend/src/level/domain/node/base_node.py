from typing import List, Optional

from level.domain.tree_level import TreeLevel


class BaseNode(object):
    """Represents a abstract node in the internal tree

    All nodes in the internal tree representation has this base class
    """

    _parent: Optional['BaseNode'] = None

    def __init__(self):
        return

    def set_parent(self, parent: 'BaseNode'):
        self._parent = parent

    def get_path(self) -> str:

        if self._parent is None:
            return f"{self._get_path_segment()}"

        path_segment: str = self._get_path_segment()

        if len(path_segment) > 0:
            path_segment = f"{path_segment}/"

        return f"{self._parent.get_path()}{path_segment}"

    # to override in childs
    def _get_path_segment(self) -> str:
        return ""

    def as_level(self, max_depth: int) -> TreeLevel:

        level: TreeLevel = TreeLevel()

        self._fill_level(level)

        level.label = self._get_path_segment()

        if max_depth > 0:
            level.sublevels = self._fill_sublevels(max_depth - 1)

        level.has_sublevels = self._has_sublevels()

        return level

    # to override in childs
    def _fill_level(self, level: TreeLevel):

        if self._parent is not None:
            self._parent._fill_level(level)        
        
        level.path = f"{self.get_path()}"

    # to override in childs
    def _fill_sublevels(self, max_depth: int) -> List[TreeLevel]:
        return []

    # to override in childs
    def _has_sublevels(self) -> bool:
        return False

    # # this is for jsonpickle to ignore _parent when serializing
    # def __getstate__(self):
    #     state = self.__dict__.copy()
    #     state.pop('_parent', None)
    #     return state

    # def __setstate__(self, state): # type: ignore
    #     self.__dict__.update(state) # type: ignore




# @jsonpickle.handlers.register(BaseNode, base=True) # type: ignore
# class BaseNodeHandler(jsonpickle.handlers.BaseHandler):
    
#     def flatten(self, obj, data): # type: ignore
#         return data # type: ignore

#     def restore(self, obj): # type: ignore
#         pass
