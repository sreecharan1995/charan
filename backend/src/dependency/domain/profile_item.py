import re


class ProfileItem:
    """Represents a profile.
    """
    
    @staticmethod
    def is_name_valid(name: str) -> bool:    
        return name is not None and re.fullmatch("\\w[\\w-]*", name) is not None