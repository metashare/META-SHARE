@echo off

AltovaXML /xslt1 "MappingMapToMETA-SHARE-Resource.xslt" /in "C:/develop/metashare/transform/schemaTransform/toBeTransformed - Copy/CorporaAll/Corpus/UP10_7.4.xml" /out "C:/develop/metashare/transform/schemaTransform/output/outTest.xml" %*
IF ERRORLEVEL 1 EXIT/B %ERRORLEVEL%
