
STUDENT_LIST_FILE=$1
USERNAME=$2
PASSWORD=$3
URL="https://umcloud1.ustadmobile.com/create_new_user_public/"

cat ${STUDENT_LIST_FILE} | while read line
do
	STUDENT_ID=`echo $line | awk -F\| '{ print $1 }'`
	CLASS_ID=`echo $line | awk -F\| '{ print $2 }'`
	FIRST_NAME=`echo $line | awk -F\| '{ print $3 }'`
	LAST_NAME=`echo $line | awk -F\| '{ print $4 }'`
	DATE_OF_BIRTH=`echo $line | awk -F\| '{ print $5 }'`
	GENDER=`echo $line | awk -F\| '{ print $6 }'`

	echo""
	echo "For Student: ${FIRST_NAME} ${LAST_NAME}"

	curl -X POST -u ${USERNAME}:${PASSWORD} --data "first_name=${FIRST_NAME}&last_name=${LAST_NAME}&gender=${GENDER}&dateofbirth=${DATE_OF_BIRTH}&student_id=${STUDENT_ID}&allclass_id=${CLASS_ID}" ${URL} 
	echo ""
	echo ""
done
