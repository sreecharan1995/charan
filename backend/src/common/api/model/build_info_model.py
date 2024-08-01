# coding: utf-8

from __future__ import annotations
from pydantic import BaseModel, Field

from common.domain.build_info import BuildInfo


class BuildInfoModel(BaseModel):
    """The build information represents some attributes attached to the application when was built."""

    build_id: str = Field(default="", title="the build id", example="222")
    build_date: str = Field(default="",
                            title="the build date",
                            example="2022-09-15 12:17:13 EDT")
    build_hash: str = Field(default="",
                            title="the build hash",
                            example="c61353fca13e24f2f407c899b1829f58ae33204d")
    build_image: str = Field(default="",
                            title="the build image",
                            example="301653940240.dkr.ecr.us-east-1.amazonaws.com/scheduler-service:develop-891-4b5b1d9")
    build_link: str = Field(
        default="",
        title="the build link",
        example="https://bitbucket.org/spinvfx/levels_service"
        "/pipelines/results/111")

    @staticmethod
    def from_build_info(build_info: BuildInfo) -> BuildInfoModel:

        build_info_model: BuildInfoModel = BuildInfoModel()

        build_info_model.build_id = build_info.id
        build_info_model.build_date = build_info.date
        build_info_model.build_hash = build_info.hash
        build_info_model.build_link = build_info.link
        build_info_model.build_image = build_info.image

        return build_info_model


BuildInfoModel.update_forward_refs()
