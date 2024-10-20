#!/bin/bash

/backup.sh

if [ $? -ne 0 ]; then
    if [ -z "${NTFY_URL}" ]; then
        echo "ERROR: backup failed, no NTFY_URL set. Set NTFY_URL=ntfy.sh/my-topic to receive alerts."
        exit 1
    fi
    /ntfy.py -u $NTFY_URL -T "Backup Failed" -m "A backup job for sqlite-generic failed" -p 5
else
    if [ -z "${NTFY_URL}" ]; then
        exit 0
    fi
    /ntfy.py -u $NTFY_URL -T "Backup Succeeded" -m "Successfully backed up sqlite-generic" -p 1
fi
