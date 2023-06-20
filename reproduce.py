from kubernetes import client, config
import yaml
import time
import datetime
from pathlib import Path
from termcolor import colored

STATEFUL_SET_NAME="ebstest"
POD_NAME="ebstest-0"

NODE_SELECTOR="node_role=test"
WAIT_RUNNING_DELAY=5

# Load the Kubernetes configuration from the default location
config.load_kube_config()

# Create a Kubernetes API client
api_client = client.ApiClient()
api_instance = client.AppsV1Api(api_client)
api_core = client.CoreV1Api(api_client)
api_storage = client.StorageV1Api(api_client)

# To reproduce the issue, we need to:
# 1. Create a StatefulSet
# 2. Find the two nodes that we have allocated for testing
# 3. Set both nodes to unschedulable
# 4. Kill the pod
# 5. Set one node to schedulable
# 6. Wait for the pod to be scheduled
# 7. Set the other node to schedulable
# 8. Kill the pod
# 9. Repeat from step 5



def main():
    # Prepare the environment
    fmt_print("Preparing environment")
    delete_stateful_set()

    # Find the two nodes we want to cycle
    nodes = get_nodes()
    if len(nodes) != 2:
        raise Exception("Expected 2 nodes, found %d" % len(nodes))

    # Set first node for scheduling
    selected = 0
    set_unschedulable(nodes[selected], False)
    set_unschedulable(nodes[1-selected], True)

    # Create the StatefulSet which will schedule on the selected node
    create_stateful_set()

    # Loop forever
    iteration = 1
    while True:
        fmt_print("========== ITERATION {} ==========".format(iteration))
        fmt_print("Waiting for pod to become running on node: {}".format(nodes[selected]))
        wait_for_running_pod()
        time.sleep(2)

        # Set current node to unschedulable, and the other to schedulable
        selected = 1-selected
        set_unschedulable(nodes[selected], False)
        set_unschedulable(nodes[1-selected], True)

        # Kill the pod
        kill_pod()
        iteration += 1

def kill_pod():
    # Delete the pod
    fmt_print("Deleting pod in 5 seconds...")
    # We can expect the scheduler to immediately schedule the pod on the other node
    time.sleep(5)
    api_core.delete_namespaced_pod(
        name=POD_NAME,
        namespace="default",
        body=client.V1DeleteOptions(
            grace_period_seconds=0
        )
    )

def wait_for_running_pod():
    # Wait for the pod to be running
    count = 0
    while True:
        count += 1

        try:
            pod = api_core.read_namespaced_pod(
                name=POD_NAME,
                namespace="default"
            )

            if pod.status.phase == "Running":
                return

            if count % 10:
                fmt_print("Still waiting for pod to become running after {} sec. State: {}. {}".format(
                    count * WAIT_RUNNING_DELAY,
                    colored(pod.status.phase, "red"),
                    get_va_status()
                ))

        except Exception as e:
            if e.status == 404:
                fmt_print("Pod not found")
            else:
                print(e)

        time.sleep(WAIT_RUNNING_DELAY)

def get_va_status():
    nodes = get_nodes()
    count = {node: 0 for node in nodes}

    # Output the volume attachments summary for each node
    response = api_storage.list_volume_attachment()
    for attachment in response.items:
        if attachment.spec.node_name in nodes:
            count[attachment.spec.node_name] += 1

    # Strip the names to show only before FQDN
    # ip-10-0-0-47.eu-west-1.compute.internal => ip-10-0-0-47
    # Output as ip-10-0-0-47=colored(1, "red"), ip-10-0-0-48=colored(2, "red")
    x = ["{}: {}".format(k.split(".")[0], colored(v, "red")) for k, v in count.items()]
    return " | ".join(x)


def get_nodes():
    nodes = api_core.list_node(label_selector=NODE_SELECTOR).items
    return [n.metadata.name for n in nodes]

def set_unschedulable(name, unschedulable):
    # Cordon the node
    spec = {
        "spec": {
            "unschedulable": unschedulable
        }
    }
    response = api_core.patch_node(name, spec)
    fmt_print("Node {} set to unschedulable={}".format(name, unschedulable))

def delete_stateful_set():
    try:
        fmt_print("Deleting StatefulSet")
        delete_options = client.V1DeleteOptions(propagation_policy='Foreground')
        response = api_instance.delete_namespaced_stateful_set(
            name=STATEFUL_SET_NAME,
            namespace="default",
            body=delete_options
        )

        # Wait for the StatefulSet to be deleted
        while True:
            try:
                api_instance.read_namespaced_stateful_set(
                    name=STATEFUL_SET_NAME,
                    namespace="default"
                )
                fmt_print("StatefulSet still exists")
            except Exception as e:
                if e.status == 404:
                    break
                else:
                    print(e)

            time.sleep(5)

        fmt_print("StatefulSet deleted")
    except Exception as e:
        print(e)

def create_stateful_set():
    response = api_instance.create_namespaced_stateful_set(
        namespace="default",
        body=yaml.safe_load(Path('manifests/stateful_set.yml').read_text())
    )
    fmt_print("StatefulSet created")

def get_time():
    # Return UTC with a Z suffix
    return datetime.datetime.utcnow().isoformat() + "Z"

def fmt_print(msg):
    print("[{}] {}".format(colored(get_time(), 'green'), msg))

if __name__ == "__main__":
    main()
