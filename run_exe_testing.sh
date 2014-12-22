#!/bin/bash

Usage: -s ustadMobileTestMode=True -x ustadmobile 

mode=$1
testmode=$2
mode1=$3
exportmode=$4
inputelp=$5
outputfolder=$6

echo "Arg is: $1|$2|$3|$4|$5|$6"

if [ ! -f ./exelearning-ustadmobile-work/exe/exe_do ]; then
    echo "ExE File not found!"
    exit 1
fi
echo "eXe File Found"

if [ ! -f $inputelp ];then
    echo "Input elp file not found"
    exit 1
fi

echo "Running the export"

./exelearning-ustadmobile-work/exe/exe_do $1 $2 $3 $4 $5 $6 

if [ "$?" != "0" ]; then
    echo"Did Not export well."
    exit 1
fi
exit 0

