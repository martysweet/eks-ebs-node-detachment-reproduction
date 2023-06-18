from kubernetes import client, config
import yaml
from pathlib import Path

# Load the Kubernetes configuration from the default location
config.load_kube_config()

# Create a Kubernetes API client
api_client = client.ApiClient()
api_instance = client.AppsV1Api(api_client)
api_core = client.CoreV1Api(api_client)

def main():
    #create_stateful_set()


    # Find the two nodes we want to cycle
    nodes = api_core.list_node(label_selector="node_role=test").items
    node_names = [n.metadata.name for n in nodes]
    print(node_names)

    for n in node_names:
        set_unschedulable(n, False)

    # Ensure both are scheduleable
    scheduled = 0

    drain(node_names[scheduled])

    # Forever

    # drain 1

    # Wait for pod to become running


def set_unschedulable(name, unschedulable):
    # Cordon the node
    spec = {
        "node": {
            "spec": {
                "unschedulable": unschedulable
            }
        }
    }
    api_core.patch_node(name, spec)

def drain(name):
    # Drain the node
    evict = client.V1beta1Eviction(
        metadata=client.V1ObjectMeta(
            name="drain-node"
        ),
        delete_options=client.V1DeleteOptions(
            grace_period_seconds=60
        )
    )
    evict.metadata.annotations = {
        "cluster-autoscaler.kubernetes.io/safe-to-evict": "false",
        "eviction.kubernetes.io/ignore-daemonsets": "true",
        "eviction.kubernetes.io/ignore-pods-with-local-storage": "true"
    }
    api_core.create_node_eviction(name, evict)

def create_stateful_set():
    statefulset_manifest = yaml.safe_load(Path('manifests/statefulset.yml').read_text())

    # Create the StatefulSet
    try:
        response = api_instance.delete_namespaced_stateful_set(
            name="web",
            namespace="default",
            body=statefulset_manifest
        )
    except Exception as e:
        print(e)

    response = api_instance.create_namespaced_stateful_set(
        namespace="default",
        body=statefulset_manifest
    )

    print("StatefulSet created/updated. Status: %s" % str(response.status))


if __name__ == "__main__":
    main()
