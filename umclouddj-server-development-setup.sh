#!/bin/bash

if [ $# -eq 0 ]; then
    echo "No arguments provided "
    echo "Usage: .sh <Super username> <password> <wordpress pass> <um pass> <secret key> <postgres user> <postgres password> <exe link>" 
    echo "Ex:    .sh adminusername adminpassword worddpass umtestpass secretkey_10212wdsda><?:<>!@%*%$ umcloudadmin umcloudpassword" "https://path/to/exe.git"
    exit 1
fi

if [ $# -ne 7 ]; then
    echo "You need to give at least 7 arguments"
    echo "Usage: .sh <Super username> <password> <wordpress pass> <um pass> <secret key> <postgres user> <postgres password>"
    echo "Ex:    .sh adminusername adminpassword worddpass umtestpass secretkey_10212wdsda><?:<>!@%*%$ umcloudadmin umcloudpassword"
    exit 1
fi


SUPERUSERNAME=${1}
SUPERPASSWORD=${2}
WORDPRESSPASS=${3}
UMPASS=${4}
SECRET_KEY=${5}
PGUSER=${6}
PGPASSWORD=${7}
EXELINK=${8}
if [ "${EXELINK}" == "" ]
then
   echo "No eXe link given. Not going to install eXe"
else
   echo "eXe Link given. Will try to install it."
fi


DATE=`date +%Y-%m-%d-%H-%M-%S`
echo "Starting installation of UMCDjCloud."
echo "Sorting and installing dependencies.."
sudo apt-get install -y libjpeg-dev apache2  python  python-pip python-virtualenv  tree  git sudo apt-get -f install  sqlite3  build-essential  unzip  ant  git  fabric  postgresql  python-setuptools  postgresql-server-dev-all  python-dev libxml2-dev libxslt-dev
#sudo apt-get -y dist-upgrade #Added 31/12/2014 to make sure every distribution gets updated
#sudo apt-get -y update
#sudo apt-get -y upgrade

sudo easy_install pip

sudo pip install virtualenv Django==1.6.6 requests coverage Image django_extensions gunicorn==0.14.2 pytz==2012c supervisor==3.0a12 oauth2==1.5.170 bencode==1.0 psycopg2==2.5 isodate==0.4.9 python-dateutil==1.5 unipath==1.0 pycrypto==2.5 lxml==2.3.4 jsonfield==0.9.19 pygraphviz==1.2 graphviz simplejson pytz phonenumbers

export LANGUAGE=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export LC_TYPE=en_US.UTF-8

git clone https://github.com/UstadMobile/UMCloudDj-Code.git UMCloudDj
git clone https://github.com/varunasingh/ADL_LRS.git ADL_LRS_VS

echo "Making git pull and update scripts.."

echo "cd UMCloudDj" > git_pull.sh

echo "git pull" >> git_pull.sh
echo " if [ ! -f UMCloudDj/settings.py ]; then" >> git_pull.sh
echo "  echo \"settings.py file does not exist. Creating it..\"" >> git_pull.sh
echo "  cp UMCloudDj/settings.py.edit UMCloudDj/settings.py" >> git_pull.sh
echo "  sed -i.bak -e 's/^SECRET_KEY.*/##/' UMCloudDj/settings.py" >> git_pull.sh
echo "  echo \"SECRET_KEY=\"${SECRET_KEY}\" >> UMCloudDj/settings.py" >> git_pull.sh
echo "  echo \"finished.\"" >> git_pull.sh
echo "  else" >> git_pull.sh
echo "   echo \"settings.py file already exists.\"" >> git_pull.sh
echo " fi" >> git_pull.sh

if [ "${EXELINK}" == "" ]
then
    echo "Skipping eXe because eXe mode is disabled"
else
    echo "echo \"Pulling from exelearning-ustadmobile-work..\"" >> git_pull.sh
    echo "cd exelearning-ustadmobile-work/" >> git_pull.sh
    echo "git pull" >> git_pull.sh
fi

chmod a+x git_pull.sh

echo "Installing ADL_LRS in the UMCloudDj project.."
cp -r ADL_LRS_VS/lrs UMCloudDj/ 
cp -r ADL_LRS_VS/oauth_provider UMCloudDj/
cp -r ADL_LRS_VS/adl_lrs UMCloudDj/
rm -f UMCloudDj/adl_lrs/settings.py

rm -rf ADL_LRS_VS

#sed -i.bak "/ 'users',/a    \ \ \ \ \'lrs\',\n    \'lrs.util\',\n    \'adl_lrs\',\n    \'oauth_provider\',\n    \'gunicorn\',\n    \'django_extensions\'," UMCloudDj/UMCloudDj/settings.py.edit

#sed -i.bak "/^urlpatterns/a \ \ \ \ \ \ \ \ (r\'\^umlrs\/\', include(\'lrs.urls\'))," UMCloudDj/UMCloudDj/urls.py

> UMCloudDj/UMCloudDj/wordpresscred.txt
> UMCloudDj/UMCloudDj/media/gruntConfig/umpassword.txt
echo "${WORDPRESSPASS}" > UMCloudDj/UMCloudDj/wordpresscred.txt		#Soon to be deprecated. Was used for authenticting wordpress users. 
echo "${UMPASS}" > UMCloudDj/UMCloudDj/media/gruntConfig/umpassword.txt #Soon to be deprecated . Was used for testing course pass/fail when sent to server

cd UMCloudDj
mkdir logs #needed for ADL_LRS and UMCloud logs

cp UMCloudDj/settings.py.edit UMCloudDj/settings.py

#Need to update the secret key
sed -i.bak -e 's/^SECRET_KEY/##/' UMCloudDj/settings.py
echo "SECRET_KEY=\"${SECRET_KEY}\"" >> UMCloudDj/settings.py

echo "Configuing postgres in your system.."
VER=`dpkg -l | grep postgresql- | head -n 1 | awk ' { print $2 }' | awk -F\- '{ print $2 }'`
sudo pg_createcluster ${VER} main --start
#sudo pg_createcluster 9.3 main --start
#sudo pg_createcluster 9.1 main --start #sometimes this is used instead.

#By this time there should be a postgres user as it has been installed in the system. 
#we can set the user and password for this postgres user: 
echo "Creating user: ${PGUSER}"
#sudo -u postgres createuser -P ${PGUSER}
echo "Updating password"
sudo -u postgres psql -c "CREATE USER ${PGUSER} WITH PASSWORD '${PGPASSWORD}';"

#Create the lrs database
echo "Creating the lrs database"
sudo -u postgres psql -c "CREATE DATABASE umcdj OWNER ${PGUSER};"
DB_CREATE_FLAG="${?}"

#Update settings.py to have access to database via these credentials
#sed -i.bak -e 's/.*USER.*/##USER/' UMCloudDj/settings.py
sed -i.bak "/^##USER/a \ \ \ \ \ \ \ \ 'USER': '${PGUSER}'," UMCloudDj/settings.py
grep -v "^##USER*" UMCloudDj/settings.py > UMCloudDj/settings.py.2
mv UMCloudDj/settings.py.2 UMCloudDj/settings.py
sed -i.bak "/^##PASSW/a \ \ \ \ \ \ \ \ 'PASSWORD':'${PGPASSWORD}'," UMCloudDj/settings.py
grep -v "^##PASS*" UMCloudDj/settings.py > UMCloudDj/settings.py.2
mv UMCloudDj/settings.py.2 UMCloudDj/settings.py



#After getting latest version, we use this to create super user and assign database mappings:
#Creates a super user and syncs models and databases

#Added ADL_LRS specific cache databaase additions.
python manage.py createcachetable cache_statement_list
python manage.py createcachetable attachment_cache

#Sync it all..
python manage.py syncdb --noinput

if [ "$DB_CREATE_FLAG" == "0" ]
then
    echo "lrs database created successfully. making roles and organisations"
    echo "from django.contrib.auth.models import User; User.objects.create_superuser('${SUPERUSERNAME}', 'info@ustadmobile.com', '${SUPERPASSWORD}')" | python manage.py shell

    #load fixtures
    python manage.py loaddata uploadeXe/fixtures/initial-model-data.json
    DATE2=`date +%Y-%m-%d`

    echo "from uploadeXe.models import User_Roles; User_Roles.objects.create(name='build',user_userid_id=1,role_roleid_id=1,add_date='${DATE2}')" | python manage.py shell
    echo "from organisation.models import User_Organisations; User_Organisations.objects.create(add_date='${DATE2}',user_userid_id=1,organisation_organisationid_id=1)" | python manage.py shell
else
    echo "Couldn't create lrs database. Possibly an update."
fi


cd UMCloudDj/media/
mkdir eXeExport
mkdir eXeUpload
mkdir eXeUpload/UPLOAD_CHUNKS
mkdir test
mkdir eXeTestElp
mkdir eXeTestExport

cd ../
if [ "${EXELINK}" == "" ]
then
   echo "Skipping cloning eXe because eXe mode is disabled"
else
   git clone https://github.com/UstadMobile/exelearning-ustadmobile-work.git
fi

