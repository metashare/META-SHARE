#!/bin/bash

export METASHARE_SW_DIR="$PWD"

cd "$METASHARE_SW_DIR/metashare" && "./start-solr.sh" && cd "$METASHARE_SW_DIR"

source "$METASHARE_SW_DIR/venv/bin/activate"

cp "$METASHARE_SW_DIR/misc/tools/migration/to_3_1/call_south_migration_scripts.py" "$METASHARE_SW_DIR/metashare/call_south_migration_scripts.py"

python "$METASHARE_SW_DIR/metashare/call_south_migration_scripts.py"

rm "$METASHARE_SW_DIR/metashare/call_south_migration_scripts.py"

cd "$METASHARE_SW_DIR/metashare" && "./stop-solr.sh" && cd "$METASHARE_SW_DIR"

deactivate