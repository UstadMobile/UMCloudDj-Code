cp UMCloudDj/settings.py UMCloudDj/settings.py.edit
sed -i.bak -e 's/^SECRET_KEY.*/##/' UMCloudDj/settings.py.edit
sed -i.bak -e "s/.*'USER'.*/##USER/" UMCloudDj/settings.py.edit
sed -i.bak -e "s/.*'PASSWORD'.*/##PASSWORD/" UMCloudDj/settings.py.edit
echo "SECRET_KEY=\"ChangeMeLikeYouChange\"" >> UMCloudDj/settings.py.edit
git add --all .
git commit
