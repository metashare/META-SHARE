@echo off

AltovaXML /xslt1 "MappingMapToMETA-SHARE-Resource.xslt" /in "../ceasar/404.xml" /out "META-SHARE-Resource.xml" %*
IF ERRORLEVEL 1 EXIT/B %ERRORLEVEL%
