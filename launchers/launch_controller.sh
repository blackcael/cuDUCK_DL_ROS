#!/bin/bash

HW_PACKAGE="game_controller"
HW_LAUNCH="game_controller.launch"

source /environment.sh

# initialize launch file
dt-launchfile-init

# YOUR CODE BELOW THIS LINE
# ----------------------------------------------------------------------------


# NOTE: Use the variable DT_REPO_PATH to know the absolute path to your code
# NOTE: Use `dt-exec COMMAND` to run the main process (blocking process)

WAIT_FOR_JOYSTICK="${WAIT_FOR_JOYSTICK:-1}"
WAIT_FOR_JOYSTICK_INTERVAL="${WAIT_FOR_JOYSTICK_INTERVAL:-1}"
WAIT_FOR_JOYSTICK_PATTERN="${WAIT_FOR_JOYSTICK_PATTERN:-/dev/input/js*}"

if [ "${WAIT_FOR_JOYSTICK}" = "1" ]; then
    echo "[launch_controller] Waiting for joystick (${WAIT_FOR_JOYSTICK_PATTERN})..."
    while true; do
        if compgen -G "${WAIT_FOR_JOYSTICK_PATTERN}" > /dev/null; then
            echo "[launch_controller] Joystick detected."
            ls -l /dev/input || true
            break
        fi
        sleep "${WAIT_FOR_JOYSTICK_INTERVAL}"
    done
fi

# launching app
dt-exec roslaunch $HW_PACKAGE $HW_LAUNCH


# ----------------------------------------------------------------------------
# YOUR CODE ABOVE THIS LINE

# wait for app to end
dt-launchfile-join
