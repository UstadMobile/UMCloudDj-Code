#run tests
#./unit-test-setup-android.sh emulate
coverage run --source='.' manage.py test
#python manage.py test
if [ "$?" != "0" ]; then
        echo "UMCloudDj UNIT TESTS FAIL: STOP!"
        exit 1
fi

echo "UMCloudDj UNIT TESTS PASS: CONTINUE"

coverage report
coverage report --omit=*lrs*,*oauth*,*django_messages*
coverage html --omit=*lrs*,*oauth*,*django_messages*
rsync -a htmlcov/ UMCloudDj/media/eXeExport/htmlcov/
rm -rf htmlcov/
