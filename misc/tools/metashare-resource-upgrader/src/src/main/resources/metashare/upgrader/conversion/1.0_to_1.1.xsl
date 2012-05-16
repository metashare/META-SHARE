<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:ms="http://www.ilsp.gr/META-XMLSchema"
  exclude-result-prefixes="ms"
  xmlns="http://www.ilsp.gr/META-XMLSchema"
  version="1.0">

  <xsl:output method="xml"/>

  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>

  <!-- ResourceType / PersonInfo renamed to contactPerson -->
  <xsl:template match="ms:Resource/ms:PersonInfo">
    <contactPerson>
      <xsl:apply-templates select="@*|node()"/>
    </contactPerson>
  </xsl:template>

  <!-- ResourceType / CorpusInfo removed -->
  <xsl:template match="ms:Resource/ms:CorpusInfo">
  </xsl:template>

  <!-- CommunicationInfoType / region removed -->
  <xsl:template match="ms:CommunicationInfo/ms:region">
  </xsl:template>

  <!-- ActualUseInfoType / usage changed to usageProject -->
  <xsl:template match="ms:ActualUseInfo/ms:usage">
    <usageProject>
      <xsl:apply-templates select="@*|node()"/>
    </usageProject>
  </xsl:template>

  <!-- ContentInfoType / toolService renamed to technologyToolService -->
  <xsl:template match="ms:ContentInfo/ms:toolService">
    <technologyToolService>
      <xsl:apply-templates select="@*|node()"/>
    </technologyToolService>
  </xsl:template>

  <!-- CharacterEncodingInfoType / SizeInfo renamed to sizePerCharacterEncoding
       -->
  <xsl:template match="ms:CharacterEncodingInfo/ms:SizeInfo">
    <sizePerCharacterEncoding>
      <xsl:apply-templates select="@*|node()"/>
    </sizePerCharacterEncoding>
  </xsl:template>

  <!-- TextClassificationInfoType / SizeInfo renamed to sizePerTextClassification -->
  <xsl:template match="ms:TextClassificationInfo/ms:SizeInfo">
    <sizePerTextClassification>
      <xsl:apply-templates select="@*|node()"/>
    </sizePerTextClassification>
  </xsl:template>

  <!-- AnnotationInfoType / SizeInfo renamed to sizePerAnnotation -->
  <xsl:template match="ms:AnnotationInfo/ms:SizeInfo">
    <sizePerAnnotation>
      <xsl:apply-templates select="@*|node()"/>
    </sizePerAnnotation>
  </xsl:template>

  <!-- TextCorpusCreationInfoType and TextCorpusCreationInfo completely
       removed -->
  <xsl:template match="ms:TextCorpusCreationInfo">
  </xsl:template>

  <!--  LanguageInfoType / SizeInfo renamed to sizePerLanguage -->
  <xsl:template match="ms:LanguageInfo/ms:SizeInfo">
    <sizePerLanguage>
      <xsl:apply-templates select="@*|node()"/>
    </sizePerLanguage>
  </xsl:template>

  <!-- LanguageVarietyInfoType / SizeInfo renamed to sizePerLanguageVariety -->
  <xsl:template match="ms:LanguageVarietyInfo/ms:SizeInfo">
    <sizePerLanguageVariety>
      <xsl:apply-templates select="@*|node()"/>
    </sizePerLanguageVariety>
  </xsl:template>

  <!-- TextFormatInfoType / SizeInfo renamed to sizePerTextFormat -->
  <xsl:template match="ms:TextFormatInfo/ms:SizeInfo">
    <sizePerTextFormat>
      <xsl:apply-templates select="@*|node()"/>
    </sizePerTextFormat>
  </xsl:template>

  <!-- DomainInfoType / SizeInfo renamed to sizePerDomain -->
  <xsl:template match="ms:DomainInfo/ms:SizeInfo">
    <sizePerDomain>
      <xsl:apply-templates select="@*|node()"/>
    </sizePerDomain>
  </xsl:template>

  <!-- TimeCoverageInfoType  / SizeInfo renamed to sizePerTimeCoverage -->
  <xsl:template match="ms:TimeCoverageInfo/ms:SizeInfo">
    <sizePerTimeCoverage>
      <xsl:apply-templates select="@*|node()"/>
    </sizePerTimeCoverage>
  </xsl:template>

  <!-- GeographicCoverageInfoType / SizeInfo renamed to sizePerGeographicCoverage -->
  <xsl:template match="ms:GeographicCoverageInfo/ms:SizeInfo">
    <sizePerGeographicCoverage>
      <xsl:apply-templates select="@*|node()"/>
    </sizePerGeographicCoverage>
  </xsl:template>

  <!-- ValidationInfoType / SizeInfo renamed to sizePerValidation -->
  <xsl:template match="ms:ValidationInfo/ms:SizeInfo">
    <sizePerValidation>
      <xsl:apply-templates select="@*|node()"/>
    </sizePerValidation>
  </xsl:template>

  <!-- ValidationInfoType / SizeInfo renamed to sizePerValidation -->
  <xsl:template match="ms:mimeType">
    <mime-type>
      <xsl:apply-templates select="@*|node()"/>
    </mime-type>
  </xsl:template>

  <!-- correct spelling of IPRHolder -->
  <xsl:template match="ms:IPRHolder">
    <iprHolder>
      <xsl:apply-templates select="@*|node()"/>
    </iprHolder>
  </xsl:template>

  <!-- wrong true values -->
  <xsl:template match="ms:validated[text()=1]|ms:annotationStandoff[text()=1]">
    <xsl:element name="{name()}">true</xsl:element>
  </xsl:template>

  <!-- wrong white space -->
  <xsl:template match="ms:languageVarietyName|ms:useNLPSpecific|ms:size">
    <xsl:element name="{name()}">
      <xsl:value-of select="normalize-space(text())"/>
    </xsl:element>
  </xsl:template>

</xsl:stylesheet>
