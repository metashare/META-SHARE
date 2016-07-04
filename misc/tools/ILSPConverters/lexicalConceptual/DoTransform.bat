@echo off

AltovaXML /xslt1 "MappingMapToMETA-SHARE-Resource.xslt" /in "../toBeTransformed/tilde_node/lexicalConceptual/resource-8.xml" /out "META-SHARE-Resource.xml" %*
IF ERRORLEVEL 1 EXIT/B %ERRORLEVEL%
