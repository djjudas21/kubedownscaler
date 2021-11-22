"""
Scale down Kubernetes Deployments and Statefulsets
and restore them to their original scale
"""

import argparse
from kubernetes import client, config
from kubernetes.client.rest import ApiException


def annotate(api, kind: str, name: str, namespace: str, value: str):
    '''
    Annotate a kube resource with its original number of replicas
    '''
    body = {"metadata": {"annotations": {
        'kubescaledown/originalReplicas': str(value)}}}

    match kind:
        case "Deployment":
            try:
                resp = api.patch_namespaced_deployment(
                    name=name, namespace=namespace, body=body
                )
            except ApiException as e:
                print(
                    f"Exception when calling AppsV1Api->patch_namespaced_deployment: {e}\n")
        case "StatefulSet":
            try:
                resp = api.patch_namespaced_stateful_set(
                    name=name, namespace=namespace, body=body
                )
            except ApiException as e:
                print(
                    f"Exception when calling AppsV1Api->patch_namespaced_stateful_set: {e}\n")

    return resp


# pylint: disable=too-many-arguments
def scale(api, kind: str, name: str, namespace: str, from_replicas: int, to_replicas: int):
    '''
    Scale a kube resource to a new number of replicas
    '''
    print(
        f"Scaling {kind} {namespace}/{name} from {from_replicas} to {to_replicas} replicas")

    body = {"spec": {"replicas": to_replicas}}

    match kind:
        case "Deployment":
            try:
                resp = api.patch_namespaced_deployment_scale(
                    name=name, namespace=namespace, body=body
                )
            except ApiException as e:
                print(
                    f"Exception when calling AppsV1Api->patch_namespaced_deployment_scale: {e}\n")
        case "StatefulSet":
            try:
                resp = api.patch_namespaced_stateful_set_scale(
                    name=name, namespace=namespace, body=body
                )
            except ApiException as e:
                print(
                    f"Exception when calling AppsV1Api->patch_namespaced_stateful_set_scale: {e}\n")

    return resp


def downscale(api, kind: str, obj):
    '''
    Handle the downscaling of an object
    '''
    # Grab some info from the deployment
    namespace = obj.metadata.namespace
    name = obj.metadata.name
    replicas = int(obj.spec.replicas)

    if replicas != 0 and not args.dry_run:
        annotate(api, kind, name, namespace, replicas)
        scale(api, kind, name, namespace, replicas, 0)


def upscale(api, kind: str, obj):
    '''
    Handle the upscaling of an object
    '''
    # Grab some info from the deployment
    namespace = obj.metadata.namespace
    name = obj.metadata.name
    replicas = int(obj.spec.replicas)
    try:
        original_replicas = int(
            obj.metadata.annotations['kubescaledown/originalReplicas'])
    except IndexError:
        return

    # Remove the annotation, and scale back up
    if replicas != original_replicas and not args.dry_run:
        annotate(api, kind, name, namespace, '')
        scale(api, kind, name, namespace, replicas, original_replicas)

# pylint: disable=too-many-branches
def main(args):
    """
    Main function
    """

    # connect to cluster
    config.load_kube_config()
    apps_v1 = client.AppsV1Api()

    # Determine whether namespaced or global, and fetch list of Deployments
    if args.namespace:
        # do namespaced
        if args.deployments:
            try:
                deployments = apps_v1.list_namespaced_deployment(
                    namespace=args.namespace)
            except ApiException as e:
                print(
                    f"Exception when calling AppsV1Api->list_namespaced_deployment: {e}\n")
        if args.statefulsets:
            try:
                statefulsets = apps_v1.list_namespaced_stateful_set(
                    namespace=args.namespace)
            except ApiException as e:
                print(
                    f"Exception when calling AppsV1Api->list_namespaced_stateful_set: {e}\n")
    else:
        # do global
        if args.deployments:
            try:
                deployments = apps_v1.list_deployment_for_all_namespaces()
            except ApiException as e:
                print(
                    f"Exception when calling AppsV1Api->list_deployment_for_all_namespaces: {e}\n")
        if args.statefulsets:
            try:
                statefulsets = apps_v1.list_stateful_set_for_all_namespaces()
            except ApiException as e:
                print(
                    f"Exception when calling AppsV1Api->list_stateful_set_for_all_namespaces: {e}\n")

    if args.up:
        if args.deployments:
            for deployment in deployments.items:
                upscale(apps_v1, "Deployment", deployment)
        if args.statefulsets:
            for statefulset in statefulsets.items:
                upscale(apps_v1, "StatefulSet", statefulset)
    elif args.down:
        if args.deployments:
            for deployment in deployments.items:
                downscale(apps_v1, "Deployment", deployment)
        if args.statefulsets:
            for statefulset in statefulsets.items:
                downscale(apps_v1, "StatefulSet", statefulset)

if __name__ == '__main__':

    # Read in args
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-d', '--down',
                       help="scale down cluster resources", action='store_true')
    group.add_argument('-u', '--up',
                       help="scale up to restore state", action='store_true')
    parser.add_argument(
        '--dry-run', help="don't actually scale anything", action='store_true')
    parser.add_argument('-n', '--namespace',
                        help="namespace to operate on", type=str)
    parser.add_argument("--deployments", help="scale Deployments",
                        default=True, action=argparse.BooleanOptionalAction)
    parser.add_argument("--statefulsets", help="scale StatefulSets",
                        default=True, action=argparse.BooleanOptionalAction)
    args = parser.parse_args()

    main(args)
