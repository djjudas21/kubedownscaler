import argparse
import kubernetes

if __name__ == '__main__':
    pass

    # Read in args
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--restore', help="scale up to restore state", action='store_true')
    parser.add_argument('-d', '--dry-run', help="don't actually scale anything", action='store_true')
    parser.add_argument('-n', '--namespace', help="namespace to operate on", type=str)
    args = parser.parse_args()




# connect to cluster
# Determine whether namespaced or global

# if scaling down:
# get all Deployments
# get all Statefulsets
# foreach Deployment
    # discover current replicas
    # annotate with current replicas
    # scale to 0
# foreach Statefulset
    # ""

# if restoring:
# get all Deployments with an annotation
# foreach Deployment
