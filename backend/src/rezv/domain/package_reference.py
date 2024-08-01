class PackageReference:
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        pass

    def as_version(self) -> str:
        return self.name + "-" + self.version
