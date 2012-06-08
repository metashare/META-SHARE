
echo "Starting Multi-server test"

export SOLR_DIR=../../solr
export METASHARE_DIR=/home/metashare/git/META-SHARE-NEW/metashare

export SOLR_PORT=4444
export DJANGO_PORT=8001
export DJANGO_CONF_NUM=1
./start_instance.sh &

exit

export SOLR_PORT=4445
export DJANGO_PORT=8002
export DJANGO_CONF_NUM=2
./start_instance.sh &

