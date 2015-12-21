#!/bin/bash

# Build the docs:
(cd misc/docs/ && make html)
cd ..
git clone "https://${GH_AUTH}@${GH_REF}" metashare_docs || exit 1
cd metashare_docs
git checkout gh-pages
git config user.name "Travis-CI"
git config user.email "travis@travis-ci.org"
# Replace the old web pages by the new ones
rm -rf dev
mv ../META-SHARE/misc/docs/_build/html/ dev || exit 1
git add --all dev || exit 1
git commit -m "Automatic update of documentation" && git push origin gh-pages
exit 0
