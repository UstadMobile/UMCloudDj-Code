
Welcome to the Ustad Mobile Cloud Portal for statistics, analytical Course Management System. Code Named- UMCloudDj
This project is based on Django 1.6 and integrates ADL_LRS for more robust reporting along with CMS concepts inspired by Ustad Mobile platform's usage. 


Note: this repo itself is not enough to run the server. Follow the steps and it should co-operate on an Ubuntu fresh machine. 

To run the server, 

There is a build script within this main repository called: umclouddj-server-development-setup.sh  

1. Get this script to a location where you want the server folder contents to reside :
 wget https://raw.githubusercontent.com/UstadMobile/UMCloudDj-Code/master/umclouddj-server-development-setup.sh

2. You might need to make this script executable:

chmod a+x umclouddj-server-development-setup.sh

Run the script as an example like so:

./umclouddj-server-development-setup.sh "bobtheadmin" "!t$r@|30|3$W0r!|]" "blah" "blah" "secretkey10212wdsda><?:<>!@%" "postgresumcloud" "postgresumcloudpassword"


The usage for this script is: 

    Usage: .sh <Super username> <password> <wordpress pass> <um pass> <secret key> <postgres user> <postgres password

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



