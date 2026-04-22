#!/bin/bash

source /environment.sh

# initialize launch file

dt-launchfile-init

# YOUR CODE BELOW THIS LINE
# ----------------------------------------------------------------------------

# Usage:
#   launcher-dl-drive.sh [-a|-aa|-c|-m] [--model NAME]
#
# Model aliases:
#   -a   -> alvinn_latest.pt
#   -aa  -> alvinnita_latest.pt
#   -c   -> calvinn_latest.pt
#   -m   -> melvinn_latest.pt
#
# You can also pass a plain model name with --model NAME. If NAME has no
# extension, "_latest.pt" is appended. The model is resolved inside
# packages/dl_drive/models.

MODELS_DIR="${DT_REPO_PATH}/packages/dl_drive/models"
MODEL_FILE="alvinn_latest.pt"
DEVICE="${DL_DRIVE_DEVICE:-auto}"

print_usage() {
    echo "Usage: launcher-dl-drive.sh [-a|-aa|-c|-m] [--model NAME] [--device DEVICE]"
    echo "  -a              Use ALVINN (alvinn_latest.pt)"
    echo "  -aa             Use ALVINNITA (alvinnita_latest.pt)"
    echo "  -c              Use CALVINN (calvinn_latest.pt)"
    echo "  -m              Use MELVINN (melvinn_latest.pt)"
    echo "  --model NAME    Use model in models dir (NAME or NAME.pt or NAME_latest.pt)"
    echo "  --device VALUE  ROS device param (default: auto or DL_DRIVE_DEVICE env)"
    echo "  -h, --help      Show this help"
}

while [ $# -gt 0 ]; do
    case "$1" in
        -a)
            MODEL_FILE="alvinn_latest.pt"
            ;;
        -aa)
            MODEL_FILE="alvinnita_latest.pt"
            ;;
        -c)
            MODEL_FILE="calvinn_latest.pt"
            ;;
        -m)
            MODEL_FILE="melvinn_latest.pt"
            ;;
        --model)
            shift
            if [ -z "$1" ]; then
                echo "[dl-drive-launcher] Error: --model requires a value"
                print_usage
                exit 1
            fi
            if [[ "$1" == *.pt ]]; then
                MODEL_FILE="$1"
            elif [[ "$1" == *_latest ]]; then
                MODEL_FILE="${1}.pt"
            else
                MODEL_FILE="${1}_latest.pt"
            fi
            ;;
        --device)
            shift
            if [ -z "$1" ]; then
                echo "[dl-drive-launcher] Error: --device requires a value"
                print_usage
                exit 1
            fi
            DEVICE="$1"
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo "[dl-drive-launcher] Unknown argument: $1"
            print_usage
            exit 1
            ;;
    esac
    shift

done

MODEL_PATH="${MODELS_DIR}/${MODEL_FILE}"

if [ ! -f "${MODEL_PATH}" ]; then
    echo "[dl-drive-launcher] Model file not found: ${MODEL_PATH}"
    echo "[dl-drive-launcher] Available models:"
    ls -1 "${MODELS_DIR}"/*.pt 2>/dev/null || echo "  (none found)"
    exit 1
fi

echo "[dl-drive-launcher] Launching dl_drive with model: ${MODEL_PATH}"
echo "[dl-drive-launcher] Device: ${DEVICE}"

# launching app

dt-exec roslaunch dl_drive dl_drive.launch model_path:="${MODEL_PATH}" device:="${DEVICE}"

# ----------------------------------------------------------------------------
# YOUR CODE ABOVE THIS LINE

# wait for app to end

dt-launchfile-join
