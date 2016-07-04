<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns="http://www.clarin.eu/cmd/" 
xmlns:ms="http://www.ilsp.gr/META-XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xalan="http://xml.apache.org/xslt"  xmlns:date="http://exslt.org/dates-and-times" 
exclude-result-prefixes="ms xalan date" >
	<xsl:output method="xml" version="1.0" encoding="UTF-8" indent="yes" xalan:indent-amount="4"/>
	<xsl:strip-space elements="*"/>
	<xsl:template match="*">
    	<xsl:element name="{local-name(.)}">
    		<xsl:apply-templates select="@* | node()"/>
    	</xsl:element>
    </xsl:template>
    <xsl:template match ="@*" >
			<xsl:if test="local-name() = 'lang'">
				<xsl:attribute name ="xml:lang">
					<xsl:value-of select ="." />
				</xsl:attribute>
			</xsl:if>
		</xsl:template>
	<xsl:template name="personOrOrganizationInfo">
		<xsl:choose>
			<xsl:when test="ms:personInfo">
				<xsl:element name="{concat(local-name(), 'Person')}">
					<xsl:element name="role">
						<xsl:value-of select ="local-name()"/>
					</xsl:element>
					<xsl:element name="{local-name(ms:personInfo)}">
						<xsl:for-each select="ms:personInfo/child::*">
							<xsl:sort select="not(child::*)" order="descending"/>
							<xsl:choose>
								<xsl:when test="self::ms:affiliation">
									<xsl:element name="{local-name()}">
										<xsl:element name="role">
											<xsl:value-of select ="local-name()"/>
										</xsl:element>
										<xsl:element name="organizationInfo">
											<xsl:apply-templates select="child::*"/>
										</xsl:element>
									</xsl:element>
								</xsl:when>
								<xsl:otherwise>
									<xsl:apply-templates select="."/>
								</xsl:otherwise>
							</xsl:choose>
						</xsl:for-each>
					</xsl:element>
				</xsl:element>
			</xsl:when>
			<xsl:otherwise>
				<xsl:element name="{concat(local-name(), 'Organization')}">
					<xsl:element name="role">
						<xsl:value-of select ="local-name()"/>
					</xsl:element>
					<xsl:apply-templates select="child::*"/>
				</xsl:element>			
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	<xsl:template name="reportInfo">
		<xsl:choose>
			<xsl:when test="child::ms:documentUnstructured">
				<xsl:element name="{concat(local-name(), 'Unstructured')}">
					<xsl:element name="role">
						<xsl:value-of select ="local-name()"/>
					</xsl:element>
					<xsl:apply-templates select="node()"/>
				</xsl:element>
			</xsl:when>
			<xsl:otherwise>
				<xsl:element name="{concat(local-name(), 'Structured')}">
					<xsl:element name="role">
						<xsl:value-of select ="local-name()"/>
					</xsl:element>
					<xsl:apply-templates select="node()"/>
				</xsl:element>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	<xsl:template match="ms:distributionInfo">
		<xsl:element name="{local-name()}">
            <xsl:for-each select="child::*">
				<xsl:sort select="not(child::*)" order="descending"/>
				<xsl:choose>
					<xsl:when test="self::ms:iprHolder">
						<xsl:call-template name="personOrOrganizationInfo"/>
					</xsl:when>
					<xsl:when test="self::ms:licenceInfo">
						<xsl:apply-templates select="."/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
            </xsl:for-each>
		</xsl:element>
	</xsl:template>
	<xsl:template match="ms:licenceInfo">
		<xsl:element name="{local-name()}">
            <xsl:for-each select="child::*">
				<xsl:sort select="not(child::*)" order="descending"/>
				<xsl:choose>
					<xsl:when test="self::ms:licensor or self::ms:distributionRightsHolder">
						<xsl:call-template name="personOrOrganizationInfo"/>
					</xsl:when>
					<xsl:when test="self::ms:downloadLocation or self::ms:executionLocation">
						<xsl:choose>
							<xsl:when test="contains(string(preceding-sibling::ms:licence), 'MSCommons')"/>
							<xsl:otherwise>
								<xsl:apply-templates select="."/>
							</xsl:otherwise>
						</xsl:choose>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
            </xsl:for-each>
		</xsl:element>
	</xsl:template>
	<xsl:template match="ms:contactPerson | ms:metadataCreator">
		<xsl:param name="info" select="'contactPerson'"/>
		<xsl:element name="{$info}">
			<xsl:element name="role">
				<xsl:value-of select ="local-name()"/>
			</xsl:element>
			<xsl:element name="personInfo">
				<xsl:for-each select="child::*">
					<xsl:sort select="not(child::*)" order="descending"/>
					<xsl:choose>
						<xsl:when test="self::ms:affiliation">
							<xsl:element name="affiliation">
								<xsl:element name="role">
									<xsl:value-of select ="local-name()"/>
								</xsl:element>
								<xsl:element name="organizationInfo">
									<xsl:for-each select="child::*">
										<xsl:apply-templates select="."/>
									</xsl:for-each>
								</xsl:element>
							</xsl:element>
						</xsl:when>
						<xsl:otherwise>
							<xsl:apply-templates select="."/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:for-each>
			</xsl:element>
		</xsl:element>
	</xsl:template>	
	<xsl:template match="ms:metadataInfo">
		<xsl:element name="{local-name()}">
			<xsl:for-each select="child::*">
				<xsl:sort select="not(child::*)" order="descending"/>
				<xsl:choose>
					<xsl:when test="self::ms:metadataCreator">
						<xsl:apply-templates select=".">
							<xsl:with-param name="info" select="'metadataCreator'"/>
						</xsl:apply-templates>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>

	<xsl:template match="ms:validationInfo">
		<xsl:element name="{local-name()}">
            <xsl:for-each select="child::*">
				<xsl:sort select="not(child::*)" order="descending"/>
				<xsl:choose>
					<xsl:when test="self::ms:sizePerValidation">
						<xsl:element name="{local-name()}">
							<xsl:element name="role">
								<xsl:value-of select="local-name()"/>
							</xsl:element>
							<xsl:element name="sizeInfo">
								<xsl:apply-templates select="child::*"/>
							</xsl:element>
						</xsl:element>
					</xsl:when>
					<xsl:when test="self::ms:validationReport">
						<xsl:call-template name="reportInfo"/>
					</xsl:when>
					<xsl:when test="self::ms:validator">
						<xsl:call-template name="personOrOrganizationInfo"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
            </xsl:for-each>
        </xsl:element>
	</xsl:template>
	<xsl:template match="ms:usageInfo">
		<xsl:element name="{local-name()}">
            <xsl:for-each select="child::*">
				<xsl:sort select="not(child::*)" order="descending"/>
				<xsl:choose>
					<xsl:when test="self::ms:actualUseInfo">
						<xsl:element name="{local-name()}">
							<xsl:for-each select="child::*">
								<xsl:sort select="not(child::*)" order="descending"/>
								<xsl:choose>
									<xsl:when test="self::ms:usageReport">
										<xsl:call-template name="reportInfo"/>
									</xsl:when>
									<xsl:when test="self::ms:usageProject">
										<xsl:element name="{local-name()}">
											<xsl:element name="role">
												<xsl:value-of select ="local-name()"/>
											</xsl:element>
											<xsl:element name="projectInfo">
												<xsl:apply-templates select="node()"/>
											</xsl:element>
										</xsl:element>
									</xsl:when>
									<xsl:otherwise>
										<xsl:apply-templates select="."/>
									</xsl:otherwise>
								</xsl:choose>
							</xsl:for-each>
						</xsl:element>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
            </xsl:for-each>
		</xsl:element>
	</xsl:template>
	<xsl:template match="ms:resourceDocumentationInfo">
		<xsl:element name="{local-name()}">
            <xsl:for-each select="child::*">
				<xsl:sort select="not(child::*)" order="descending"/>
				<xsl:choose>
					<xsl:when test="self::ms:documentation">
						<xsl:call-template name="reportInfo"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
            </xsl:for-each>
        </xsl:element>
	</xsl:template>
	<xsl:template match="ms:resourceCreationInfo">
		<xsl:element name="{local-name()}">
            <xsl:for-each select="child::*">
				<xsl:sort select="not(child::*)" order="descending"/>
				<xsl:choose>
					<xsl:when test="self::ms:resourceCreator">
						<xsl:call-template name="personOrOrganizationInfo"/>
					</xsl:when>
					<xsl:when test="self::ms:fundingProject">
						<xsl:element name="{local-name()}">
							<xsl:element name="role">
								<xsl:value-of select ="local-name()"/>
							</xsl:element>
							<xsl:element name="projectInfo">
								<xsl:apply-templates select="node()"/>
							</xsl:element>
						</xsl:element>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
            </xsl:for-each>
        </xsl:element>
	</xsl:template>
	<xsl:template match="ms:languageInfo">
		<xsl:element name="{local-name()}">
			<xsl:for-each select="child::*">
				<xsl:sort select="not(child::*)" order="descending"/>
				<xsl:choose>
					<xsl:when test="self::ms:sizePerLanguage">
						<xsl:call-template name="sizeInfoPerCategory"/>
					</xsl:when>
					<xsl:when test="self::ms:languageVarietyInfo">
						<xsl:element name="{local-name()}">
							<xsl:for-each select="child::*">
								<xsl:sort select="not(child::*)" order="descending"/>
								<xsl:choose>
									<xsl:when test="self::ms:sizePerLanguageVariety">
										<xsl:call-template name="sizeInfoPerCategory"/>
									</xsl:when>
									<xsl:otherwise>
										<xsl:apply-templates select="."/>
									</xsl:otherwise>
								</xsl:choose>
							</xsl:for-each>
						</xsl:element>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
	<xsl:template name="info_with_sizeInfo">
		<xsl:element name="{local-name()}">
			<xsl:for-each select="child::*">
				<xsl:sort select="not(child::*)" order="descending"/>
				<xsl:choose>
					<xsl:when test="contains(local-name(), 'size')">
						<xsl:call-template name="sizeInfoPerCategory"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
	<xsl:template match="ms:annotationInfo">
		<xsl:element name="annotationInfo">
			<xsl:for-each select="child::*">
				<xsl:sort select="not(child::*)" order="descending"/>
				<xsl:choose>
					<xsl:when test="self::ms:annotationManual">
						<xsl:call-template name="reportInfo"/>
					</xsl:when>
					<xsl:when test="self::ms:sizePerAnnotation">
						<xsl:call-template name="sizeInfoPerCategory"/>
					</xsl:when>
					<xsl:when test="self::ms:annotator">
						<xsl:call-template name="personOrOrganizationInfo"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
	<xsl:template match="ms:creationInfo">
		<xsl:element name="creationInfo">
			<xsl:for-each select="child::*">
				<xsl:sort select="not(child::*)" order="descending"/>
				<xsl:apply-templates select="."/>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
	<xsl:template match="ms:audioContentInfo">
		<xsl:element name="audioContentInfo">
			<xsl:for-each select="child::*">
				<xsl:choose>
					<xsl:when test="self::ms:nonSpeechItems and contains(string(.), 'commercial')">
						<xsl:element name="nonSpeechItems">
							<xsl:text>commercial</xsl:text>
						</xsl:element>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
	<xsl:template name="formatInfo">
		<xsl:element name="{local-name()}">
			<xsl:for-each select="child::*">
				<xsl:sort select="not(child::*)" order="descending"/>
				<xsl:choose>
					<xsl:when test="self::ms:sizePerAudioFormat or self::ms:sizePerVideoFormat or self::ms:sizePerImageFormat">
						<xsl:call-template name="sizeInfoPerCategory"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
	<xsl:template match="ms:recordingInfo">
		<xsl:element name="{local-name()}">
			<xsl:for-each select="child::*">
				<xsl:sort select="not(child::*)" order="descending"/>
				<xsl:choose>
					<xsl:when test="self::ms:recorder">
						<xsl:call-template name="personOrOrganizationInfo"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
	<xsl:template match="ms:toolServiceOperationInfo">
		<xsl:element name="{local-name()}">
			<xsl:for-each select="child::*">
				<xsl:sort select="not(child::*)" order="descending"/>
				<xsl:apply-templates select="."/>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
	<xsl:template match="ms:runningEnvironmentInfo">
		<xsl:element name="{local-name()}">
            <xsl:for-each select="child::*">
				<xsl:sort select="not(child::*)" order="descending"/>
				<xsl:apply-templates select="."/>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
	<xsl:template match="ms:toolServiceEvaluationInfo">
		<xsl:element name="{local-name()}">
            <xsl:for-each select="child::*">
				<xsl:sort select="not(child::*)" order="descending"/>
					<xsl:choose>
						<xsl:when test="self::ms:evaluationReport">
							<xsl:call-template name="reportInfo"/>
						</xsl:when>
						<xsl:when test="self::ms:evaluator">
							<xsl:call-template name="personOrOrganizationInfo"/>
						</xsl:when>
						<xsl:otherwise>
							<xsl:apply-templates select="."/>
						</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
	<xsl:template match="ms:toolServiceCreationInfo">
		<xsl:element name="{local-name()}">
			<xsl:for-each select="child::*">
				<xsl:sort select="not(child::*)" order="descending"/>
				<xsl:apply-templates select="."/>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
	<xsl:template name="sizeInfoPerCategory">
		<xsl:element name="{local-name()}">
            <xsl:element name="role">
				<xsl:value-of select ="local-name()"/>
			</xsl:element>
			<xsl:element name="sizeInfo">
				<xsl:apply-templates select="child::*"/>
			</xsl:element>
		</xsl:element>
	</xsl:template>
	<xsl:template match="ms:corpusTextInfo| ms:corpusAudioInfo| ms:corpusVideoInfo | ms:corpusImageInfo | ms:corpusTextNumericalInfo | ms:corpusTextNgramInfo | ms:languageDescriptionTextInfo | ms:languageDescriptionVideoInfo | ms:languageDescriptionImageInfo | ms:lexicalConceptualResourceTextInfo | ms:lexicalConceptualResourceAudioInfo |ms:lexicalConceptualResourceVideoInfo | ms:lexicalConceptualResourceImageInfo">
		<xsl:element name="{local-name()}">
			<xsl:for-each select="child::*">
				<xsl:if test="self::ms:mediaType">
					<xsl:apply-templates select="."/>
				</xsl:if>
				<xsl:if test="self::ms:lingualityInfo">
					<xsl:apply-templates select="."/>
				</xsl:if>
				<xsl:if test="self::ms:languageInfo">
					<xsl:apply-templates select="."/>
				</xsl:if>
				<xsl:if test="self::ms:modalityInfo">
					<xsl:call-template name="info_with_sizeInfo"/>
				</xsl:if>
				<xsl:if test="self::ms:sizeInfo">
					<xsl:apply-templates select="."/>
				</xsl:if>
				<xsl:if test="self::ms:textFormatInfo">
					<xsl:call-template name="info_with_sizeInfo"/>
				</xsl:if>
				<xsl:if test="self::ms:characterEncodingInfo">
					<xsl:call-template name="info_with_sizeInfo"/>
				</xsl:if>
				<xsl:if test="self::ms:annotationInfo">
					<xsl:apply-templates select="."/>
				</xsl:if>
				<xsl:if test="self::ms:domainInfo">
					<xsl:call-template name="info_with_sizeInfo"/>
				</xsl:if>
				<xsl:if test="self::ms:textClassificationInfo">
					<xsl:call-template name="info_with_sizeInfo"/>
				</xsl:if>
				<xsl:if test="self::ms:timeCoverageInfo">
					<xsl:call-template name="info_with_sizeInfo"/>
				</xsl:if>
				<xsl:if test="self::ms:geographicCoverageInfo">
					<xsl:call-template name="info_with_sizeInfo"/>
				</xsl:if>
				<xsl:if test="self::ms:creationInfo">
					<xsl:apply-templates select="."/>
				</xsl:if>
				<xsl:if test="self::ms:linkToOtherMediaInfo">
					<xsl:apply-templates select="."/>
				</xsl:if>	
				<xsl:if test="self::ms:audioSizeInfo">
					<xsl:apply-templates select="."/>
				</xsl:if>
				<xsl:if test="self::ms:audioContentInfo">
					<xsl:apply-templates select="."/>
				</xsl:if>
				<xsl:if test="self::ms:settingInfo">
					<xsl:apply-templates select="."/>
				</xsl:if>
				<xsl:if test="self::ms:audioFormatInfo">
					<xsl:call-template name="formatInfo"/>
				</xsl:if>
				<xsl:if test="self::ms:audioClassificationInfo">
					<xsl:call-template name="info_with_sizeInfo"/>
				</xsl:if>
				<xsl:if test="self::ms:recordingInfo">
					<xsl:apply-templates select="."/>
				</xsl:if>
				<xsl:if test="self::ms:captureInfo">
					<xsl:apply-templates select="."/>
				</xsl:if>			
				<xsl:if test="self::ms:videoContentInfo">
					<xsl:apply-templates select="."/>
				</xsl:if>
				<xsl:if test="self::ms:videoFormatInfo">
					<xsl:call-template name="formatInfo"/>
				</xsl:if>
				<xsl:if test="self::ms:videoClassificationInfo">
					<xsl:call-template name="info_with_sizeInfo"/>
				</xsl:if>			
				<xsl:if test="self::ms:imageContentInfo">
					<xsl:apply-templates select="."/>
				</xsl:if>
				<xsl:if test="self::ms:imageFormatInfo">
					<xsl:call-template name="formatInfo"/>
				</xsl:if>
				<xsl:if test="self::ms:imageClassificationInfo">
					<xsl:call-template name="info_with_sizeInfo"/>
				</xsl:if>			
				<xsl:if test="self::ms:textNumericalContentInfo">
					<xsl:apply-templates select="."/>
				</xsl:if>
				<xsl:if test="self::ms:textNumericalFormatInfo">
					<xsl:call-template name="info_with_sizeInfo"/>
				</xsl:if>
				<xsl:if test="self::ms:ngramInfo">
					<xsl:apply-templates select="."/>
				</xsl:if>					
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
	<xsl:template match="ms:resourceInfo" name="resourceInfo">
		<xsl:text>
</xsl:text>
		<CMD>
			<xsl:attribute name="CMDVersion">1.1</xsl:attribute>
			<xsl:attribute name="xsi:schemaLocation">
				<xsl:choose>
					<xsl:when test="ms:resourceComponentType/ms:corpusInfo">
						<xsl:text>http://www.clarin.eu/cmd/ http://catalog.clarin.eu/ds/ComponentRegistry/rest/registry/profiles/clarin.eu:cr1:p_1361876010571/xsd</xsl:text>
					</xsl:when>
					<xsl:when test="ms:resourceComponentType/ms:toolServiceInfo">
						<xsl:text>http://www.clarin.eu/cmd/ http://catalog.clarin.eu/ds/ComponentRegistry/rest/registry/profiles/clarin.eu:cr1:p_1360931019836/xsd</xsl:text>
					</xsl:when>
					<xsl:when test="ms:resourceComponentType/ms:languageDescriptionInfo">
						<xsl:text>http://www.clarin.eu/cmd/ http://catalog.clarin.eu/ds/ComponentRegistry/rest/registry/profiles/clarin.eu:cr1:p_1361876010554/xsd</xsl:text>
					</xsl:when>
					<xsl:otherwise>
						<xsl:text>http://www.clarin.eu/cmd/ http://catalog.clarin.eu/ds/ComponentRegistry/rest/registry/profiles/clarin.eu:cr1:p_1355150532312/xsd</xsl:text>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:attribute>
			<Header>
				<MdCreator>metashareToCmdi.xsl</MdCreator>
				<MdCreationDate>
					<xsl:value-of select="substring(date:date(), 1, 10)"/>
				</MdCreationDate>
				<MdProfile>
					<xsl:choose>
						<xsl:when test="ms:resourceComponentType/ms:corpusInfo">
							<xsl:text>clarin.eu:cr1:p_1361876010571</xsl:text>
						</xsl:when>
						<xsl:when test="ms:resourceComponentType/ms:toolServiceInfo">
							<xsl:text>clarin.eu:cr1:p_1360931019836</xsl:text>
						</xsl:when>
						<xsl:when test="ms:resourceComponentType/ms:languageDescriptionInfo">
							<xsl:text>clarin.eu:cr1:p_1361876010554</xsl:text>
						</xsl:when>
						<xsl:otherwise>
							<xsl:text>clarin.eu:cr1:p_1355150532312</xsl:text>
						</xsl:otherwise>
					</xsl:choose>
				</MdProfile>
			</Header>
			<Resources>
				<ResourceProxyList/>
				<JournalFileProxyList/>
				<ResourceRelationList/>
			</Resources>
			<Components>
				<resourceInfo>
					<xsl:for-each select="child::*[not(self::ms:resourceComponentType)]">
						<xsl:apply-templates select="."/>
					</xsl:for-each>
					<xsl:if test="ms:resourceComponentType/ms:corpusInfo">
						<xsl:apply-templates select="//ms:corpusInfo"/>
					</xsl:if>
					<xsl:if test="ms:resourceComponentType/ms:toolServiceInfo">
						<xsl:apply-templates select="//ms:toolServiceInfo"/>
					</xsl:if>
					<xsl:if test="ms:resourceComponentType/ms:languageDescriptionInfo">
						<xsl:apply-templates select="//ms:languageDescriptionInfo"/>
					</xsl:if>
					<xsl:if test="ms:resourceComponentType/ms:lexicalConceptualResourceInfo">
						<xsl:apply-templates select="//ms:lexicalConceptualResourceInfo"/>
					</xsl:if>
				</resourceInfo>
			</Components>
		</CMD>
	</xsl:template>
</xsl:stylesheet>
