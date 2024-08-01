
from typing import List
from rez.exceptions import RezError # type: ignore
from rez.resolved_context import ResolvedContext # type: ignore

from common.logger import log
from rezv.domain.validation_result import ValidationResult
from rezv.domain.validation_request import ValidationRequest
from rezv.service.events_service import EventsService
from rezv.rez_settings import RezSettings
# from vendor.version.util import VersionError

class RezService():

    _events_service: EventsService

    def __init__(self, settings: RezSettings = RezSettings.load()):
        self._events_service = EventsService(settings)

    def build_cache(self, request: ValidationRequest):

        log.info("Received event")

        packages: List[str] = []

        for p in request.get_packages():
            packages.append(p['name'] + "-" + p['version'])

        for b in request.get_bundles():
            for p in b['packages']:
                if 'use_legacy' not in p or not p['use_legacy']:
                    packages.append(p['name'] + "-" + p['version'])

        if len(packages) > 0:
            log.info("Resolving packages: %s", packages)
        else:
            log.warning("No packages found in the validation request.")
            return

        try:

            c = ResolvedContext(package_requests=packages)

            log.info("ResolvedContext: %s", c)

            self._events_service.on_profile_validated(ValidationResult(request, resolved_context=c))

    #    except (RezError, VersionError) as ex:
        except (RezError) as ex: # TODO: TBI: VersionError? can't find
            self._events_service.on_profile_validated(ValidationResult(request, exception=ex))


