echo "Pulling from UMCloudDj.."
git pull

echo "Pulling from LRS.."
cd  ../
git clone https://github.com/varunasingh/ADL_LRS.git ADL_LRS_VS
echo "Installing ADL_LRS in the UMCloudDj project.."
cp -r ADL_LRS_VS/lrs UMCloudDj/
cp -r ADL_LRS_VS/oauth_provider UMCloudDj/
cp -r ADL_LRS_VS/adl_lrs UMCloudDj/
rm -f UMCloudDj/adl_lrs/settings.py

rm -rf ADL_LRS_VS

cd UMCloudDj/

 if [ ! -f UMCloudDj/settings.py ]; then
  echo "settings.py file does not exist. Creating it.."
  cp UMCloudDj/settings.py.edit UMCloudDj/settings.py
  sed -i.bak -e 's/^SECRET_KEY/##/' UMCloudDj/settings.py
  echo "SECRET_KEY=\"@##:{}@#L@#L@#:@}#@{#{Ch@Th!*Ust@d/'/0|3||_3T|-|33C&3%/<3Y}@#}{@#{@}##@:&&*(&*(&*^&\"" >> UMCloudDj/settings.py
 else
  echo "settings.py file already exists."
 fi
echo "finished"

