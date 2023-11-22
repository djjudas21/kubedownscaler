# kubedownscaler

Scales down Kubernetes Deployments and StatefulSets to 0 replicas, keeps note of the number
of replicas in annotations, and scales everything back up to the original number of replicas.

Can operate on a single namespace, or the entire cluster.
Can operate only on Deployments and StatefulSets that use a specific StorageClass

Ideal for performing a controlled shutdown, maintenance, etc.

Uses whatever context your local `kubectl` has.

## Install

```sh
pip install kubedownscaler
```

## Use

Either `-d|--down` or `-u|--up` must be specified.

```
usage: kubectl downscale [-h] (-d | -u) [--dry-run] [-n NAMESPACE] [--deployments | --no-deployments]
               [--statefulsets | --no-statefulsets] [--storageclass STORAGECLASS]

options:
  -h, --help            show this help message and exit
  -d, --down            scale down cluster resources
  -u, --up              scale up to restore state
  --dry-run             don't actually scale anything
  -n NAMESPACE, --namespace NAMESPACE
                        namespace to operate on
  --deployments, --no-deployments
                        scale Deployments (default: True)
  --statefulsets, --no-statefulsets
                        scale StatefulSets (default: True)
  --storageclass STORAGECLASS
                        only scale Deployments and StatefulSets that are consuming a specific StorageClass
```

## Build

```sh
poetry install
poetry build
poetry publish
```
