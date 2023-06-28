import boto3
from datetime import datetime, timezone
import time
from termcolor import colored

client = boto3.client('ec2', region_name="eu-west-1")

CLUSTER_SELECTOR = "ebs-test-cluster"
POLL_INTERVAL = 1
STATE_THRESHOLD = 15

# Used for colouring the output consistently
runtime_node_list = set()


# Expect AWS credentials to be set in the environment
# Outputs the EC2/EBS volume status for each node in the cluster
# Lists left over volumes that are not attached to any node


def main():
    global runtime_node_listS

    # Used to track changes in volume state
    previous_volumes = {}
    volume_state_change_times = {}

    while True:
        volumes = sorted(get_volumes(), key=lambda d: d['VolumeId'])
        nodes = get_nodes(volumes)

        # Add new nodes to the runtime list
        for node in nodes:
            if node not in runtime_node_list:
                runtime_node_list.add(node)

        # We want to keep a timestamp when a volume state changes, so we can calculate the duration of the current state
        for volume in volumes:
            current_state = get_attachment_state(volume)
            if volume['VolumeId'] not in volume_state_change_times:
                volume_state_change_times[volume['VolumeId']] = datetime.now(timezone.utc)
            else:
                if current_state != get_attachment_state(previous_volumes[volume['VolumeId']]):
                    volume_state_change_times[volume['VolumeId']] = datetime.now(timezone.utc)

        fmt_print("=====================================================================================================")
        for volume in volumes:
            attach_state, attach_time, device, state_secs, instance_id = "------", "------", "------", "------", "------"
            id = volume['VolumeId']
            if volume['Attachments'] and len(volume['Attachments']) > 0:
                attach_state = colour_state(volume['Attachments'][0]['State'])
                attach_time = volume['Attachments'][0]['AttachTime']
                instance_id = colour_node(volume['Attachments'][0]['InstanceId'], nodes)
                device = volume['Attachments'][0]['Device']

                # Calculate the time since the volume was attached
                now = datetime.now(timezone.utc)
                state_secs = int((now - volume_state_change_times[id]).total_seconds())

                if volume['Attachments'][0]['State'] != "attached":
                    state_secs = colour_threshold(state_secs, STATE_THRESHOLD)

            fmt_print("{} \t| {} \t| {} ({}s ago) \t| {} | {}".format(id, attach_state, attach_time, state_secs, instance_id, device))

        # Convert volumes to map for easier lookup
        previous_volumes = {volume['VolumeId']: volume for volume in volumes}
        time.sleep(POLL_INTERVAL)


def get_attachment_state(volume):
    if volume['Attachments'] and len(volume['Attachments']) > 0:
        return volume['Attachments'][0]['State']
    else:
        return "detached"


def colour_threshold(value, threshold):
    if value > threshold:
        return colored(value, "red")
    else:
        return colored(value, "green")


def colour_state(state):
    if state == "attached":
        return colored(state, "green")
    elif state == "detached":
        return colored(state, "red")
    elif state == "attaching":
        return colored(state, "yellow")
    else:
        return colored(state, "white")


def colour_node(node, nodes):
    global runtime_node_list
    sorted_runtime = sorted(list(runtime_node_list))
    node_colors = ["light_red", "light_yellow", "light_blue", "light_magenta", "light_cyan"]
    return colored(node, node_colors[sorted_runtime.index(node) % len(node_colors)])


def get_nodes(volumes):
    nodes = set()
    for volume in volumes:
        if volume['Attachments'] and len(volume['Attachments']) > 0:
            nodes.add(volume['Attachments'][0]['InstanceId'])
    return sorted(list(nodes))


def get_time():
    # Return UTC with a Z suffix
    return datetime.utcnow().isoformat() + "Z"


def get_volumes():
    response = client.describe_volumes(
        Filters=[
            {
                'Name': 'tag:KubernetesCluster',
                'Values': [CLUSTER_SELECTOR]
            },
        ],
    )
    return response['Volumes']


def fmt_print(msg):
    print("[{}] {}".format(colored(get_time(), 'green'), msg))


if __name__ == "__main__":
    main()
