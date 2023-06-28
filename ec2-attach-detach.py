import time
import boto3
from datetime import datetime
from termcolor import colored

client = boto3.client('ec2', region_name="eu-west-1")

DETACH_ATTACH_DELAY = 5

CLUSTER_SELECTOR = "ebs-test-cluster"
PREFIX = "/dev/xvda"
alphabet = "abcdefghijklmnopqrstuvwxyz"

def main():
    iteration = 0

    # We detach and reattach to the next item in the loop, doing a modulo rollover
    cluster_instances = get_instances()
    fmt_print("Found {} instances".format(len(cluster_instances)))

    # Find volumes
    volumes = get_volumes()
    fmt_print("Found {} volumes".format(len(volumes)))

    # Initial detach
    detach_volumes()
    time_all_volumes_successful("available")
    time.sleep(DETACH_ATTACH_DELAY)

    while True:
        instance = cluster_instances[iteration % len(cluster_instances)]
        fmt_print("Iteration {} attaching to {}".format(iteration, instance))

        # Attach to target instance
        attach_volumes(instance)     # Attaching is always pretty instant
        time_all_volumes_successful("in-use")
        time.sleep(DETACH_ATTACH_DELAY)

        # Detach from target instance
        detach_volumes()
        time_all_volumes_successful("available")
        time.sleep(DETACH_ATTACH_DELAY)

        iteration += 1


def time_all_volumes_successful(desired_state):
    start = time.time()
    volumes = get_volumes()
    while not all_volumes_successful(volumes, desired_state):
        # print("Waiting for all volumes to be available")
        time.sleep(1)
        volumes = get_volumes()
    end = time.time()
    fmt_print("DESIRED_STATE={},DURATION={}".format(desired_state, end - start))


def all_volumes_successful(volumes, desired_state):
    for volume in volumes:
        if volume['State'] != desired_state:
            return False
    return True


def detach_volumes():
    fmt_print("Detaching all volumes")
    volumes = get_volumes()
    for volume in volumes:
        if volume['Attachments'] and len(volume['Attachments']) > 0:
            # print("Detaching {}".format(volume['VolumeId']))
            if volume['Attachments'][0]['State'] == "attached":
                client.detach_volume(
                    VolumeId=volume['VolumeId'],
                )


def attach_volumes(instance):
    fmt_print("Attaching all volumes")
    volumes = get_volumes()
    for volume in volumes:
        if not volume["Attachments"] or len(volume["Attachments"]) == 0:
            # print("Attaching {}".format(volume['VolumeId']))
            client.attach_volume(
                VolumeId=volume['VolumeId'],
                InstanceId=instance,
                Device=PREFIX + alphabet[volumes.index(volume)]
            )

def get_instances():
    response = client.describe_instances(
        Filters=[
            {
                'Name': 'tag:eks:cluster-name',
                'Values': [CLUSTER_SELECTOR]
            },
        ],
    )

    if len(response['Reservations']) == 0:
        fmt_print("No instances found")
        exit(1)

    # Return a list of InstanceId
    return [instance['InstanceId'] for instance in response['Reservations'][0]['Instances']]

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

def get_time():
    # Return UTC with a Z suffix
    return datetime.utcnow().isoformat() + "Z"


def fmt_print(msg):
    print("[{}] {}".format(colored(get_time(), 'green'), msg))


if __name__ == "__main__":
    main()
