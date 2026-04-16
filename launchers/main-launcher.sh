#!/bin/bash

path_to_repo="../"

if [ "$1" == "lab4_masking" ]; then
    lab_specific_launcher="launcher-masking"
elif [ "$1" == "lab4_lines" ]; then
    lab_specific_launcher="launcher-lines"
elif [ "$1" == "lab5_pid" ]; then
    lab_specific_launcher="launcher-pid"
elif [ "$1" == "final"]; then
    lab_specific_launcher="launcher_intersection"
else
    echo "Incorrect lab number"
    exit 0
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

cd $path_to_repo

dts devel run -X -L $lab_specific_launcher
