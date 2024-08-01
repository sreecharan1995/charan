# coding: utf-8

from fastapi import APIRouter, Depends, Request

from common.api.model.status_model import StatusModel
from common.auth.auth_manager import AuthManager, Permission
from common.domain.user import User
from common.logger import log
from sourcing import event_stats
from sourcing.api.auth.sourcing_resource import (ACTION_VIEW_STATS,
                                                 SourcingResource)
from sourcing.api.model.event_stats_model import EventStatsModel
from sourcing.service.sourcing_service import SourcingService
from sourcing.sourcing_settings import SourcingSettings

router = APIRouter()
settings: SourcingSettings = SourcingSettings.load()

sourcing_service: SourcingService = SourcingService(settings)


@router.get(
    "/stats",
    responses={
        200: {
            "model": EventStatsModel,
            "description": "Stats info returned"
        },
        401: {
            "model": StatusModel,
            "description": "Unauthenticated"
        },
        403: {
            "model": StatusModel,
            "description": "Unauthorized"
        },
    },
    tags=["info"],
    summary="Retrieve event counts and stats",
)
async def get_stats(
        req: Request,
        br: SourcingResource = Permission(ACTION_VIEW_STATS, SourcingResource),
        user: User = Depends(AuthManager.from_token),
) -> EventStatsModel:
    """Retrieves the event counts per type and total for the last hour"""
    ...

    log.info(f"User '{user.username}' accessing stats")

    stats_model: EventStatsModel = EventStatsModel.from_stats(
        event_stats.counts()[1])

    return stats_model
