<?xml version="1.0" encoding="UTF-8"?>
<!-- Upgrades v2.x schema compliant XML documents to v3.0, which currently only involves 
  changes to the available license names -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.ilsp.gr/META-XMLSchema"
  xmlns:ms="http://www.ilsp.gr/META-XMLSchema" exclude-result-prefixes="xsl ms">
  <xsl:output method="xml" encoding="UTF-8" indent="no" />

  <!-- copy template for license names with the required name change mappings -->
  <xsl:template match="ms:licence">
    <licence>
      <xsl:choose>
        <!-- change license names ending with “_3.0” -->
        <xsl:when test="text() = 'CC_BY-NC-SA_3.0'">
          <xsl:message>
            <xsl:text>Changed license name “CC_BY-NC-SA_3.0” to “CC-BY-NC-SA”.</xsl:text>
          </xsl:message>
          <xsl:text>CC-BY-NC-SA</xsl:text>
        </xsl:when>
        <xsl:when test="text() = 'CC_BY-SA_3.0'">
          <xsl:message>
            <xsl:text>Changed license name “CC_BY-SA_3.0” to “CC-BY-SA”.</xsl:text>
          </xsl:message>
          <xsl:text>CC-BY-SA</xsl:text>
        </xsl:when>
        <!-- change other license names starting with “CC_” -->
        <xsl:when test="starts-with(text(), 'CC_')">
          <xsl:text>CC-</xsl:text>
          <xsl:value-of select="substring-after(text(), 'CC_')" />
          <xsl:message>
            <xsl:text>Changed “CC_” prefix in license name to “CC-”: </xsl:text>
            <xsl:value-of select="text()" />
          </xsl:message>
        </xsl:when>
        <!-- change various special case license names -->
        <xsl:when test="text() = 'CC0'">
          <xsl:message>
            <xsl:text>Changed license name “CC0” to “CC-ZERO”.</xsl:text>
          </xsl:message>
          <xsl:text>CC-ZERO</xsl:text>
        </xsl:when>
        <xsl:when test="text() = 'ApacheLicence_V2.0'">
          <xsl:message>
            <xsl:text>Changed license name “ApacheLicence_V2.0” to “ApacheLicence_2.0”.</xsl:text>
          </xsl:message>
          <xsl:text>ApacheLicence_2.0</xsl:text>
        </xsl:when>
        <xsl:when test="text() = 'LGPLv3'">
          <xsl:message>
            <xsl:text>Changed license name “LGPLv3” to “LGPL”.</xsl:text>
          </xsl:message>
          <xsl:text>LGPL</xsl:text>
        </xsl:when>
        <!-- change various special case license names starting with “MSCommons_” -->
        <xsl:when test="text() = 'MSCommons_COM-NR'">
          <xsl:message>
            <xsl:text>Changed license name “MSCommons_COM-NR” to “MS-C-NoReD”.</xsl:text>
          </xsl:message>
          <xsl:text>MS-C-NoReD</xsl:text>
        </xsl:when>
        <xsl:when test="text() = 'MSCommons_COM-NR-FF'">
          <xsl:message>
            <xsl:text>Changed license name “MSCommons_COM-NR-FF” to “MS-C-NoReD-FF”.</xsl:text>
          </xsl:message>
          <xsl:text>MS-C-NoReD-FF</xsl:text>
        </xsl:when>
        <xsl:when test="text() = 'MSCommons_COM-NR-ND'">
          <xsl:message>
            <xsl:text>Changed license name “MSCommons_COM-NR-ND” to “MS-C-NoReD-ND”.</xsl:text>
          </xsl:message>
          <xsl:text>MS-C-NoReD-ND</xsl:text>
        </xsl:when>
        <xsl:when test="text() = 'MSCommons_COM-NR-ND-FF'">
          <xsl:message>
            <xsl:text>Changed license name “MSCommons_COM-NR-ND-FF” to “MS-C-NoReD-ND-FF”.</xsl:text>
          </xsl:message>
          <xsl:text>MS-C-NoReD-ND-FF</xsl:text>
        </xsl:when>
        <xsl:when test="text() = 'MSCommons_NoCOM-NC-NR'">
          <xsl:message>
            <xsl:text>Changed license name “MSCommons_NoCOM-NC-NR” to “MS-NC-NoReD”.</xsl:text>
          </xsl:message>
          <xsl:text>MS-NC-NoReD</xsl:text>
        </xsl:when>
        <xsl:when test="text() = 'MSCommons_NoCOM-NC-NR-FF'">
          <xsl:message>
            <xsl:text>Changed license name “MSCommons_NoCOM-NC-NR-FF” to “MS-NC-NoReD-FF”.</xsl:text>
          </xsl:message>
          <xsl:text>MS-NC-NoReD-FF</xsl:text>
        </xsl:when>
        <xsl:when test="text() = 'MSCommons_NoCOM-NC-NR-ND'">
          <xsl:message>
            <xsl:text>Changed license name “MSCommons_NoCOM-NC-NR-ND” to “MS-NC-NoReD-ND”.</xsl:text>
          </xsl:message>
          <xsl:text>MS-NC-NoReD-ND</xsl:text>
        </xsl:when>
        <xsl:when test="text() = 'MSCommons_NoCOM-NC-NR-ND-FF'">
          <xsl:message>
            <xsl:text>Changed license name “MSCommons_NoCOM-NC-NR-ND-FF” to “MS-NC-NoReD-ND-FF”.</xsl:text>
          </xsl:message>
          <xsl:text>MS-NC-NoReD-ND-FF</xsl:text>
        </xsl:when>
        <!-- change all other license names starting with “MSCommons_” -->
        <xsl:when test="starts-with(text(), 'MSCommons_')">
          <xsl:text>MSCommons-</xsl:text>
          <xsl:value-of select="substring-after(text(), 'MSCommons_')" />
          <xsl:message>
            <xsl:text>Changed “MSCommons_” prefix in license name to “MSCommons-”: </xsl:text>
            <xsl:value-of select="text()" />
          </xsl:message>
        </xsl:when>
        <!-- leave all other license names unchanged -->
        <xsl:otherwise>
          <xsl:value-of select="text()" />
        </xsl:otherwise>
      </xsl:choose>
    </licence>
  </xsl:template>

  <!-- make sure that any xsi:schemaLocation points to the latest schema version -->
  <xsl:template match="@xsi:schemaLocation">
    <!-- we assume that there will only be xsi:schemaLocation attributes that were
      generated by the META-SHARE software, i.e., there will not be multiple schema
      locations in the attribute -->
    <xsl:attribute name="xsi:schemaLocation">
      <xsl:text>http://www.ilsp.gr/META-XMLSchema http://metashare.ilsp.gr/META-XMLSchema/v3.0/META-SHARE-Resource.xsd</xsl:text>
    </xsl:attribute>
  </xsl:template>

  <!-- standard copy template for everything else -->
  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()" />
    </xsl:copy>
  </xsl:template>

</xsl:stylesheet>
