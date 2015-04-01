#!/bin/bash
echo "Starting UMCloudDj deployment.."

if [ $# -eq 0 ]; then
    echo "No arguments provided"
    echo "Usage: .sh <Super username> <password> <secret key> <postgres user> <postgres password> <host url>"
    echo "Ex:    .sh adminusername adminpassword secretkey_10212wdsda><?:<>!@%*%$ umcloudadmin umcloudpassword umcloud4.ustadmobile.com"
    exit 1
fi

if [ $# -ne 6 ]; then
    echo "You need to give 6 arguments"
    echo "Usage: .sh <Super username> <password> <wordpress pass> <um pass> <secret key> <postgres user> <postgres password> <host url>"
    echo "Ex:    .sh adminusername adminpassword worddpass umtestpass secretkey_10212wdsda><?:<>!@%*%$ umcloudadmin umcloudpassword umcloud4.ustadmobile.com"
    exit 1
fi


SUPERUSERNAME=${1}
SUPERPASSWORD=${2}
#WORDPRESSPASS=${3}
#UMPASS=${4}
SECRET_KEY=${3}
PGUSER=${4}
PGPASSWORD=${5}
HOSTURL=${6}

DATE=`date +%Y-%m-%d-%H-%M-%S`
echo "Starting installation of UMCDjCloud."
echo "Sorting and installing dependencies.."
sudo apt-get -y dist-upgrade #Added 31/12/2014 to make sure every distribution gets updated
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
sudo apt-get -y install unzip
sudo apt-get -y install ant

sudo apt-get install -y git 
sudo apt-get install -y fabric
sudo apt-get install -y postgresql
sudo apt-get install -y python-setuptools
sudo apt-get install -y postgresql-server-dev-9.3
sudo apt-get install -y postgresql-server-dev-9.1 #Sometimes this is installed
sudo apt-get install -y python-dev libxml2-dev libxslt-dev

sudo easy_install pip

sudo pip install virtualenv

sudo pip install Django==1.6.6
sudo pip install requests
sudo pip install coverage
sudo pip install Image
sudo pip install django_extensions
sudo pip install gunicorn==0.14.2
sudo pip install pytz==2012c
sudo pip install supervisor==3.0a12
sudo pip install oauth2==1.5.170
sudo pip install bencode==1.0
sudo pip install Aisodate==0.4.9
sudo pip install psycopg2==2.5
sudo pip install isodate==0.4.9
sudo pip install python-dateutil==1.5
sudo pip install unipath==1.0
sudo pip install pycrypto==2.5
sudo pip install lxml==2.3.4
sudo pip install jsonfield==0.9.19
sudo pip install pygraphviz==1.2
sudo pip install graphviz
sudo pip install simplejson
sudo pip install pytz

export LANGUAGE=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export LC_TYPE=en_US.UTF-8

#git clone ssh://varunasingh@git.code.sf.net/p/ustadmobil/code-umclouddjango UMCloudDj
#git clone http://git.code.sf.net/p/ustadmobil/code-umclouddjango UMCloudDj
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
echo "echo \"Pulling from exelearning-ustadmobile-work..\"" >> git_pull.sh
echo "cd exelearning-ustadmobile-work/" >> git_pull.sh
echo "git pull" >> git_pull.sh


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
#echo "${WORDPRESSPASS}" > UMCloudDj/UMCloudDj/wordpresscred.txt		#Soon to be deprecated. Was used for authenticting wordpress users. 
#echo "${UMPASS}" > UMCloudDj/UMCloudDj/media/gruntConfig/umpassword.txt #Soon to be deprecated . Was used for testing course pass/fail when sent to server

cd UMCloudDj

git clone https://github.com/UstadMobile/exelearning-ustadmobile-work.git

mkdir logs #needed for ADL_LRS and UMCloud logs

cp UMCloudDj/settings.py.edit UMCloudDj/settings.py

#Need to update the secret key
sed -i.bak -e 's/^SECRET_KEY/##/' UMCloudDj/settings.py
echo "SECRET_KEY=\"${SECRET_KEY}\"" >> UMCloudDj/settings.py

#Need to add the HOST URL
ALLOWED_HOSTS="ALLOWED_HOSTS=['${HOSTURL}']"
sed -i.backup -e 's/^ALLOWED_HOSTS.*/'${ALLOWED_HOSTS}'/' UMCloudDj/settings.py

echo "Configuing postgres in your system.."
sudo pg_createcluster 9.3 main --start
sudo pg_createcluster 9.1 main --start #sometimes this is used instead.

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

if [ $DB_CREATE_FLAG == "0" ]
then
    echo "lrs database created successfully. making roles and organisations"
    echo "from django.contrib.auth.models import User; User.objects.create_superuser('${SUPERUSERNAME}', 'info@ustadmobile.com', '${SUPERPASSWORD}')" | python manage.py shell

    #load fixtures
    python manage.py loaddata uploadeXe/fixtures/initial-model-data.json
    DATE2=`date +%Y-%m-%d`

    echo "from uploadeXe.models import User_Roles; User_Roles.objects.create(name='build',user_userid_id=1,role_roleid_id=1,add_date='${DATE2}')" | python manage.py shell
    echo "from organisation.models import User_Organisations; User_Organisations.objects.create(add_date='${DATE2}',user_userid_id=1,organisation_organisationid_id=1)" | python manage.py shell
else
    echo "Couldn't create lrs. Possibly an update."
fi


cd UMCloudDj/media/
mkdir eXeExport
mkdir eXeUpload
mkdir eXeUpload/UPLOAD_CHUNKS
mkdir test
mkdir eXeTestElp
mkdir eXeTestExport

#Copying the code to apache's html folder.
cd ../../../
sudo cp -r UMCloudDj /var/www/

cd /var/www/UMCloudDj

if [ "$?" != "0" ]; then
    echo "Something went wrong in copying assets to /var/www/"
    exit 1;
fi
echo "Installing mod-wsgi.."
sudo apt-get -y install libapache2-mod-wsgi

sudo chown -R www-data:nogroup /var/www/UMCloudDj

echo "Configuring django entry for apache.."
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
        sudo echo "    WSGIDaemonProcess UMCloudDj python-path=/var/www/UMCloudDj" >add.txt
        sudo echo "    WSGIProcessGroup UMCloudDj" >>add.txt
        sudo echo "    WSGIScriptAlias / /var/www/UMCloudDj/UMCloudDj/wsgi.py" >> add.txt

        sudo echo "    AliasMatch ^/([^/]*\.css) /var/www/UMCloudDj/uploadeXe/static/css/\$1" >>add.txt

        sudo echo "    Alias /media/ /var/www/UMCloudDj/UMCloudDj/media/" >>add.txt
        sudo echo "    Alias /static/ /var/www/UMCloudDj/uploadeXe/static/" >>add.txt


        sudo echo "    <Directory /var/www/UMCloudDj/UMCloudDj>" >>add.txt
        sudo echo "      <Files wsgi.py>" >>add.txt
  	sudo echo $djangospecificaccess >> add.txt
        sudo echo "      </Files>" >> add.txt
        sudo echo "      </Directory>" >> add.txt

#sed '/^<VirtualHost \*\:80/r add.txt' /etc/apache2/sites-enabled/000-default.conf > /etc/apache2/sites-enabled/000-default.conf

echo "Adding django entry to sites-available.."
sudo sed '/^<VirtualHost \*\:80/r add.txt' /etc/apache2/sites-available/000-default.conf > 000-default.conf.new
cat 000-default.conf.new
sudo cp 000-default.conf.new /etc/apache2/sites-available/000-default.conf


echo "Here is a look at the final 000-default.conf in apache2's site-enabled folder:"
cat /etc/apache2/sites-enabled/000-default.conf

echo "Restarting apache2 to initiate the server."
sudo service apache2 restart
echo "Done."



