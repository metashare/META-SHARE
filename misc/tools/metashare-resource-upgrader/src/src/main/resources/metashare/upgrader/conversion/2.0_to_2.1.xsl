<?xml version="1.0" encoding="UTF-8"?>
<!-- converts META-SHARE metadata descriptions from schema version 2.0 to 2.1 -->
<xsl:stylesheet version="1.0" xmlns:ms="http://www.ilsp.gr/META-XMLSchema" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" exclude-result-prefixes="xsl">
    <xsl:output method="xml" encoding="UTF-8" indent="yes"/>
    
	<xsl:template match="@*|node()">
		<xsl:copy>
			<xsl:apply-templates select="@*|node()"/>
		</xsl:copy>
	</xsl:template>
	
	<xsl:template match="@lang">
		<xsl:choose>
			<xsl:when test=".='English'">
			<xsl:attribute name="lang" namespace="">en</xsl:attribute>          	
			</xsl:when>
			<xsl:when test=".='French'">
			<xsl:attribute name="lang" namespace="">fr</xsl:attribute>    	
			</xsl:when>			
		</xsl:choose>	
	</xsl:template>
	
	
	<xsl:template match="*[. = 'True']">
	  <xsl:copy>
	    <xsl:apply-templates select="@*"/>
	    <xsl:text>true</xsl:text>
	 </xsl:copy>
	</xsl:template>

	<xsl:template match="*[. = 'False']">
	  <xsl:copy>
	    <xsl:apply-templates select="@*"/>
	    <xsl:text>false</xsl:text>
	 </xsl:copy>
	</xsl:template>

	<xsl:template match="ms:year">
		<ms:year>
			<xsl:value-of select="substring(text(), 1, 4)"/>
		</ms:year>
	</xsl:template>
	
	<xsl:template match="ms:price">
		<ms:fee>	
			<xsl:value-of select="."/>	
		</ms:fee>		
	</xsl:template>
	
	<xsl:template match="ms:sizePerLanguageVariety">
		<xsl:variable name="size" select="./ms:size"/>
		<xsl:variable name="sizeUnit" select="./ms:sizeUnit"/>
		<xsl:choose>
			<xsl:when test="$size=0 and $sizeUnit='units'">			
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy>
					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>	
	</xsl:template>
	
	<xsl:template match="ms:licence">
		<xsl:variable name="licence" select="."/>
		<xsl:choose>
			<xsl:when test="$licence='CC'"><ms:licence>CC0</ms:licence>		
			</xsl:when>
			<xsl:when test="$licence='GeneralLicenceGrant'"><ms:licence>other</ms:licence>		
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy>
					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>			
	</xsl:template>
	
	<xsl:template match="ms:conformanceToStandardsBestPractices">
		<xsl:variable name="conf" select="."/>
		<xsl:choose>		
			<xsl:when test="$conf='CES' or $conf='EML' or $conf='EMMA' or $conf='GMX' or $conf='HamNoSys' or $conf='InkML' or $conf='ISO12620' or $conf='ISO16642' or $conf='ISO1987' or $conf='ISO26162' or $conf='ISO30042' or $conf='ISO704' or $conf='LMF' or $conf='MAF' or $conf='MLIF' or $conf='MULTEXT' or $conf='multimodalInteractionFramework' or $conf='OAXAL' or $conf='OWL' or $conf='pennTreeBank' or $conf='pragueTreebank' or $conf='RDF' or $conf='SemAF' or $conf='SemAF_DA' or $conf='SemAF_NE' or $conf='SemAF_SRL' or $conf='SemAF_DS' or $conf='SKOS' or $conf='SRX' or $conf='SynAF' or $conf='TBX' or $conf='TMX' or $conf='TEI' or $conf='TEI_P3' or $conf='TEI_P4' or $conf='TEI_P5' or $conf='TimeML' or $conf='XCES' or $conf='XLIFF' or $conf='MUMIN' or $conf='BLM'">	
				<xsl:copy>
					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>	
			</xsl:when>
			<xsl:otherwise>
			<ms:conformanceToStandardsBestPractices>other</ms:conformanceToStandardsBestPractices>				
			</xsl:otherwise>
		</xsl:choose>			
	</xsl:template>
	

</xsl:stylesheet>
