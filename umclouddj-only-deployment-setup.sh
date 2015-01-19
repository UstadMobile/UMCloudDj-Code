#!/bin/bash

#Run this file as sudo.

#Copying the code to apache's html folder.
echo "Copying the code to apache's html folder."
sudo cp -r UMCloudDj /var/www/

cd /var/www/UMCloudDj

if [ "$?" != "0" ]; then
    echo "Something went wrong in copying assets to /var/www/"
    exit 1;
fi
echo "Installing mod-wsgi.."
sudo apt-get -y install libapache2-mod-wsgi

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
        echo "    WSGIDaemonProcess UMCloudDj python-path=/var/www/UMCloudDj" >add.txt
        echo "    WSGIProcessGroup UMCloudDj" >>add.txt
        echo "    WSGIScriptAlias / /var/www/UMCloudDj/UMCloudDj/wsgi.py" >> add.txt

        echo "    AliasMatch ^/([^/]*\.css) /var/www/UMCloudDj/uploadeXe/static/css/\$1" >>add.txt

        echo "    Alias /media/ /var/www/UMCloudDj/UMCloudDj/media/" >>add.txt
        echo "    Alias /static/ /var/www/UMCloudDj/uploadeXe/static/" >>add.txt


        echo "    <Directory /var/www/UMCloudDj/UMCloudDj>" >>add.txt
        echo "      <Files wsgi.py>" >>add.txt
        echo $djangospecificaccess >> add.txt
        echo "      </Files>" >> add.txt
        echo "      </Directory>" >> add.txt

#sed '/^<VirtualHost \*\:80/r add.txt' /etc/apache2/sites-enabled/000-default.conf > /etc/apache2/sites-enabled/000-default.conf

echo "Adding django entry to sites-available.."
sudo sed '/^<VirtualHost \*\:80/r add.txt' /etc/apache2/sites-available/000-default.conf > 000-default.conf.new
cat 000-default.conf.new
cp 000-default.conf.new /etc/apache2/sites-available/000-default.conf


echo "Here is a look at the final 000-default.conf in apache2's site-enabled folder:"
cat /etc/apache2/sites-enabled/000-default.conf

sudo chown -R www-data:nogroup /var/www/UMCloudDj

echo "Restarting apache2 to initiate the server."
service apache2 restart
echo "Done."

