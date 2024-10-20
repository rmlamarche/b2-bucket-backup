#!/bin/bash
# start.sh: wrapper script that sends success/failure notifications via ntfy based on exit code

# helper function to send ntfy push notification on success
function send_ntfy_success {
    local time_elapsed="${1}"
    /bbb/common/ntfy.py -u "${NTFY_URL}" -T "${NTFY_SUCCESS_TITLE}" -m "${NTFY_SUCCESS_MESSAGE} $time_elapsed" -p "${NTFY_SUCCESS_PRIORITY}"
}
# helper function to send ntfy push notification on failure
function send_ntfy_failure {
    local time_elapsed="${1}"
    /bbb/common/ntfy.py -u "${NTFY_URL}" -T "${NTFY_FAILURE_TITLE}" -m "${NTFY_FAILURE_MESSAGE} $time_elapsed" -p "${NTFY_FAILURE_PRIORITY}"
}

# Run supplied backup script
SECONDS=0
$1
RESULT=$?
DURATION=$SECONDS
TIME_ELAPSED="(took $((DURATION / 60))m $((DURATION % 60))s)"

# send push notifications based on exit code
if [ $RESULT -ne 0 ]; then
    if [ -z "${NTFY_URL}" ]; then
        echo "ERROR: backup failed, no NTFY_URL set. Set NTFY_URL=https://ntfy.sh/my-topic to receive alerts."
        exit 1
    fi
    send_ntfy_failure $TIME_ELAPSED
else
    if [ -z "${NTFY_URL}" ]; then
        exit 0
    fi
    send_ntfy_success $TIME_ELAPSED
fi
