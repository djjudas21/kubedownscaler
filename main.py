import argparse
from kubernetes import client, config
from kubernetes.client.rest import ApiException


def annotate(name, namespace, value):

    body = {"metadata": {"annotations": {
        'kubescaledown/originalReplicas': str(value)}}}
    resp = apps_v1.patch_namespaced_deployment(
        name=name, namespace=namespace, body=body
    )

    return resp


def scale(name: str, namespace: str, replicas: int):

    body = {"spec": {"replicas": replicas}}
    resp = apps_v1.patch_namespaced_deployment_scale(
        name=name, namespace=namespace, body=body
    )

    return resp


if __name__ == '__main__':
    pass

    # Read in args
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--restore',
                        help="scale up to restore state", action='store_true')
    parser.add_argument(
        '-d', '--dry-run', help="don't actually scale anything", action='store_true')
    parser.add_argument('-n', '--namespace',
                        help="namespace to operate on", type=str)
    args = parser.parse_args()

    # connect to cluster
    config.load_kube_config()
    apps_v1 = client.AppsV1Api()

    # Determine whether namespaced or global, and fetch list of Deployments
    if args.namespace:
        # do namespaced
        try:
            deployments = apps_v1.list_namespaced_deployment(
                namespace=args.namespace)
        except ApiException as e:
            print(
                "Exception when calling AppsV1Api->list_namespaced_deployment: %s\n" % e)
    else:
        # do global
        try:
            deployments = apps_v1.list_deployment_for_all_namespaces()
        except ApiException as e:
            print(
                "Exception when calling AppsV1Api->list_deployment_for_all_namespaces: %s\n" % e)

    if args.restore:
        for deployment in deployments.items:
            # Grab some info from the deployment
            namespace = deployment.metadata.namespace
            name = deployment.metadata.name
            replicas = int(deployment.spec.replicas)
            try:
                originalReplicas = int(
                    deployment.metadata.annotations['kubescaledown/originalReplicas'])
            except:
                continue

            print(
                f"Scaling {namespace}/{name} from {replicas} to {originalReplicas} replicas")

            if replicas == originalReplicas:
                continue

            # Remove the annotation, and scale back up
            annotate(name, namespace, '')
            scale(name, namespace, originalReplicas)
    else:
        for deployment in deployments.items:
            # Grab some info from the deployment
            namespace = deployment.metadata.namespace
            name = deployment.metadata.name
            replicas = int(deployment.spec.replicas)

            if replicas == 0:
                continue

            print(f"Scaling {namespace}/{name} from {replicas} to 0 replicas")

            annotate(name, namespace, replicas)
            scale(name, namespace, 0)
