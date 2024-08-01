from typing import List, Optional
from kubernetes.client.models.v1_env_from_source import V1EnvFromSource # type: ignore
from kubernetes.client.models.v1_volume_mount import V1VolumeMount # type: ignore


class Container():
    """Wrapper for a k8 container data
    """

    name: str
    image: str
    env_from: List[V1EnvFromSource]
    vol_mounts: List[V1VolumeMount]


    def __init__(self, name: str, image: str, env_from: Optional[List[V1EnvFromSource]], vol_mounts: Optional[List[V1VolumeMount]]) -> None:

        self.name = name
        self.image = image
        self.env_from = env_from or []
        self.vol_mounts = vol_mounts or []
