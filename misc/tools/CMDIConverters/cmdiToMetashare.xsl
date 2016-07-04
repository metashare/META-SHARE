<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns="http://www.ilsp.gr/META-XMLSchema" xmlns:cmd="http://www.clarin.eu/cmd/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xalan="http://xml.apache.org/xslt" exclude-result-prefixes="cmd xalan">
	<xsl:output method="xml" version="1.0" encoding="UTF-8" indent="yes" xalan:indent-amount="4"/>
	<xsl:strip-space elements="*"/>
	<xsl:template match="/">
		<xsl:apply-templates select="//cmd:resourceInfo"/>
	</xsl:template>
	<xsl:template match="*">
    	<xsl:element name="{local-name(.)}">
    		<xsl:apply-templates select="@* | node()"/>
    	</xsl:element>
    </xsl:template>
    <xsl:template match ="@*" >
			<xsl:if test="local-name() = 'lang'">
				<xsl:attribute name ="{local-name()}">
					<xsl:value-of select ="." />
				</xsl:attribute>
			</xsl:if>
		</xsl:template>
	<xsl:template name="personInfo">
		<personInfo>
			<xsl:apply-templates select="cmd:personInfo"/>
		</personInfo>
	</xsl:template>
	<xsl:template match="cmd:personInfo">
		<xsl:apply-templates select="cmd:surname[not(@lang=(preceding-sibling::cmd:surname/@lang))]"/>
		<xsl:apply-templates select="cmd:givenName[not(@lang=(preceding-sibling::cmd:givenName/@lang))]"/>
		<xsl:apply-templates select="cmd:sex"/>
		<xsl:apply-templates select="cmd:communicationInfo"/>
		<xsl:apply-templates select="cmd:position"/>
		<xsl:for-each select="cmd:affiliation">
			<affiliation>
				<xsl:apply-templates select="cmd:organizationInfo"/>
			</affiliation>
		</xsl:for-each>
	</xsl:template>
	
	<xsl:template name="organizationInfo">
		<organizationInfo>
			<xsl:apply-templates select="cmd:organizationInfo"/>
		</organizationInfo>
	</xsl:template>
	<xsl:template match="cmd:organizationInfo">
		<xsl:apply-templates select="cmd:organizationName[not(@lang=(preceding-sibling::cmd:organizationName/@lang))]"/>
		<xsl:apply-templates select="cmd:organizationShortName[not(@lang=(preceding-sibling::cmd:organizationShortName/@lang))]"/>
		<xsl:apply-templates select="cmd:departmentName[not(@lang=(preceding-sibling::cmd:departmentName/@lang))]"/>
		<xsl:apply-templates select="cmd:communicationInfo"/>
	</xsl:template>
	<xsl:template name="projectInfo">
		<xsl:for-each select="cmd:projectInfo/child::*">
			<xsl:choose>
				<xsl:when test="self::cmd:projectName">
					<xsl:apply-templates select="self::cmd:projectName[not(@lang=(preceding-sibling::cmd:projectName/@lang))]"/>
				</xsl:when>
				<xsl:when test="self::cmd:projectShortName">
					<xsl:apply-templates select="self::cmd:projectShortName[not(@lang=(preceding-sibling::cmd:projectShortName/@lang))]"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:apply-templates select="."/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:for-each>
	</xsl:template>
	<xsl:template name="info">
		<xsl:for-each select="child::*[not(self::cmd:role)]">
			<xsl:choose>
				<xsl:when test="self::cmd:sizeInfo">
					<xsl:call-template name="info"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:element name="{local-name()}">
						 <xsl:copy-of select="@lang"/>
						<xsl:if test="count(child::*)=0">
							<xsl:value-of select="."/>
						</xsl:if>
						<xsl:call-template name="info"/>
					</xsl:element>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:for-each>
	</xsl:template>
	<xsl:template name="documentInfo">
		<xsl:choose>
			<xsl:when test="cmd:documentInfo or child::*/cmd:documentInfo">
				<documentInfo>
					<xsl:apply-templates select="cmd:documentInfo/child::*[not(self::cmd:title[@lang=(preceding-sibling::cmd:title/@lang)])]"/>
					<xsl:apply-templates select="child::*/cmd:documentInfo/child::*[not(self::cmd:title[@lang=(preceding-sibling::cmd:title/@lang)])]"/>					
				</documentInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:apply-templates select="cmd:documentUnstructured"/>
				<xsl:apply-templates select=" child::*/cmd:documentUnstructured"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>

	<xsl:template match="cmd:identificationInfo">
		<xsl:element name="{local-name()}">
			<xsl:apply-templates select="cmd:resourceName[not(@lang=(preceding-sibling::cmd:resourceName/@lang))]"/>
			<xsl:apply-templates select="cmd:description[not(@lang=(preceding-sibling::cmd:description/@lang))]"/>
			<xsl:apply-templates select="cmd:resourceShortName[not(@lang=(preceding-sibling::cmd:resourceShortName/@lang))]"/>
			<xsl:apply-templates select="child::*[self::cmd:url or self::cmd:metaShareId or self::cmd:identifier]"/>
		</xsl:element>
	</xsl:template>
	<xsl:template match="cmd:licenceInfo">
		<xsl:element name="{local-name()}">
			<xsl:for-each select="child::*[not(self::cmd:userNature or self::cmd:licensorPerson or self::cmd:licensorOrganization or self::cmd:distributionRightsHolderPerson or self::cmd:distributionRightsHolderOrganization or self::cmd:membershipInfo)] ">
				<xsl:choose>
					<xsl:when test="self::cmd:attributionText">
						<xsl:apply-templates select="self::cmd:attributionText[not(@lang=(preceding-sibling::cmd:attributionText/@lang))]"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each>
			<xsl:for-each select="cmd:licensorPerson">
				<licensor>
					<xsl:call-template name="personInfo"/>
				</licensor>
			</xsl:for-each>
			<xsl:for-each select="cmd:licensorOrganization">
				<licensor>
					<xsl:call-template name="organizationInfo"/>
				</licensor>
			</xsl:for-each>
				<xsl:for-each select="cmd:distributionRightsHolderPerson">
					<distributionRightsHolder>
						<xsl:call-template name="personInfo"/>
					</distributionRightsHolder>
				</xsl:for-each>
				<xsl:for-each select="cmd:distributionRightsHolderOrganization">
					<distributionRightsHolder>
						<xsl:call-template name="organizationInfo"/>
					</distributionRightsHolder>
				</xsl:for-each>
				<xsl:apply-templates select="cmd:userNature"/>
				<xsl:apply-templates select="cmd:membershipInfo"/>
		</xsl:element>
	</xsl:template>
	<xsl:template match="cmd:distributionInfo">
		<xsl:element name="{local-name()}">
			<xsl:apply-templates select="cmd:availability"/>
			<xsl:apply-templates select="cmd:licenceInfo"/>
			<xsl:for-each select="cmd:iprHolderPerson">
				<iprHolder>
					<xsl:call-template name="personInfo"/>
				</iprHolder>
			</xsl:for-each>
			<xsl:for-each select="cmd:iprHolderOrganization">
				<iprHolder>
					<xsl:call-template name="organizationInfo"/>
				</iprHolder>
			</xsl:for-each>
			<xsl:apply-templates select="cmd:availabilityEndDate"/>
			<xsl:apply-templates select="cmd:availabilityStartDate"/>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="cmd:metadataInfo">
		<xsl:element name="{local-name()}">
			<xsl:apply-templates select="cmd:metadataCreationDate"/>
			<xsl:for-each select="cmd:metadataCreator">
				<metadataCreator>
					<xsl:apply-templates select="cmd:personInfo"/>
				</metadataCreator>
			</xsl:for-each>
			<xsl:for-each select="child::*[not(self::cmd:metadataCreationDate or self::cmd:metadataCreator)]">
				<xsl:apply-templates select="."/>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="cmd:validationInfo">
		<xsl:element name="{local-name()}">
			<xsl:for-each select="child::*[not(self::cmd:sizePerValidation or self::cmd:validationReportStructured or self::cmd:validationReportUnstructured or self::cmd:validationTool or self::cmd:validatorPerson or self::cmd:validatorOrganization)]">
				<xsl:apply-templates select="."/>
			</xsl:for-each>
			<xsl:if test="cmd:sizePerValidation">
				<sizePerValidation>
					<xsl:apply-templates select="cmd:sizePerValidation/child::cmd:sizeInfo/child::*"/>
				</sizePerValidation>
			</xsl:if>
			<xsl:for-each select="child::*[self::cmd:validationReportStructured or self::cmd:validationReportUnstructured]">
				<validationReport>
					<xsl:call-template name="documentInfo"/>
				</validationReport>
			</xsl:for-each>
			<xsl:apply-templates select="cmd:validationTool"/>
			<xsl:for-each select="cmd:validatorPerson">
				<validator>
					<xsl:call-template name="personInfo"/>
				</validator>
			</xsl:for-each>
			<xsl:for-each select="cmd:validatorOrganization">
				<validator>
					<xsl:call-template name="organizationInfo"/>
				</validator>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="cmd:usageInfo">
		<xsl:element name="{local-name()}">
			<xsl:for-each select="child::*[not(self::cmd:actualUseInfo)]">
				<xsl:apply-templates select="."/>
			</xsl:for-each>
			<xsl:for-each select="cmd:actualUseInfo">
				<actualUseInfo>
					<xsl:for-each select="child::*[self::cmd:actualUse or self::cmd:useNLPSpecific]">
						<xsl:apply-templates select="."/>
					</xsl:for-each>
					<xsl:for-each select="child::*[self::cmd:usageReportStructured or self::cmd:usageReportUnstructured]">
						<usageReport>
							<xsl:call-template name="documentInfo"/>
						</usageReport>
					</xsl:for-each>
					<xsl:apply-templates select="child::cmd:derivedResource"/>
					<xsl:for-each select="cmd:usageProject">
						<usageProject>
							<xsl:call-template name="projectInfo"/>
						</usageProject>
					</xsl:for-each>
					<xsl:apply-templates select="child::cmd:actualUseDetails"/>
				</actualUseInfo>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="cmd:resourceDocumentationInfo">
		<xsl:element name="{local-name()}">
			<xsl:for-each select="child::*[self::cmd:documentationStructured or self::cmd:documentationUnstructured]">
				<documentation>
					<xsl:call-template name="documentInfo"/>
				</documentation>
			</xsl:for-each>
			<xsl:apply-templates select="cmd:samplesLocation"/>
			<xsl:apply-templates select="cmd:toolDocumentationType"/>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="cmd:resourceCreationInfo">
		<xsl:element name="{local-name()}">
			<xsl:for-each select="cmd:resourceCreatorPerson">
				<resourceCreator>
					<xsl:call-template name="personInfo"/>
				</resourceCreator>
			</xsl:for-each>
			<xsl:for-each select="cmd:resourceCreatorOrganization">
				<resourceCreator>
					<xsl:call-template name="organizationInfo"/>
				</resourceCreator>
			</xsl:for-each>
			<xsl:for-each select="cmd:fundingProject">
				<fundingProject>
					<xsl:call-template name="projectInfo"/>
				</fundingProject>
			</xsl:for-each>
			<xsl:apply-templates select="cmd:creationStartDate"/>
			<xsl:apply-templates select="cmd:creationEndDate"/>
		</xsl:element>
	</xsl:template>
	<xsl:template match="cmd:annotationInfo">
		<xsl:element name="{local-name()}">
				<xsl:for-each select="child::*[self::cmd:annotationType or self::cmd:annotatedElements or self::cmd:annotationStandoff or self::cmd:segmentationLevel or self::cmd:annotationFormat or self::cmd:tagset or self::cmd:tagsetLanguageId or self::cmd:tagsetLanguageName or self::cmd:conformanceToStandardsBestPractices or self::cmd:theoreticModel]">
					<xsl:apply-templates select="."/>
				</xsl:for-each>
				<xsl:for-each select="child::*[self::cmd:annotationManualStructured or self::cmd:annotationManualUnstructured]">
					<annotationManual>
						<xsl:call-template name="documentInfo"/>
					</annotationManual>
				</xsl:for-each>
				<xsl:for-each select="child::*[self::cmd:annotationMode or self::cmd:annotationModeDetails or self::cmd:annotationTool]">
					<xsl:apply-templates select="."/>
				</xsl:for-each>
				<xsl:apply-templates select="cmd:annotationStartDate"/>
				<xsl:apply-templates select="cmd:annotationEndDate"/>
				<xsl:if test="cmd:sizePerAnnotation">
					<sizePerAnnotation>
						<xsl:apply-templates select="cmd:sizePerAnnotation/cmd:sizeInfo/child::*[self::cmd:size or self::cmd:sizeUnit]"/>
					</sizePerAnnotation>
				</xsl:if>
				<xsl:for-each select="child::*[self::cmd:interannotatorAgreement or self::cmd:intraannotatorAgreement]">
					<xsl:apply-templates select="."/>
				</xsl:for-each>
				<xsl:for-each select="cmd:annotatorPerson">
					<annotator>
						<xsl:call-template name="personInfo"/>
					</annotator>
				</xsl:for-each>
				<xsl:for-each select="cmd:annotatorOrganization">
					<annotator>
						<xsl:call-template name="organizationInfo"/>
					</annotator>
				</xsl:for-each>
			</xsl:element>
	</xsl:template>
		<xsl:template match="cmd:domainInfo">
		<xsl:element name="{local-name()}">
			<xsl:apply-templates select="cmd:domain"/>
			<xsl:if test="cmd:sizePerDomain">
				<sizePerDomain>
					<xsl:apply-templates select="cmd:sizePerDomain/cmd:sizeInfo/child::*"/>
				</sizePerDomain>
			</xsl:if>
			<xsl:apply-templates select="cmd:conformanceToClassificationScheme"/>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="cmd:creationInfo">
		<xsl:element name="{local-name()}">
			<xsl:apply-templates select="cmd:originalSource"/>
			<xsl:apply-templates select="cmd:creationMode"/>
			<xsl:apply-templates select="cmd:creationModeDetails"/>
			<xsl:apply-templates select="cmd:creationTool"/>
		</xsl:element>
	</xsl:template>
	<xsl:template match="cmd:participantInfo">
		<xsl:element name="{local-name()}">
			<xsl:for-each select="child::*">
				<xsl:choose>
					<xsl:when test="self::cmd:alias">
						<xsl:apply-templates select="self::cmd:alias[not(@lang=(preceding-sibling::cmd:alias/@lang))]"/>
					</xsl:when>
					<xsl:when test="self::cmd:dialectAccent">
						<xsl:apply-templates select="self::cmd:dialectAccent[not(@lang=(preceding-sibling::cmd:dialectAccent/@lang))]"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
	<xsl:template match="cmd:personSourceSetInfo">
		<xsl:element name="{local-name()}">
			<xsl:for-each select="child::*">
				<xsl:choose>
					<xsl:when test="self::cmd:participantInfo">
						<xsl:apply-templates select="."/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>

	<xsl:template match="cmd:runningEnvironmentInfo">
		<xsl:element name="{local-name()}">
			<xsl:apply-templates select="cmd:requiredSoftware"/>
			<xsl:apply-templates select="cmd:requiredHardware"/>
			<xsl:apply-templates select="cmd:requiredLRs"/>
			<xsl:apply-templates select="cmd:runningEnvironmentDetails"/>
		</xsl:element>
	</xsl:template>
	<xsl:template match="cmd:recordingInfo">
		<xsl:element name="{local-name()}">
			<xsl:for-each select="child::*">
				<xsl:choose>
					<xsl:when test="self::cmd:recorderPerson or self::cmd:recorderOrganization">
						<recorder>
							<xsl:choose>
								<xsl:when test="self::cmd:recorderPerson">
									<xsl:call-template name="personInfo"/>
								</xsl:when>
								<xsl:otherwise>
									<xsl:call-template name="organizationInfo"/>
								</xsl:otherwise>
							</xsl:choose>
						</recorder>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="cmd:audioContentInfo">
		<xsl:element name="audioContentInfo">
			<xsl:for-each select="child::*">
				<xsl:choose>
					<xsl:when test="self::cmd:nonSpeechItems and contains(string(.), 'commercial')">
						<xsl:element name="nonSpeechItems">
							<xsl:text>commercial </xsl:text>
						</xsl:element>
					</xsl:when>
					<xsl:otherwise>
						<xsl:apply-templates select="."/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="cmd:audioFormatInfo">
		<xsl:element name="{local-name()}">
			<xsl:apply-templates select="cmd:mimeType"/>
			<xsl:apply-templates select="cmd:signalEncoding"/>
			<xsl:apply-templates select="cmd:samplingRate"/>
			<xsl:apply-templates select="cmd:quantization"/>
			<xsl:apply-templates select="cmd:byteOrder"/>
			<xsl:apply-templates select="cmd:signConvention"/>
			<xsl:apply-templates select="cmd:compressionInfo"/>
			<xsl:apply-templates select="cmd:audioQualityMeasuresIncluded"/>
			<xsl:apply-templates select="cmd:numberOfTracks"/>
			<xsl:apply-templates select="cmd:recordingQuality"/>
			<xsl:if test="cmd:sizePerAudioFormat">
				<sizePerAudioFormat>
					<xsl:apply-templates select="cmd:sizePerAudioFormat/cmd:sizeInfo/child::*"/>
				</sizePerAudioFormat>
			</xsl:if>		
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="cmd:videoFormatInfo">
		<xsl:element name="{local-name()}">
			<xsl:apply-templates select="cmd:mimeType"/>
			<xsl:apply-templates select="cmd:colourSpace"/>
			<xsl:apply-templates select="cmd:colourDepth"/>
			<xsl:apply-templates select="cmd:frameRate"/>
			<xsl:apply-templates select="cmd:resolutionInfo"/>
			<xsl:apply-templates select="cmd:visualModelling"/>
			<xsl:apply-templates select="cmd:fidelity"/>
			<xsl:apply-templates select="cmd:compressionInfo"/>
			<xsl:if test="cmd:sizePerVideoFormat">
				<sizePerVideoFormat>
					<xsl:apply-templates select="cmd:sizePerVideoFormat/cmd:sizeInfo/child::*"/>
				</sizePerVideoFormat>
			</xsl:if>		
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="cmd:imageFormatInfo">
		<xsl:element name="{local-name()}">
			<xsl:apply-templates select="cmd:mimeType"/>
			<xsl:apply-templates select="cmd:colourSpace"/>
			<xsl:apply-templates select="cmd:colourDepth"/>
			<xsl:apply-templates select="cmd:compressionInfo"/>
			<xsl:apply-templates select="cmd:resolutionInfo"/>
			<xsl:apply-templates select="cmd:visualModelling"/>
			<xsl:apply-templates select="cmd:rasterOrVectorGraphics"/>
			<xsl:apply-templates select="cmd:quality"/>
			<xsl:if test="cmd:sizePerImageFormat">
				<sizePerImageFormat>
					<xsl:apply-templates select="cmd:sizePerImageFormat/cmd:sizeInfo/child::*"/>
				</sizePerImageFormat>
			</xsl:if>		
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="cmd:corpusInfo">
		<xsl:element name="{local-name()}">
			<xsl:apply-templates select="cmd:resourceType"/>
				<corpusMediaType>
					<xsl:for-each select="cmd:corpusMediaType/child::*">
						<xsl:element name="{local-name()}">
							<xsl:apply-templates select="cmd:mediaType"/>
							<xsl:for-each select="child::*[not(self::cmd:mediaType)]">
								<xsl:choose>
									<xsl:when test="self::cmd:annotationInfo">
										<xsl:apply-templates select="."/>
									</xsl:when>
									<xsl:when test="self::cmd:creationInfo">
										<xsl:apply-templates select="."/>
									</xsl:when>
									<xsl:when test="self::cmd:captureInfo">
										<xsl:apply-templates select="."/>
									</xsl:when>
									<xsl:when test="self::cmd:sizeInfo">
										<xsl:apply-templates select="."/>
									</xsl:when>
									<xsl:when test="self::cmd:domainInfo">
										<xsl:apply-templates select="."/>
									</xsl:when>
									<xsl:when test="self::cmd:recordingInfo">
										<xsl:apply-templates select="."/>
									</xsl:when>
									<xsl:when test="self::cmd:audioSizeInfo">
										<xsl:apply-templates select="."/>
									</xsl:when>
									<xsl:when test="self::cmd:audioContentInfo">
										<xsl:apply-templates select="."/>
									</xsl:when>
									<xsl:when test="self::cmd:audioFormatInfo">
										<xsl:apply-templates select="."/>
									</xsl:when>
									<xsl:when test="self::cmd:videoFormatInfo">
										<xsl:apply-templates select="."/>
									</xsl:when>
									<xsl:when test="self::cmd:imageFormatInfo">
										<xsl:apply-templates select="."/>
									</xsl:when>
									<xsl:otherwise>
										<xsl:element name="{local-name()}">
											<xsl:call-template name="info"/>
										</xsl:element>
									</xsl:otherwise>
								</xsl:choose>
							</xsl:for-each>
						</xsl:element>
					</xsl:for-each>
				</corpusMediaType>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="cmd:toolServiceOperationInfo">
		<xsl:element name="{local-name()}">
			<xsl:apply-templates select="cmd:operatingSystem"/>
			<xsl:apply-templates select="cmd:runningEnvironmentInfo"/>
			<xsl:apply-templates select="cmd:runningTime"/>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="cmd:toolServiceEvaluationInfo">
		<xsl:element name="{local-name()}">
			<xsl:apply-templates select="cmd:evaluated"/>
			<xsl:apply-templates select="cmd:evaluationLevel"/>
			<xsl:apply-templates select="cmd:evaluationType"/>
			<xsl:apply-templates select="cmd:evaluationCriteria"/>
			<xsl:apply-templates select="cmd:evaluationMeasure"/>
			<xsl:for-each select="child::*[self::cmd:evaluationReportStructured or self::cmd:evaluationReportUnstructured]">
				<evaluationReport>
					<xsl:call-template name="documentInfo"/>
				</evaluationReport>
			</xsl:for-each>
			<xsl:apply-templates select="cmd:evaluationTool"/>
			<xsl:apply-templates select="cmd:evaluationDetails"/>
			<xsl:for-each select="cmd:evaluatorPerson">
				<evaluator>
					<xsl:call-template name="personInfo"/>
				</evaluator>
			</xsl:for-each>
			<xsl:for-each select="cmd:evaluatorOrganization">
				<evaluator>
					<xsl:call-template name="organizationInfo"/>
				</evaluator>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="cmd:toolServiceCreationInfo">
		<xsl:element name="{local-name()}">
			<xsl:apply-templates select="cmd:implementationLanguage"/>
			<xsl:apply-templates select="cmd:formalism"/>
			<xsl:apply-templates select="cmd:originalSource"/>
			<xsl:apply-templates select="cmd:creationDetails"/>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="cmd:toolServiceInfo">
		<xsl:element name="{local-name()}">
			<xsl:apply-templates select="cmd:resourceType"/>
			<xsl:apply-templates select="cmd:toolServiceType"/>
			<xsl:apply-templates select="cmd:toolServiceSubtype"/>
			<xsl:apply-templates select="cmd:languageDependent"/>
			<xsl:apply-templates select="cmd:inputInfo"/>
			<xsl:apply-templates select="cmd:outputInfo"/>
			<xsl:apply-templates select="cmd:toolServiceOperationInfo"/>
			<xsl:apply-templates select="cmd:toolServiceEvaluationInfo"/>
			<xsl:apply-templates select="cmd:toolServiceCreationInfo"/>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="cmd:languageDescriptionOperationInfo">
		<xsl:element name="{local-name()}">
			<xsl:apply-templates select="cmd:runningEnvironmentInfo"/>
			<xsl:apply-templates select="cmd:relatedLexiconInfo"/>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="cmd:languageDescriptionMediaType">
		<xsl:element name="{local-name()}">
			<xsl:for-each select="child::*">
				<xsl:element name="{local-name()}">
					<xsl:for-each select="child::*">
						<xsl:choose>
							<xsl:when test="self::cmd:mediaType or self::cmd:creationInfo or self::cmd:domainInfo or self::cmd:videoFormatInfo or self::cmd:imageFormatInfo">
								<xsl:apply-templates select="."/>
							</xsl:when>
							<xsl:otherwise>
								<xsl:element name="{local-name()}">
									<xsl:call-template name="info"/>
								</xsl:element>
							</xsl:otherwise>
						</xsl:choose>
					</xsl:for-each>
				</xsl:element>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="cmd:languageDescriptionInfo">
		<xsl:element name="{local-name()}">
			<xsl:apply-templates select="cmd:resourceType"/>
			<xsl:apply-templates select="cmd:languageDescriptionType"/>
			<xsl:apply-templates select="cmd:languageDescriptionEncodingInfo"/>
			<xsl:apply-templates select="cmd:languageDescriptionOperationInfo"/>
			<xsl:apply-templates select="cmd:languageDescriptionPerformanceInfo"/>
			<xsl:apply-templates select="cmd:creationInfo"/>
			<xsl:apply-templates select="cmd:languageDescriptionMediaType"/>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="cmd:lexicalConceptualResourceMediaType">
		<xsl:element name="{local-name()}">
			<xsl:for-each select="child::*">
				<xsl:element name="{local-name()}">
					<xsl:for-each select="child::*">
						<xsl:choose>
							<xsl:when test="self::cmd:mediaType">
								<xsl:apply-templates select="self::cmd:mediaType"/>
							</xsl:when>
							<xsl:when test="self::cmd:creationInfo">
								<xsl:apply-templates select="."/>
							</xsl:when>
							<xsl:when test="self::cmd:domainInfo">
								<xsl:apply-templates select="."/>
							</xsl:when>
							<xsl:when test="self::cmd:audioSizeInfo">
								<xsl:apply-templates select="."/>
							</xsl:when>
							<xsl:when test="self::cmd:audioContentInfo">
								<xsl:apply-templates select="."/>
							</xsl:when>
							<xsl:when test="self::cmd:audioFormatInfo">
								<xsl:apply-templates select="."/>
							</xsl:when>
							<xsl:when test="self::cmd:videoFormatInfo">
								<xsl:apply-templates select="."/>
							</xsl:when>
							<xsl:when test="self::cmd:imageFormatInfo">
								<xsl:apply-templates select="."/>
							</xsl:when>
							<xsl:otherwise>
								<xsl:element name="{local-name()}">
									<xsl:call-template name="info"/>
								</xsl:element>
							</xsl:otherwise>
						</xsl:choose>
					</xsl:for-each>
				</xsl:element>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="cmd:lexicalConceptualResourceInfo">
		<xsl:element name="{local-name()}">
			<xsl:apply-templates select="cmd:resourceType"/>
			<xsl:apply-templates select="cmd:lexicalConceptualResourceType"/>
			<xsl:apply-templates select="cmd:lexicalConceptualResourceEncodingInfo"/>
			<xsl:apply-templates select="cmd:creationInfo"/>
			<xsl:apply-templates select="cmd:lexicalConceptualResourceMediaType"/>
		</xsl:element>
	</xsl:template>
	
	<xsl:template match="cmd:resourceInfo" name="resourceInfo">
		<xsl:text>
</xsl:text>
		<resourceInfo>
			<xsl:attribute name="xsi:schemaLocation">http://www.ilsp.gr/META-XMLSchema http://metashare.ilsp.gr/META-XMLSchema/v3.0/META-SHARE-Resource.xsd</xsl:attribute>
			<xsl:apply-templates select="cmd:identificationInfo"/>
			<xsl:apply-templates select="cmd:distributionInfo"/>
			<xsl:for-each select="cmd:contactPerson">
				<contactPerson>
					<xsl:apply-templates select="cmd:personInfo"/>
				</contactPerson>
			</xsl:for-each>
			<xsl:apply-templates select="cmd:metadataInfo"/>
			<xsl:apply-templates select="cmd:versionInfo"/>
			<xsl:apply-templates select="cmd:validationInfo"/>
			<xsl:apply-templates select="cmd:usageInfo"/>
			<xsl:apply-templates select="cmd:resourceDocumentationInfo"/>
			<xsl:apply-templates select="cmd:resourceCreationInfo"/>
			<xsl:apply-templates select="cmd:relationInfo"/>
			<resourceComponentType>
				<xsl:apply-templates select="cmd:corpusInfo"/>
				<xsl:apply-templates select="cmd:toolServiceInfo"/>
				<xsl:apply-templates select="cmd:languageDescriptionInfo"/>
				<xsl:apply-templates select="cmd:lexicalConceptualResourceInfo"/>
			</resourceComponentType>
		</resourceInfo>
	</xsl:template>
</xsl:stylesheet>
