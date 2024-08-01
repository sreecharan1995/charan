# coding: utf-8

from typing import Optional, Set


class User:
    """Represents an actual user or internal user decoded from a token or apikey when using endpoints.
    """
    
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    groups: Optional[Set[str]] = None
    projects: Optional[Set[str]] = None
    token: Optional[str] = None

    def __init__(self, username: str, email: str, full_name: str, groups: Set[str] = set(), projects: Set[str] = set(), token: str = "") -> None:
        self.username = username
        self.email = email
        self.full_name = full_name
        self.groups = groups
        self.projects = projects
        self.token = token        
