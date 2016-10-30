#!/bin/bash

TIMESTAMP=`date +%Y%m%d`
echo "Starting backup at: ${TIMESTAMP}"
echo `date`
if [ $# -eq 0 ]
  then
    echo "No arguments supplied, taking default values"
    #exit 1
    DBNAME="umcdj" #default
    DBUSER="umcdjpgsu" #default
    DB_DUMP_FOLDER="/srv/dump"
elif [ $# -ne 3 ]
  then
    echo "Four Arguments not given."
    exit 1
    DBNAME="umcdj" #default
    DBUSER="umcdjpgsu" #default
    DB_DUMP_FOLDER="/home/ubuntu/srv/dump" #default
else
  #log file can be declared in the cron job..
  DBNAME=$1
  DBUSER=$2
  DB_DUMP_FOLDER=$3
fi
DB_DUMP_LOCATION="${DB_DUMP_FOLDER}/UMCloudDj_${DBNAME}_DUMP_${TIMESTAMP}.dump"
echo "Starting backup script.."
pg_dump -w -U $DBUSER -h localhost $DBNAME > $DB_DUMP_LOCATION

if [ $? -ne 0 ]
  then
    echo "Something went wrong in pg_dump command"
    exit 1
else
    echo "DB dump a success"
fi
