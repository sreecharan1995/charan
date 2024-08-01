# coding: utf-8

from __future__ import annotations


class SyncRequest:
    """Represents a sync request
    """

    id: int    
    comment: str
    filename: str

    def __init__(self, id: int, comment: str = "", filename: str =""):
        self.id = id
        self.comment = comment
        self.filename = filename
