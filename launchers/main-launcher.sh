#!/bin/bash

path_to_repo="../"
mode="$1"
shift || true

if [ "$mode" == "lab4_masking" ]; then
    lab_specific_launcher="launcher-masking"
elif [ "$mode" == "lab4_lines" ]; then
    lab_specific_launcher="launcher-lines"
elif [ "$mode" == "lab5_pid" ]; then
    lab_specific_launcher="launcher-pid"
elif [ "$mode" == "final" ]; then
    lab_specific_launcher="launcher_intersection"
elif [ "$mode" == "dl_drive" ]; then
    lab_specific_launcher="launcher-dl-drive"
else
    echo "Usage: $0 {lab4_masking|lab4_lines|lab5_pid|final|dl_drive} [launcher args]"
    echo "Examples:"
    echo "  $0 dl_drive -a"
    echo "  $0 dl_drive -c --device cuda"
    exit 1
fi
# if [ "$2" == "" ]; then
    #   path_to_repo= $pwd
# if [ "$2" == "cblack1" ]; then
#     path_to_repo="/auto/fsf/cblack1/ecen433/final-project-quackops/"
# elif [ "$2" == "cchinh" ]; then
#     path_to_repo="auto/fsj/cchinh/final-projects-quackops"
# else
#     echo "Incorrect compiling computer provided"
#     exit 0
# fi

cd "$path_to_repo"

if [ "$mode" == "dl_drive" ]; then
    model_file="alvinn_latest.pt"
    device="${DL_DRIVE_DEVICE:-auto}"

    while [ $# -gt 0 ]; do
        case "$1" in
            -a)
                model_file="alvinn_latest.pt"
                ;;
            -aa)
                model_file="alvinnita_latest.pt"
                ;;
            -c)
                model_file="calvinn_latest.pt"
                ;;
            -m)
                model_file="melvinn_latest.pt"
                ;;
            --model)
                shift
                if [ -z "$1" ]; then
                    echo "Error: --model requires a value"
                    exit 1
                fi
                if [[ "$1" == *.pt ]]; then
                    model_file="$1"
                elif [[ "$1" == *_latest ]]; then
                    model_file="${1}.pt"
                else
                    model_file="${1}_latest.pt"
                fi
                ;;
            --device)
                shift
                if [ -z "$1" ]; then
                    echo "Error: --device requires a value"
                    exit 1
                fi
                device="$1"
                ;;
            -h|--help)
                echo "Usage: $0 dl_drive [-a|-aa|-c|-m] [--model NAME] [--device DEVICE]"
                exit 0
                ;;
            *)
                echo "Unknown dl_drive argument: $1"
                echo "Usage: $0 dl_drive [-a|-aa|-c|-m] [--model NAME] [--device DEVICE]"
                exit 1
                ;;
        esac
        shift
    done

    DL_DRIVE_MODEL_FILE="$model_file" DL_DRIVE_DEVICE="$device" \
        dts devel run -X -L "$lab_specific_launcher"
else
    dts devel run -X -L "$lab_specific_launcher" -- "$@"
fi
