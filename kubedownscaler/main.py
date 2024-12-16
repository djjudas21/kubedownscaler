"""
Scale down Kubernetes Deployments and Statefulsets
and restore them to their original scale
"""

import argparse
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from termcolor import cprint

def annotate(api, kind: str, name: str, namespace: str, value: str):
    '''
    Annotate a kube resource with its original number of replicas
    '''
    # Replace empty string with None, to cause it to be removed
    if value == '':
        value = None
    else:
        value = str(value)
    
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

    if to_replicas > from_replicas:
        colour = 'green'
    elif to_replicas < from_replicas:
        colour = 'red'
    else:
        colour = 'yellow'

    cprint(
        f"Scaling {kind} {namespace}/{name} from {from_replicas} to {to_replicas} replicas", colour)

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


def downscale(api, kind: str, obj, dry_run: bool):
    '''
    Handle the downscaling of an object
    '''
    # Grab some info from the deployment
    namespace = obj.metadata.namespace
    name = obj.metadata.name
    replicas = int(obj.spec.replicas)

    if replicas != 0 and not dry_run:
        annotate(api, kind, name, namespace, replicas)
        scale(api, kind, name, namespace, replicas, 0)


def upscale(api, kind: str, obj, dry_run: bool):
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
    except ValueError:
        return
    except KeyError:
        return

    # Remove the annotation, and scale back up
    if replicas != original_replicas and not dry_run:
        annotate(api, kind, name, namespace, '')
        scale(api, kind, name, namespace, replicas, original_replicas)

# pylint: disable=too-many-branches
def main():
    """
    Main function
    """

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
    parser.add_argument("--storageclass", help="only scale pods that are consuming a specific storageclass",
                        type=str)
    args = parser.parse_args()

    # connect to cluster
    config.load_kube_config()
    apps_v1 = client.AppsV1Api()
    core_v1 = client.CoreV1Api()

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

    # remove any deployment or statefulset from the list that doesn't reference this storageclass
    if args.storageclass:

        # for deployments, get the PVCs from the Deployment and get the SC from the PVC
        for deployment in deployments.items:
            to_be_scaled = False

            # get full deployment details
            try:
                deploymentspec = apps_v1.read_namespaced_deployment(name=deployment.metadata.name, namespace=deployment.metadata.namespace)
                deploymentnamespace = deploymentspec.metadata.namespace
            except ApiException as e:
                print(f"Exception when calling AppsV1Api->read_namespaced_deployment: {e}\n")

            # get PVCs from Deployment            
            for volume in deploymentspec.spec.template.spec.volumes:
                if volume.persistent_volume_claim is not None:

                    # get pvc details & get storageclass
                    try:
                        pvc = core_v1.read_namespaced_persistent_volume_claim(volume.persistent_volume_claim.claim_name, deploymentnamespace)
                        sc = pvc.spec.storage_class_name
                    except ApiException as e:
                        print(f"Exception when calling CoreV1Api->read_namespaced_persistent_volume_claim: {e}\n")

                    # if storageclass is the one we're looking for, set flag
                    if sc == args.storageclass:
                        to_be_scaled = True
        
            if to_be_scaled is False:
                deployments.items.remove(deployment)

        # for statefulsets, the SC is listed directly in the statefulset
        for statefulset in statefulsets.items:
            to_be_scaled = False

            # get statefulset details
            try:
                statefulsetspec = apps_v1.read_namespaced_stateful_set(name=statefulset.metadata.name, namespace=statefulset.metadata.namespace)
            except ApiException as e:
                print(f"Exception when calling AppsV1Api->read_namespaced_stateful_set: {e}\n")

            # get storageclass
            for volume_claim_template in statefulsetspec.spec.volume_claim_templates:
                sc = volume_claim_template.spec.storage_class_name
                # if storageclass is the one we're looking for, set flag
                if sc == args.storageclass:
                    to_be_scaled = True

            if to_be_scaled is False:
                statefulsets.items.remove(statefulset)

    if args.up:
        if args.deployments:
            for deployment in deployments.items:
                upscale(apps_v1, "Deployment", deployment, args.dry_run)
        if args.statefulsets:
            for statefulset in statefulsets.items:
                upscale(apps_v1, "StatefulSet", statefulset, args.dry_run)
    elif args.down:
        if args.deployments:
            for deployment in deployments.items:
                downscale(apps_v1, "Deployment", deployment, args.dry_run)
        if args.statefulsets:
            for statefulset in statefulsets.items:
                downscale(apps_v1, "StatefulSet", statefulset, args.dry_run)

if __name__ == '__main__':
    main()
