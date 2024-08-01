import time
from typing import Optional

from level.domain.node.root_node import RootNode
from level.domain.sync_request import SyncRequest


class Tree:
    """Represents the node tree in service
    """

    _root_node: RootNode
    _sync_request: SyncRequest
    _since: int

    def __init__(self, root_node: RootNode, sync_request: SyncRequest):

        self._since = time.time_ns()
        self._root_node = root_node
        self._sync_request = sync_request

    def get_since(self, in_seconds: bool = True) -> int:

        if in_seconds:
            return int((1.0 * self._since) / (10**9))
        else:
            return self._since

    def get_uptime(self, in_seconds: bool = True) -> int:

        ns: int = time.time_ns() - self._since

        if in_seconds:
            return int((1.0 * ns) / (10**9))
        else:
            return time.time_ns() - self._since

    def get_sync_request(self) -> SyncRequest:

        return self._sync_request

    def get_root(self) -> RootNode:

        return self._root_node

    def get_filename(self) -> Optional[str]:

        return self._sync_request.filename

    def is_older_than(self, id: int) -> bool:

        return self._sync_request.id < id
