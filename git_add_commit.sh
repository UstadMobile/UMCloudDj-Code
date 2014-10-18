cp UMCloudDj/settings.py UMCloudDj/settings.py.edit
sed -i.bak -e 's/^SECRET_KEY.*/##/' UMCloudDj/settings.py.edit
sed -i.bak -e "s/.*'USER'.*/##USER/" UMCloudDj/settings.py.edit
sed -i.bak -e "s/.*'PASSWORD'.*/##PASSWORD/" UMCloudDj/settings.py.edit
sed -i.bak -e "s/EMAIL_HOST_PASSWORD.*/###EMAIL_HOST_PASSWORD=''/" UMCloudDj/settings.py.edit
sed -i.bak -e "s/EMAIL_HOST=.*/###EMAIL_HOST=''/" UMCloudDj/settings.py.edit
sed -i.bak -e "s/EMAIL_PORT.*/###EMAIL_PORT=/" UMCloudDj/settings.py.edit
sed -i.bak -e "s/EMAIL_HOST_USER.*/##EMAIL_HOST_USER=''/" UMCloudDj/settings.py.edit
echo "SECRET_KEY=\"ChangeMeLikeYouChange\"" >> UMCloudDj/settings.py.edit
git add --all .
git commit
