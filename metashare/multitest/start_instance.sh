
echo "Starting instance"

CURRENT_DIR=`pwd`
echo "Current dir is " $CURRENT_DIR

cd $SOLR_DIR

java -Djetty.port=$SOLR_PORT -jar start.jar &

sleep 5

cd $CURRENT_DIR

cp metashare.db $METASHARE_DIR/metashare$DJANGO_CONF_NUM.db

cd $METASHARE_DIR
echo "Current directory is " `pwd`
echo "Solr port is " $SOLR_PORT
echo "Conf num is " $DJANGO_CONF_NUM
echo "Starting python on port " $DJANGO_PORT
python manage.py runserver 0.0.0.0:$DJANGO_PORT --noreload &> metashare$DJANGO_CONF_NUM.log


