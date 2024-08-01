from typing import List, Optional

from kubernetes import client, config  # type: ignore
from kubernetes.client.exceptions import ApiException  # type: ignore
from kubernetes.client.models.v1_container import V1Container  # type: ignore
from kubernetes.client.models.v1_env_from_source import V1EnvFromSource # type: ignore 
from kubernetes.client.models.v1_env_var import V1EnvVar # type: ignore 
from kubernetes.client.models.v1_job import V1Job  # type: ignore
from kubernetes.client.models.v1_pod import V1Pod  # type: ignore
from kubernetes.client.models.v1_pod_spec import V1PodSpec  # type: ignore
from kubernetes.client.models.v1_volume import V1Volume  # type: ignore
from kubernetes.client.models.v1_volume_mount import V1VolumeMount  # type: ignore

from common.domain.k8.container import Container
from common.domain.k8.job import Job
from common.domain.k8.pod import Pod
from common.logger import log

DEFAULT_NAMESPACE: str = "dev"


class K8():
    """Methods to interact with the remote kubernete service.
    """

    def __init__(self) -> None:
        try:
            config.load_config()  # type: ignore
        except BaseException as be:
            log.error(f"Unable to load kubernetes configuration. {be}")

    def list_pods(self,
                  namespace: str = DEFAULT_NAMESPACE) -> Optional[List[Pod]]:

        try:
            v1 = client.CoreV1Api()
            r = v1.list_namespaced_pod(namespace=namespace)  # type: ignore
        except BaseException as be:
            log.error(f"Error retrieving pods. {be}")
            return None

        if r is None:
            return None

        list: List[V1Pod] = r.items  # type: ignore

        pod_list: List[Pod] = []

        if list is None:  # type: ignore
            return []

        p: V1Pod
        for p in list:
            ip: str = p.status.pod_ip  # type: ignore
            ns: str = p.metadata.namespace  # type: ignore
            name: str = p.metadata.name  # type: ignore
            pod: Pod = Pod(ip=ip, namespace=ns, name=name, volumes=[])
            pod_list.append(pod)

        return pod_list

    def list_jobs(self,
                  namespace: str = DEFAULT_NAMESPACE) -> Optional[List[Job]]:

        try:
            v1 = client.BatchV1Api()
            r = v1.list_namespaced_job(namespace=namespace)  # type: ignore
        except BaseException as be:
            log.error(f"Error retrieving jobs. {be}")
            return None

        if r is None:
            return None

        list: List[Job] = []

        if r.items is None:  # type: ignore
            return []

        for i in r.items:  # type: ignore
            ns: str = i.metadata.namespace  # type: ignore
            name: str = i.metadata.name  # type: ignore
            status: str = i.status  # type: ignore
            job: Job = Job(name=name, namespace=ns, status=status)
            list.append(job)

        return list

    def get_pod(self,
                pod_name: str,
                namespace: str = DEFAULT_NAMESPACE,
                raise_errors: bool = False) -> Optional[Pod]:

        try:
            v1 = client.CoreV1Api()
            p: Optional[V1Pod] = v1.read_namespaced_pod(  # type: ignore
                name=pod_name, namespace=namespace)
        except ApiException as ae:
            if ae.status is not None and ae.status == 404:  # type: ignore
                return None
            else:
                if raise_errors:
                    raise ae
                else:
                    return None
        except BaseException as be:
            log.error(f"Error retrieving pod. {be}")
            if raise_errors:
                raise be
            else:
                return None

        if p is None:
            return None

        ip: str = p.status.pod_ip  # type: ignore
        ns: str = p.metadata.namespace  # type: ignore
        name: str = p.metadata.name  # type: ignore

        spec: V1PodSpec = p.spec  # type: ignore
        volumes: List[V1Volume] = p.spec.volumes or []  # type: ignore

        pod: Pod = Pod(ip=ip, namespace=ns, name=name,
                       volumes=volumes)  # type: ignore

        c: V1Container

        if len(spec.containers) > 0:  # type: ignore
            for c in spec.containers:  # type: ignore
                pod.containers.append(
                    Container(
                        name=c.name,  # type: ignore
                        image=c.image,  # type: ignore
                        env_from=c.env_from,  # type: ignore
                        vol_mounts=c.volume_mounts))  # type: ignore

        return pod

    def get_job(self,
                job_name: str,
                namespace: str = DEFAULT_NAMESPACE,
                raise_errors: bool = False) -> Optional[Job]:

        try:
            v1 = client.BatchV1Api()
            r = v1.read_namespaced_job( # type: ignore
                name=job_name,  
                namespace=namespace)
        except ApiException as ae:
            if ae.status is not None and ae.status == 404:  # type: ignore
                return None
            else:
                if raise_errors:
                    raise ae
                else:
                    return None
        except BaseException as be:
            log.error(f"Error retrieving job. {be}")
            if raise_errors:
                raise be
            else:
                return None

        if r is None:
            return None

        ns: str = r.metadata.namespace  # type: ignore
        name: str = r.metadata.name  # type: ignore
        status: str = r.status  # type: ignore
        job: Job = Job(name=name, namespace=ns, status=status)

        return job

    def create_job(self,
                   job_name: str,
                   image: str,
                   app_name: str,
                   command: List[str],
                   env_from: List[V1EnvFromSource] = [],
                   env_list: List[V1EnvVar] = [],
                   vols: List[V1Volume] = [],
                   vol_mounts: List[V1VolumeMount] = [],
                   restart_policy: str = "Never",
                   ttl_seconds: int = 60 * 60,
                   backoff_limit: int = 5,
                   namespace: str = DEFAULT_NAMESPACE) -> None:

        try:
            v1 = client.BatchV1Api()
            job_object: V1Job = self._create_job_object(
                job_object_name=job_name,
                image=image,                
                app_name=app_name,
                command=command,
                env_from=env_from,
                env_list=env_list,
                vols=vols,
                vol_mounts=vol_mounts,
                restart_policy=restart_policy,
                ttl_seconds=ttl_seconds,
                backoff_limit=backoff_limit)
            j: V1Job = v1.create_namespaced_job(  # type: ignore
                namespace=namespace, body=job_object)
        except BaseException as be:
            log.error(f"Error creating jobs. {be}")
            return None

        if j is None or j.metadata is None:  # type: ignore
            return None

        return Job(
            name=j.metadata.name,  # type: ignore
            namespace=j.metadata.namespace,  # type: ignore
            status=j.status)  # type: ignore

    def _create_job_object(self,
                           job_object_name: str,
                           app_name: str,
                           image: str,
                           command: List[str],
                           env_from: List[V1EnvFromSource] = [],
                           env_list: List[V1EnvVar] = [],
                           vols: List[V1Volume] = [],
                           vol_mounts: List[V1VolumeMount] = [],
                           restart_policy: str = "Never",
                           backoff_limit: int = 5,
                           ttl_seconds: int = 60 * 60) -> V1Job:

        # configurate Pod template container
        container = client.V1Container(name=f"{job_object_name}",
                                       image=f"{image}",
                                       image_pull_policy="Always",
                                       env_from=env_from,
                                       env=env_list,
                                       volume_mounts=vol_mounts,
                                       command=command)

        # create and configure a spec section
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": f"{app_name}"}),
            spec=client.V1PodSpec(restart_policy=restart_policy,
                                  volumes=vols,
                                  containers=[container]))

        # create the specification of deployment
        spec = client.V1JobSpec(
            template=template,
            ttl_seconds_after_finished=ttl_seconds,  
            backoff_limit=backoff_limit)

        # Instantiate the job object
        job = client.V1Job(api_version="batch/v1",
                           kind="Job",
                           metadata=client.V1ObjectMeta(name=job_object_name),
                           spec=spec)

        return job
