from kubernetes import client, config, watch
from termcolor import colored
import datetime


# Load the Kubernetes configuration from the default location
config.load_kube_config()

# Create a Kubernetes API client
api_client = client.ApiClient()
api_instance = client.AppsV1Api(api_client)
api_core = client.CoreV1Api(api_client)
api_storage = client.StorageV1Api(api_client)

def main():
    # Watch the node resource types to receive updates
    w = watch.Watch()
    for event in w.stream(api_core.list_node, timeout_seconds=0):
        fmt_print("Name", event['object'].metadata.name)
        fmt_print("Type", event['type'])
        fmt_print("Deletion Timestamp", event['object'].metadata.deletion_timestamp)
        fmt_print("Finalizers", event['object'].metadata.finalizers)
        # Remove line breaks from volumes_attached
        volumes_attached = str(event['object'].status.volumes_attached)
        fmt_print("Status volumes attached", volumes_attached.replace("\n", ""))
        fmt_print("Status volumes in use", event['object'].status.volumes_in_use)
        fmt_print("", "====================================================================================== =")

def get_time():
    # Return UTC with a Z suffix
    return datetime.datetime.utcnow().isoformat() + "Z"

def fmt_print(field, msg):
    if field != "":
        field = field + ": "
    print("[{}] {} {}".format(colored(get_time(), 'green'), colored(field, 'red'), msg))

if __name__ == "__main__":
    main()