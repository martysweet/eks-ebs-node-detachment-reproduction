import subprocess

# Run this script on the node itself
# Here we want to observe the actual mounts which occur on the host
# We can then compare this to the state of the volumes in AWS
# We can also compare this to the state of the volumes in the cluster

POLL_INTERVAL = 2


def main():
    # Find all devices under /dev/xvda*
    # These are the devices which are mounted
    # We can then use the ebsnvme-id command to get the volume ID


def find_dev_xvda():
    # Use python glob to find all devices under /dev/xvda*
    # Return a list of devices
    path = "/dev/xvda*"

    pass


def run_ebsnvme_id(path):
    # Run the ebsnvme-id command
    # This will output the device name and the volume ID
    # We can then use this to compare against the AWS API
    result = subprocess.run(["/usr/local/bin/ebsnvme-id", path], stdout=subprocess.PIPE)
    output =  result.stdout.decode('utf-8').strip().split(" ") # Volume ID: vol-0a0a0a0a0a0a0a0a0
    if len(output) > 2:
        return output[2]
    else:
        return "UNKNOWN-ERR"

def fmt_print(msg):
    print("[{}] {}".format(colored(get_time(), 'green'), msg))


if __name__ == "__main__":
    main()
