# kubedownscaler

Scale down all deployments and statefulsets to 0, keep note of replicas in:
- a file
- or in annotations on the resources it touches

Restore original scale

Uses whatever context your local kubectl has


