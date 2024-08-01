from typing import List, Optional
from common.domain.k8.container import Container
from kubernetes.client.models.v1_env_from_source import V1EnvFromSource # type: ignore
from kubernetes.client.models.v1_volume_mount import V1VolumeMount # type: ignore
from kubernetes.client.models.v1_volume import V1Volume # type: ignore

class Pod():
    """Wrapper for a k8 pod data
    """

    ip: str
    namespace: str
    name: str
    volumes: List[V1Volume] = []
    containers: List[Container] = []

    def __init__(self, ip: str, namespace: str, name: str, volumes: List[V1Volume]) -> None:
        self.ip = ip
        self.namespace = namespace
        self.name = name
        self.volumes = volumes

    def get_image_name(self, container_index: int = 0)-> Optional[str]:

        if len(self.containers) <= container_index:
            return None
        
        return self.containers[container_index].image        

    def get_env_from_list(self, container_index: int = 0) -> Optional[List[V1EnvFromSource]]:

        if len(self.containers) <= container_index:
            return None        
        
        return self.containers[container_index].env_from
    
    def get_vol_mounts_list(self, container_index: int = 0)-> Optional[List[V1VolumeMount]]:

        if len(self.containers) <= container_index:
            return None        
        
        return self.containers[container_index].vol_mounts