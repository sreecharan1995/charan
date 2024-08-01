import re
from typing import Dict, Optional

from fastapi import Request


class Utils:
    """This class contains miscelaneous static methods with utility to other shared and non-shared api code
       of spinvfx microservice implementations.
    """
    
    @staticmethod
    def base_url(req: Optional[Request]):
        """Extracts the host, port and path portions of the url, excluding the query parameters part.
        """

        url = str(req.url or "") if req else ""
        index = url.find("?")

        if index == -1:
            return url

        return url[0:index]

    @staticmethod
    def page_selector(page_number: int, page_size: int, array_length: int):
        """Calculates the starting and ending index of an items page, given the page number and page size, 
           considering the actual total item count in the page
        """
        start_index = page_size * (page_number - 1)
        end_index = start_index + page_size

        if start_index > array_length:
            start_index = 0
            end_index = 0
        if end_index > array_length:
            end_index = array_length

        return start_index, end_index

    @staticmethod
    def extract_dict_from_query_params(req: Request, key_matcher: str = "t_(\\w+)") -> Dict[str,str]:
        """Creates a dictionary based on the t_ prefixed parameters in the query part of an url. 

        The dictionary will have as key the part of the parameter following its t_ prefix, and as value the parameter 
        value as specified in the query for that parameter.
        """

        matched_dict: Dict[str,str] = {}

        params_dict = req.query_params

        for k in params_dict.keys():
            match = re.match(key_matcher, k)
            if match:
                matched_dict[match.group(1)] = params_dict.get(k,"")

        return matched_dict        