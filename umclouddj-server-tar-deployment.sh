#!/bin/bash

#Build it.


#sed -i.backup -e 's/^DEBUG=True/DEBUG = False/' $WORKSPACE/UMCloudDj/settings.py

if [ $# -eq 0 ]; then
    echo "No arguments provided"
    echo "Usage: .sh <tar file> <Super username> <password> <host url>"
    echo "Ex:    .sh /home/varuna/UMCloudDj.tar.gz adminusername adminpassword umcloud4.ustadmobile.com"
    exit 1
fi


TARFILE=${1}
SUPERUSERNAME=${2}
SUPERPASSWORD=${3}
HOSTURL=${4}

if [ -z $1 ]
  then
    echo "Please provide the tar file as argument 1"
    echo "Usage: .sh <tar> <super username> <password>i <host url/name>"
    exit 1
fi

if [ -z "$2" ] || [ -z "$3" ]
  then
    echo "No superusername given. Username: umcdj and password: Ch@ng3M3U/C|_0UD"
    SUPERUSERNAME="umcdjsu"
    SUPERPASSWORD="Ch@ng3M3UC|_0UD"

fi


DATE=`date +%Y-%m-%d-%H-%M-%S`
echo "Starting installation of UMCDjCloud."
echo "Sorting and installing dependencies.."
sudo apt-get -y update
sudo apt-get -y upgrade
sudo apt-get -y install apache2
sudo apt-get -y install python
sudo apt-get -y install python-pip python-virtualenv
sudo apt-get -y install tree
sudo apt-get -y install git
sudo apt-get -f install
sudo apt-get -y install sqlite3
sudo apt-get -y install build-essential


#Put UMCloudDj here 
mkdir /var/www/UMCloudDj
cd /var/www/UMCloudDj
tar -xvf ${TARFILE} -C /var/www/UMCloudDj

cd /var/www/UMCloudDj
#if you want a virtual env
#virtual env
#source env/bin/activate

#temporary, need to define hosts to run django with debug off.
#sed -i.backup -e 's/^DEBUG = False/DEBUG = True/' /var/www/UMCloudDj/UMCloudDj/settings.py
ALLOWED_HOSTS="ALLOWED_HOSTS=['${HOSTURL}']"
sed -i.backup -e 's/^ALLOWED_HOSTS.*/'${ALLOWED_HOSTS}'/' /var/www/UMCloudDj/UMCloudDj/settings.py


sudo pip install Django
sudo pip install requests
sudo pip install coverage

#Creates a super user and syncs models and databases
python manage.py syncdb	--noinput
echo "from django.contrib.auth.models import User; User.objects.create_superuser('${SUPERUSERNAME}', 'info@ustadmobile.com', '${SUPERPASSWORD}')" | python manage.py shell

#load fixtures
python manage.py loaddata uploadeXe/fixtures/initial-model-data.json
DATE2=`date +%Y-%m-%d`

echo "from uploadeXe.models import User_Roles; User_Roles.objects.create(name='build',user_userid_id=1,role_roleid_id=1,add_date='${DATE2}')" | python manage.py shell
echo "from organisation.models import User_Organisations; User_Organisations.objects.create(add_date='${DATE2}',user_userid_id=1,organisation_organisationid_id=1)" | python manage.py shell


sudo apt-get -y install libapache2-mod-wsgi

apache2ver=`apache2 -v`
apache2verno=`echo $apache2ver | awk -F\/ '{ print $2 }' | awk -F' ' '{print $1 }'`
apache2comparison='2.4.0'

djangospecificaccess=`echo $apache2verno $apache2comparison |awk '{ split($1, a, ".");
       split($2, b, ".");
       for (i = 1; i <= 4; i++)
           if (a[i] < b[i]) {
	       x = "Allow from all";
               break;
           } else if (a[i] > b[i]) {
	       x ="Require all granted";
               break;
           }
       print x;
     }'`


#edit: sudo vi /etc/apache2/sites-enabled/000-default.conf 
        echo "		WSGIDaemonProcess UMCloudDj python-path=/var/www/UMCloudDj" >add.txt
        echo "		WSGIProcessGroup UMCloudDj" >>add.txt
        echo "		WSGIScriptAlias / /var/www/UMCloudDj/UMCloudDj/wsgi.py" >> add.txt

        echo "		AliasMatch ^/([^/]*\.css) /var/www/UMCloudDj/uploadeXe/static/css/\$1" >>add.txt

        echo "		Alias /media/ /var/www/UMCloudDj/UMCloudDj/media/" >>add.txt
        echo "		Alias /static/ /var/www/UMCloudDj/uploadeXe/static/" >>add.txt


        echo "		<Directory /var/www/UMCloudDj/UMCloudDj>" >>add.txt
        echo "			<Files wsgi.py>" >>add.txt
	echo $djangospecificaccess >> add.txt
        echo "			</Files>" >> add.txt
        echo "			</Directory>" >> add.txt

#sed '/^<VirtualHost \*\:80/r add.txt' /etc/apache2/sites-enabled/000-default.conf > /etc/apache2/sites-enabled/000-default.conf

sudo sed '/^<VirtualHost \*\:80/r add.txt' /etc/apache2/sites-available/000-default.conf > 000-default.conf.new
cat 000-default.conf.new
cp 000-default.conf.new /etc/apache2/sites-available/000-default.conf



cat /etc/apache2/sites-enabled/000-default.conf

sudo chown www-data. UMCloudDj/database/umcloud.sqlite3
sudo chown www-data. UMCloudDj/database

service apache2 restart


