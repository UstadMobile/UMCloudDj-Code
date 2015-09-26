#!/bin/sh

if [ $# -eq 0 ]; then
    echo " Please give the arguments with the script. They are: " 
    echo "Usage is :  <sh> FILE USERNAME PASSWORD forceNew blockCourse gradeLevel category noAutoassign"
    echo " Make sure to have empty strings where no value required. Eg: \"\" "
    exit 1;
fi

if [ $# -ne 8 ];then
    echo " Please give all 8 arguments. Even if they are empty"
    echo ""
    echo "Usage is :  <sh> FILE USERNAME PASSWORD forceNew blockCourse gradeLevel category noAutoassign"
    echo " Make sure to have empty strings where no value required. Eg: \"\" "
    exit 1;
fi

FILE=$1
USERNAME=$2
PASSWORD=$3

forceNew=$4
blockCourse=$5
gradeLevel=$6
category=$7
noAutoassign=$8

URL="http://umcloud1.ustadmobile.com/uploadeXe/upload/"
FWORD="exefile"
OPFILE="op.html"

FORMPREFIX=" --form"

FORM=""
if [ ! -z "$FILE" -a "$FILE" != " " ]; then
   FORM="${FORM} ${FORMPREFIX} ${FWORD}=@${FILE}"
fi
if [ ! -z "$USERNAME" -a "$USERNAME" != " " ]; then
   FORM="${FORM} ${FORMPREFIX} username=${USERNAME}"
fi
if [ ! -z "$PASSWORD" -a "$PASSWORD" != " " ]; then
   FORM="${FORM} ${FORMPREFIX} password=${PASSWORD}"
fi
if [ ! -z "$forceNew" -a "$forceNew" != " " ]; then
   FORM="${FORM} ${FORMPREFIX} forceNew=True"
fi
if [ ! -z "$blockCourse" -a "$blockCourse" != " " ]; then
   FORM="${FORM} ${FORMPREFIX} blockCourse=True"
fi
if [ ! -z "$gradeLevel" -a "$gradeLevel" != " " ]; then
   FORM="${FORM} ${FORMPREFIX} gradeLevel=${gradeLevel}"
fi
if [ ! -z "$category" -a "$category" != " " ]; then
   FORM="${FORM} ${FORMPREFIX} category=${category}"
fi 
if [ ! -z "$noAutoassign" -a "$noAutoassign" != " " ]; then
   FORM="${FORM} ${FORMPREFIX} noAutoassign=True"
fi

echo ""
echo "Running this: " 
echo "curl -i -s ${FORM} -X POST ${URL} "

response=`curl -i -s ${FORM} -X POST ${URL} | grep "HTTP/1.1"`
res=`echo ${response} | grep -c "200 OK"`

echo "${res}"

if [ $res -eq 1 ]
then
    echo "All good. Response was 200"
else
    echo "Failure. Not 200 response. It was:"
    echo "${response}"
    exit 1
fi

