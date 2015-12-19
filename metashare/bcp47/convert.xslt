<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns:xs="http://www.w3.org/2001/XMLSchema" version="2.0">
	<xsl:template match="/">
		<xsl:for-each select="//identificationInfo">
			<xsl:value-of select="."/>
		</xsl:for-each>
	</xsl:template>
</xsl:stylesheet>