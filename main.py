import argparse
from kubernetes import client, config
from kubernetes.client.rest import ApiException


def annotate(kind: str, name: str, namespace: str, value: str):

    body = {"metadata": {"annotations": {
        'kubescaledown/originalReplicas': str(value)}}}
    
    match kind:
        case "Deployment":
            try:
                resp = apps_v1.patch_namespaced_deployment(
                    name=name, namespace=namespace, body=body
                )
            except ApiException as e:
                print("Exception when calling AppsV1Api->patch_namespaced_deployment: %s\n" % e)
        case "StatefulSet":
            try:
                resp = apps_v1.patch_namespaced_stateful_set(
                    name=name, namespace=namespace, body=body
                )
            except ApiException as e:
                print("Exception when calling AppsV1Api->patch_namespaced_stateful_set: %s\n" % e)

    return resp


def scale(kind: str, name: str, namespace: str, fromReplicas: int, toReplicas: int):

    print(f"Scaling {kind} {namespace}/{name} from {fromReplicas} to {toReplicas} replicas")

    body = {"spec": {"replicas": toReplicas}}

    match kind:
        case "Deployment":
            try:
                resp = apps_v1.patch_namespaced_deployment_scale(
                    name=name, namespace=namespace, body=body
                )
            except ApiException as e:
                print("Exception when calling AppsV1Api->patch_namespaced_deployment_scale: %s\n" % e)
        case "StatefulSet":
            try:
                resp = apps_v1.patch_namespaced_stateful_set_scale(
                    name=name, namespace=namespace, body=body
                )
            except ApiException as e:
                print("Exception when calling AppsV1Api->patch_namespaced_stateful_set_scale: %s\n" % e)

    return resp



def down(kind, object):
    # Grab some info from the deployment
    namespace = object.metadata.namespace
    name = object.metadata.name
    #kind = object.kind
    replicas = int(deployment.spec.replicas)

    if replicas != 0 and not args.dry_run:
        annotate(kind, name, namespace, replicas)
        scale(kind, name, namespace, replicas, 0)


def up(kind, object):
    # Grab some info from the deployment
    namespace = object.metadata.namespace
    name = object.metadata.name
    #kind = object.kind
    replicas = int(object.spec.replicas)
    try:
        originalReplicas = int(
            object.metadata.annotations['kubescaledown/originalReplicas'])
    except:
        return

    # Remove the annotation, and scale back up
    if replicas != originalReplicas and not args.dry_run:
        annotate(kind, name, namespace, '')
        scale(kind, name, namespace, replicas, originalReplicas)


if __name__ == '__main__':
    pass

    # Read in args
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-d', '--down',
                        help="scale down cluster resources", action='store_true')
    group.add_argument('-u', '--up',
                        help="scale up to restore state", action='store_true')
    parser.add_argument('--dry-run', help="don't actually scale anything", action='store_true')
    parser.add_argument('-n', '--namespace',
                        help="namespace to operate on", type=str)
    parser.add_argument("--deployments", help="scale Deployments", default=True, action=argparse.BooleanOptionalAction)
    parser.add_argument("--statefulsets", help="scale StatefulSets", default=True, action=argparse.BooleanOptionalAction)
    args = parser.parse_args()

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
                    "Exception when calling AppsV1Api->list_namespaced_deployment: %s\n" % e)
        if args.statefulsets:
            try:
                statefulsets = apps_v1.list_namespaced_stateful_set(
                    namespace=args.namespace)
            except ApiException as e:
                print(
                    "Exception when calling AppsV1Api->list_namespaced_stateful_set: %s\n" % e)
    else:
        # do global
        if args.deployments:
            try:
                deployments = apps_v1.list_deployment_for_all_namespaces()
            except ApiException as e:
                print(
                    "Exception when calling AppsV1Api->list_deployment_for_all_namespaces: %s\n" % e)
        if args.statefulsets:
            try:
                statefulsets = apps_v1.list_stateful_set_for_all_namespaces()
            except ApiException as e:
                print(
                    "Exception when calling AppsV1Api->list_stateful_set_for_all_namespaces: %s\n" % e)

    if args.up:
        if args.deployments:
            for deployment in deployments.items:
               up("Deployment", deployment)
        if args.statefulsets:
            for statefulset in statefulsets.items:
                up("StatefulSet", statefulset)
    elif args.down:
        if args.deployments:
            for deployment in deployments.items:
                down("Deployment", deployment)
        if args.statefulsets:
            for statefulset in statefulsets.items:
                down("StatefulSet", statefulset)
