#!/bin/bash

# bash run.sh | tee -a vol.log

# Output the time and date
# List all the attached volumes using lsblk
# Output the mapped modified times /dev/xvd* devices

# Run forever
# Run the script every 5 seconds
while true; do

    echo "===================================================================================================="
    echo "The time and date is:"
    date

    echo -e "\nList of mapped modified mounts:"
    ls -l --time-style=full-iso /dev/xvd*

    echo -e "\nList of mapped nvme mounts:"
    ls -l --time-style=full-iso /dev/nvme*

    echo -e "\nList of attached volumes:"
    lsblk -o +SERIAL


    sleep 5
done
