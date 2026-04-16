#!/bin/bash
set -euo pipefail

WAIT_FOR_JOYSTICK="${WAIT_FOR_JOYSTICK:-1}"
WAIT_FOR_JOYSTICK_INTERVAL="${WAIT_FOR_JOYSTICK_INTERVAL:-1}"
WAIT_FOR_JOYSTICK_TIMEOUT="${WAIT_FOR_JOYSTICK_TIMEOUT:-0}"
WAIT_FOR_JOYSTICK_PATTERN="${WAIT_FOR_JOYSTICK_PATTERN:-/dev/input/js*}"

if [ "${WAIT_FOR_JOYSTICK}" != "1" ]; then
    exec "$@"
fi

echo "[wait_for_joystick] Waiting for joystick device pattern: ${WAIT_FOR_JOYSTICK_PATTERN}"
echo "[wait_for_joystick] Poll interval: ${WAIT_FOR_JOYSTICK_INTERVAL}s (timeout: ${WAIT_FOR_JOYSTICK_TIMEOUT}s, 0=forever)"

START_TS="$(date +%s)"
while true; do
    if compgen -G "${WAIT_FOR_JOYSTICK_PATTERN}" > /dev/null; then
        echo "[wait_for_joystick] Joystick detected."
        ls -l /dev/input || true
        break
    fi

    if [ "${WAIT_FOR_JOYSTICK_TIMEOUT}" -gt 0 ]; then
        NOW_TS="$(date +%s)"
        ELAPSED="$((NOW_TS - START_TS))"
        if [ "${ELAPSED}" -ge "${WAIT_FOR_JOYSTICK_TIMEOUT}" ]; then
            echo "[wait_for_joystick] Timeout waiting for joystick after ${ELAPSED}s."
            exit 1
        fi
    fi

    sleep "${WAIT_FOR_JOYSTICK_INTERVAL}"
done

exec "$@"
