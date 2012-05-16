This folder contains a tool to upgrade META-SHARE resources as XML files
from earlier version to the latest version.

This tool will convert all META-SHARE XML files in a source folder to META-SHARE
format 2.1 versions in a target folder.
Usage:
java [options] -jar metashare-resource-upgrader.jar source-folder/ target-folder/
options: -Dmetashare.targetVersion=... (one of v11, v20, v21; defaults to v21)
         -Dmetashare.sourceVersion=... (one of v10, v11, v20; if not set, will guess)

For more information about upgrading META-SHARE to newer versions, see the Installation
documentation at https://github.com/metashare/META-SHARE/tree/master/misc/docs.