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

dts devel run -X -L "$lab_specific_launcher" -- "$@"
