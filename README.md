
Welcome to the Ustad Mobile Cloud Portal for statistics, analytical Course Management System. Code Named- UMCloudDj
This project is based on Django 1.6 and integrates ADL_LRS for more robust reporting along with CMS concepts inspired by Ustad Mobile platform's usage. 


Note: this repo itself is not enough to run the server. Follow the steps and it should co-operate on an Ubuntu fresh machine. 

To run the server, 

There are two ways: Step by step or by the script

--------------------------------------------------------------
Step by Step
--------------------------------------------------------------


The UstadMobile Cloud Server or: UMCloudDj runs on Django and uses ADL NET's LRS Django server built in.

Steps to set up UMCloudDj on your system.

1. Install dependencies in your Linux environment (Tested in Ubuntu and Raspberry Pi2)

sudo apt-get install -y libjpeg-dev apache2  python  python-pip python-virtualenv  tree  git sudo apt-get -f install  sqlite3  build-essential  unzip  ant  git  fabric  postgresql  python-setuptools  postgresql-server-dev-all  python-dev libxml2-dev libxslt-dev

sudo easy_install pip

2. Install Python dependencies

sudo pip install virtualenv Django==1.6.6 requests coverage Image django_extensions gunicorn==0.14.2 pytz==2012c supervisor==3.0a12 oauth2==1.5.170 bencode==1.0 psycopg2==2.5 isodate==0.4.9 python-dateutil==1.5 unipath==1.0 pycrypto==2.5 lxml==2.3.4 jsonfield==0.9.19 pygraphviz==1.2 graphviz simplejson pytz phonenumbers

2b. Sometimes we may need to set this (not crutial):

export LANGUAGE=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export LC_TYPE=en_US.UTF-8

3. Clone both UMCloudDj as well as modified LRS server:

git clone https://github.com/UstadMobile/UMCloudDj-Code.git UMCloudDj
git clone https://github.com/varunasingh/ADL_LRS.git ADL_LRS_VS

4. Copy the ADL LRS into UMCloudDj 

cp -r ADL_LRS_VS/lrs UMCloudDj/ 
cp -r ADL_LRS_VS/oauth_provider UMCloudDj/
cp -r ADL_LRS_VS/adl_lrs UMCloudDj/
rm -f UMCloudDj/adl_lrs/settings.py

(You can remove the main ADL_LRS_VS if you want: rm -rf ADL_LRS_VS)

5. Make log directory in UMCloudDj

cd UMCloudDj
mkdir logs

6. Configure postgres in your system

a. Get version, create postgres cluster based on that version
VER=`dpkg -l | grep postgresql- | head -n 1 | awk ' { print $2 }' | awk -F\- '{ print $2 }'`
sudo pg_createcluster ${VER} main --start

b.Create postgres user and password 
!!REPLACE pguser and pgpassword with your postgres username and password!!

sudo -u postgres psql -c "CREATE USER pguser WITH PASSWORD 'pgpassword';"


7. Set up settings.py

a. Copy template to create your own settings.py
cp UMCloudDj/settings.py.edit UMCloudDj/settings.py

b. Edit in your SECRET key 

SECRET_KEY="MySuperSecretKey123"
(Remember to remove existing secret keys)

c. Add postgres user and password to settings.py 

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'umcdj',
        'USER': 'pguser',
        'PASSWORD':'pgpass',
        'HOST': 'localhost',
        'PORT': '',
    }
}

8. Set up the Database

#Set up ADL LRS specific cache tables
python manage.py createcachetable cache_statement_list
python manage.py createcachetable attachment_cache

python manage.py syncdb --noinput 

If success: 


9a. Load Super User Data and set up database:

!!REPLACE SUPERUSERNAME and SUPERPASSWORD with your Super admin credenntials that you like!!

echo "from django.contrib.auth.models import User; User.objects.create_superuser('SUPERUSERNAME', 'info@ustadmobile.com', 'SUPERPASSWORD')" | python manage.py shell

9b. Load UMCloud Fixtures (Tables and data needed to start UMCloud)

python manage.py loaddata uploadeXe/fixtures/initial-model-data.json

10. Set up relationships on fixtures 

DATE2=`date +%Y-%m-%d`
echo "from uploadeXe.models import User_Roles; User_Roles.objects.create(name='build',user_userid_id=1,role_roleid_id=1,add_date='${DATE2}')" | python manage.py shell
echo "from organisation.models import User_Organisations; User_Organisations.objects.create(add_date='${DATE2}',user_userid_id=1,organisation_organisationid_id=1)" | python manage.py shell

11. Make file folders necessary for upload functionality

cd UMCloudDj/media/
mkdir eXeExport
mkdir eXeUpload
mkdir eXeUpload/UPLOAD_CHUNKS
mkdir test
mkdir eXeTestElp
mkdir eXeTestExport


12. Run the server :

cd ../
python manage.py runserver 0:8042 
Go to your browser : localhost:8042 and it should be up and running. 





--------------------------------------------------------------
Using the script
--------------------------------------------------------------

There is a build script within this main repository called: umclouddj-server-development-setup.sh  

1. Get this script to a location where you want the server folder contents to reside :
 wget https://raw.githubusercontent.com/UstadMobile/UMCloudDj-Code/master/umclouddj-server-development-setup.sh

2. You might need to make this script executable:

chmod a+x umclouddj-server-development-setup.sh

Run the script as an example like so:

./umclouddj-server-development-setup.sh "bobtheadmin" "!t$r@|30|3$W0r!|]" "blah" "blah" "secretkey10212wdsda><?:<>!@%" "postgresumcloud" "postgresumcloudpassword" "/path/to/exe.git"(optional)


The usage for this script is: 

    Usage: .sh <Super username> <password> <wordpress pass> <um pass> <secret key> <postgres user> <postgres password> <exe link>(optional)

    Ex:    .sh bobtheadmin "!t$r@|30|3$W0r!|]" worddpass umtestpass "secretkey_10212wdsda><?:<>!@%*%$" postgresumcloud "postgresumcloudpassword" 


Super username> This will be the super admin of the django projet.

password> Super admin's password

wordpress pass> Internal usage. Set to "blah" (Will be depriciated)

um pass> Internal usage. Set to "blah" or anything else. (Will be depriciated)

secret key> This is a random key that should be secret only to you. Can be long and have special characters. Make sure it is in quotes. This is a django specific secret key. Read more about secret keys in Django's docs.

postgres user> UMCloudDj stored data in postgres. This is the username that will be updated in the project settings. Make your own username and these credentials should not be shared. Admin use.

postgres pass> This is the password for the database that UMCloudDj uses. It will be updated in the projects' settings file. 



Once this script runs successfully, cd in to the project directory:

cd UMCloudDj/

and run this command to run the server in development mode. 


$ python manage.py runserver 

The server will run on 127.0.0.1 over port 8000 or you can specify the port and IP after runserer. 

or:

$ python manage.py runserver 0:8004 # runs in 8004 port


The above steps starts the server in development mode (ie: it basically runs over the python command. The ideal way to run a server would be behind apache and wsgi. Steps for this and updates to the build script will be added next.




