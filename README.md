# kubedownscaler

Scales down all Deployments and StatefulSets to 0, keeps note of the number of replicas in annotations,
and scales everything back up to the original number of replicas.

Ideal for performing a controlled shutdown, maintenance, etc.

Uses whatever context your local kubectl has

## Install

```sh
pip install kubedownscaler
```

## Use

Either `-d|--down` or `-u|--up` must be specified.

```
usage: main.py [-h] (-d | -u) [--dry-run] [-n NAMESPACE] [--deployments | --no-deployments]
               [--statefulsets | --no-statefulsets]

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
```

## Build

```sh
poetry install
poetry build
poetry publish
```
