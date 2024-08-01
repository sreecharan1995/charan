from common.build_settings import BuildSettings


class BuildInfo():
    """Holds details about some related build information gathered during image build time.
    """

    def __init__(self, build_settings: BuildSettings):

        self.id = build_settings.BUILD_ID
        self.date = build_settings.BUILD_DATE
        self.hash = build_settings.BUILD_HASH
        self.link = build_settings.BUILD_LINK
        self.image = build_settings.BUILD_IMAGE
    