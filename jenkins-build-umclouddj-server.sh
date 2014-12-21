RKSPACE

git clone https://github.com/varunasingh/ADL_LRS.git ADL_LRS_VS
if [ "$?" != "0" ]; then
        echo "Not a new jenkins run"
	cd ADL_LRS_VS
	git pull
	cd ..
fi

echo "Installing ADL_LRS in the UMCloudDj project.."
cp -r ADL_LRS_VS/lrs ./
cp -r ADL_LRS_VS/oauth_provider ./
cp -r ADL_LRS_VS/adl_lrs ./
rm -f adl_lrs/settings.py

rm -rf ADL+LRS_VS
mkdir logs
> logs/lrs.log
> logs/django.log

cd UMCloudDj/media/
mkdir eXeExport
mkdir eXeUpload
mkdir test
mkdir eXeTestElp
mkdir eXeTestExport

cd ../../
pwd

cp UMCloudDj/settings.py.edit UMCloudDj/settings.py

sed -i.backup -e 's/^DEBUG=True/DEBUG = False/' $WORKSPACE/UMCloudDj/settings.py
sed -i.backup -e 's/^DEBUG = True/DEBUG = False/' $WORKSPACE/UMCloudDj/settings.py
sed -i.backup -e 's/^DEBUG =True/DEBUG = False/' $WORKSPACE/UMCloudDj/settings.py
sed -i.backup -e 's/^DEBUG= True/DEBUG = False/' $WORKSPACE/UMCloudDj/settings.py

sed -i.backup -e 's/^TEMPLATE_DEBUG=True/TEMPLATE_DEBUG = False/' $WORKSPACE/UMCloudDj/settings.py
sed -i.backup -e 's/^TEMPLATE_DEBUG =True/TEMPLATE_DEBUG = False/' $WORKSPACE/UMCloudDj/settings.py
sed -i.backup -e 's/^TEMPLATE_DEBUG = True/TEMPLATE_DEBUG = False/' $WORKSPACE/UMCloudDj/settings.py
sed -i.backup -e 's/^TEMPLATE_DEBUG = True/TEMPLATE_DEBUG = False/' $WORKSPACE/UMCloudDj/settings.py

sed -i.backup -e 's/^SECRET_KEY/##/' $WORKSPACE/UMCloudDj/settings.py
echo "SECRET_KEY=\"ReplaceMe\"" >> $WORKSPACE/UMCloudDj/settings.py

PGCRED=`cat '/opt/UMCloudDj/postgrescred.txt'`
PGUSER=`echo $PGCRED | awk -F\| '{ print $1 }'`
PGPASSWORD=`echo $PGCRED | awk -F\| '{ print$2 }'`

sed -i.bak "/^##USER/a \ \ \ \ \ \ \ \ 'USER': '${PGUSER}'," $WORKSPACE/UMCloudDj/settings.py
grep -v "^##USER*" $WORKSPACE/UMCloudDj/settings.py $WORKSPACE/UMCloudDj/settings.py.2
mv $WORKSPACE/UMCloudDj/settings.py.2 $WORKSPACE/UMCloudDj/settings.py

sed -i.bak "/^##PASSW/a \ \ \ \ \ \ \ \ 'PASSWORD':'${PGPASSWORD}'," $WORKSPACE/UMCloudDj/settings.py
grep -v "^##PASS*" $WORKSPACE/UMCloudDj/settings.py $WORKSPACE/UMCloudDj/settings.py.2
mv $WORKSPACE/UMCloudDj/settings.py.2 $WORKSPACE/UMCloudDj/settings.py

python manage.py syncdb

#We have to get eXe to another directory
cd /home/ubuntu/
if [ "$?" != "0" ]; then
    echo "Folder Exists"
    git clone https://github.com/UstadMobile/exelearning-ustadmobile-work.git
    if [ "$?" != "0" ]; then
        echo "Not a new exepull run"
        cd exelearning-ustadmobile-work
        git pull
        cd ..
    fi
fi

if [ "$?" == "0" ]; then
    echo "The directory /home/ubuntu/ does not exists for eXe to reside. Exiting.."
    exit 1
fi

cd exelearning-ustadmobile-work
git checkout 8bfa72500c103a05514b2757c2bc915a31172b1c

cd $WORKSPACE


#run tests
#./unit-test-setup-android.sh emulate
coverage run --source='.' manage.py test
#python manage.py test
if [ "$?" != "0" ]; then
        echo "UMCloudDj UNIT TESTS FAIL: STOP!"
        exit 1
fi

echo "UMCloudDj UNIT TESTS PASS: CONTINUE"


cd $WORKSPACE
DATE=`date +%Y-%m-%d-%H-%M-%S`
mkdir build
rm -f build/*tar.gz
tar -zvcf build/UMCloudDj_${DATE}.tar.gz --exclude='build' *
coverage report
coverage report --omit=*lrs*,*oauth*,*django_messages*

