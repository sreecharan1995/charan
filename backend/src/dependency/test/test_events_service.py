# coding: utf-8

import pytest

from dependency.api.model.full_profile_model import FullProfileModel
from dependency.service.events_service import EventsService

events_service : EventsService = EventsService()

@pytest.mark.skip(reason="No actual events generated from build environment")
def test_send_verification_event():

    # crear un level profile
    lp : FullProfileModel = FullProfileModel(id="abcdefg", path='/mumbai', name="a name", description="a description", bundles=[], packages=[], comments=[], created_at="", created_by="")

    events_service.on_profile_created(lp) # type: ignore


    