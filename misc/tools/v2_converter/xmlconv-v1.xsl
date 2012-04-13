<xsl:stylesheet version="2.0" 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns="http://www.ilsp.gr/META-XMLSchema"
    exclude-result-prefixes="#default"
    xpath-default-namespace="http://www.ilsp.gr/META-XMLSchema"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 

>
<xsl:output indent="yes" />

	<xsl:template match="@*|node()">
	  <xsl:copy copy-namespaces="no">
		<xsl:apply-templates select="@*|node()"/>
	  </xsl:copy>
	</xsl:template><!--copy all -->

	<xsl:template match="Resource"><!--#1 --><!--#160-->
		<resourceInfo  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.ilsp.gr/META-XMLSchema META-SHARE-Resource.xsd">
			<xsl:apply-templates select="IdentificationInfo"/>
			<xsl:apply-templates select="DistributionInfo"/>
			<xsl:apply-templates select="contactPerson"/>
			<xsl:apply-templates select="MetadataInfo"/>
			<xsl:apply-templates select="VersionInfo"/>
			<xsl:apply-templates select="ValidationInfo"/>
			<xsl:apply-templates select="UsageInfo"/>
			<xsl:apply-templates select="ResourceDocumentationInfo"/>
			<xsl:apply-templates select="ResourceCreationInfo"/>
			<xsl:apply-templates select="ContentInfo"/>	
			<!--<xsl:apply-templates select="@*|node()[not(self::contactPerson or self::TextInfo or self::LexicalConceptualResourceInfo or self::AudioInfo) ]"/>-->
		</resourceInfo>
	</xsl:template><!--#1 -->

	<xsl:template match="Resource/IdentificationInfo"><!--#2 -->
		<identificationInfo>
			<xsl:apply-templates select="resourceName"/>
			<xsl:apply-templates select="../ContentInfo/description"/>
			<xsl:apply-templates select="resourceShortName"/>
			<xsl:apply-templates select="url"/>
			<metaShareId>
				NOT_DEFINED_FOR_V2
	  		</metaShareId>
			<xsl:apply-templates select="identifier"/>
		</identificationInfo>
	</xsl:template><!--#2 -->

	<xsl:template match="Resource/IdentificationInfo/url"><!--#3 -->
	  	<xsl:copy copy-namespaces="no">
			<xsl:apply-templates select="@*|node()"/>
	  	</xsl:copy>
		
	</xsl:template><!--#3 -->

	<xsl:template match="Resource/IdentificationInfo/pid"><!--#4 -->
	</xsl:template><!--#4 -->

	<xsl:template match="Resource/DistributionInfo"><!--#5 -->
		<distributionInfo>
			<xsl:apply-templates select="availability"/>
			<xsl:apply-templates select="LicenseInfo"/>
			<xsl:apply-templates select="iprHolder"/>
			<xsl:apply-templates select="LicenseInfo[1]/availabilityEndDate"/>
			<xsl:apply-templates select="LicenseInfo[1]/availabilityStartDate"/>
		</distributionInfo>
	</xsl:template><!--#5 -->
	
	<!--<xsl:template match="Resource/contactPerson/CommunicationInfo"	>
						<communicationInfo>
							<xsl:apply-templates select="email"/>
							<xsl:apply-templates select="url"/>
							<xsl:apply-templates select="address"/>
							<xsl:apply-templates select="zipCode"/>
							<xsl:apply-templates select="city"/>
							<xsl:apply-templates select="region"/>
							<xsl:apply-templates select="country"/>
							<xsl:apply-templates select="telephoneNumber"/>
							<xsl:apply-templates select="faxNumber"/>
						</communicationInfo>
	</xsl:template>-->
	<xsl:template match="@role">
	</xsl:template>
	<xsl:template match="@lang">
	</xsl:template>
	<xsl:template match="Resource/contactPerson"><!--#161 -->
		<contactPerson>
			<xsl:choose>
				<xsl:when test="not(surname)">
					<surname>N/A</surname>
				</xsl:when>
			</xsl:choose>	
			<xsl:apply-templates select="surname"/>
			<xsl:apply-templates select="givenName"/>
			<xsl:apply-templates select="CommunicationInfo"/>
			<xsl:apply-templates select="position"/>
			<xsl:apply-templates select="affiliation"/>

		</contactPerson>
	</xsl:template><!--#161 -->
	
	<xsl:template match="Resource/MetadataInfo/metadataCreator">
		<xsl:copy copy-namespaces="no">
		<xsl:choose>
				<xsl:when test="not(surname)">
					<surname>N/A</surname>
				</xsl:when>
			</xsl:choose>	
			<xsl:apply-templates select="surname"/>
			<xsl:apply-templates select="givenName"/>
			<xsl:apply-templates select="CommunicationInfo"/>
			<xsl:apply-templates select="position"/>
			<xsl:apply-templates select="affiliation"/>
		</xsl:copy>
	</xsl:template><!--#17 -->	

	<xsl:template match="Resource/DistributionInfo/LicenseInfo/licenseSignatory"><!--#13 -->
		<licensor>
			<xsl:apply-templates select="@*|node()"/>	
		</licensor>
	</xsl:template><!--#13 -->

	<xsl:template match="Resource/DistributionInfo/LicenseInfo/distributor"><!--#14 -->
		<distributionRightsHolder>
			<xsl:apply-templates select="@*|node()"/>	
		</distributionRightsHolder>
	</xsl:template><!--#14 -->

	<xsl:template match="Resource/MetadataInfo"><!--#16 -->
		<metadataInfo>
			<xsl:choose>
				<xsl:when test="not(metadataCreationDate)">
					<metadataCreationDate/>
				</xsl:when>
			</xsl:choose>
			<xsl:apply-templates select="metadataCreationDate"/>
			<xsl:apply-templates select="metadataCreator"/>	
			<xsl:apply-templates select="source"/>
			<xsl:apply-templates select="originalMetadataSchema[1]"/>
			<xsl:apply-templates select="originalMetadataLink"/>	
			<xsl:apply-templates select="metadataLanguageName"/>
			<xsl:apply-templates select="metadataLanguage"/>
			<xsl:apply-templates select="metadataLastDateUpdated"/>	
			<xsl:apply-templates select="revision"/>		
		</metadataInfo>
	</xsl:template><!--#16 -->
	
	<xsl:template match="Resource/MetadataInfo/metadataLanguage"><!--#186 -->
		<metadataLanguageId>
			<xsl:apply-templates select="@*|node()"/>
		</metadataLanguageId>
	</xsl:template><!--#186 -->
	
	<xsl:template match="Resource/MetadataInfo/harvestingDate"><!--#18 -->
	</xsl:template><!--#18 -->

	<xsl:template match="Resource/ValidationInfo"><!--#20 -->
		<validationInfo>
			<xsl:choose>
				<xsl:when test="not(validated)">
					<validated>true</validated>
				</xsl:when>
			</xsl:choose>
			<xsl:apply-templates select="validated"/>
			<xsl:apply-templates select="validationType"/>
			<xsl:apply-templates select="validationMode"/>
			<xsl:apply-templates select="validationModeDetails"/>
			<xsl:apply-templates select="validationExtent"/>
			<xsl:apply-templates select="validationExtentDetails"/> 
			<xsl:apply-templates select="sizePerValidation"/> 
			<xsl:apply-templates select="validationReport"/>
			<xsl:apply-templates select="validationTool"/>	
			<xsl:apply-templates select="validator"/>               
		</validationInfo><!--#166 -->
	
	</xsl:template><!--#20 -->

	<xsl:template match="Resource/ValidationInfo/validationReport"><!--#22 -->
		<validationReport>
			<documentUnstructured>
				<xsl:apply-templates select="@*|node()"/>
			</documentUnstructured>	
		</validationReport>
	</xsl:template><!--#22 -->

	<xsl:template match="Resource/ValidationInfo/validationTool"><!--#23 -->
		<validationTool>
			<targetResourceNameURI>
				<xsl:apply-templates select="@*|node()"/>
			</targetResourceNameURI>	
		</validationTool>
	</xsl:template><!--#23 -->

	<xsl:template match="Resource/UsageInfo"><!--#24 -->
		<usageInfo>
			<xsl:apply-templates select="@*|node()"/>	
		</usageInfo>
	</xsl:template><!--#24 -->

	<xsl:template match="Resource/UsageInfo/accessTool"><!--#25 -->
		<accessTool>
			<targetResourceNameURI>
				<xsl:apply-templates select="@*|node()"/>
			</targetResourceNameURI>	
		</accessTool>
	</xsl:template><!--#25 -->

	<xsl:template match="Resource/UsageInfo/toolAssociatedWith"><!--#26 -->
		<resourceAssociatedWith>
			<targetResourceNameURI>
				<xsl:apply-templates select="@*|node()"/>
			</targetResourceNameURI>	
		</resourceAssociatedWith>
	</xsl:template><!--#26 -->

	<xsl:template match="Resource/UsageInfo/ForeseenUseInfo"><!--#27 -->
		
			<xsl:choose>
				<xsl:when test="count(foreseenUse)=2">
					<foreseenUseInfo>
						<foreseenUse>humanUse</foreseenUse>
					</foreseenUseInfo>
					<foreseenUseInfo>
						<foreseenUse>nlpApplications</foreseenUse>
						<xsl:apply-templates select="@*|node()[not(self::foreseenUse)]"/>
					</foreseenUseInfo>
				</xsl:when>
				<xsl:otherwise>
					<foreseenUseInfo>
						<xsl:apply-templates select="@*|node()"/>
					</foreseenUseInfo>
				</xsl:otherwise>
			</xsl:choose>
		
	</xsl:template><!--#27 -->

	<xsl:template match="Resource/UsageInfo/ActualUseInfo"><!--#29 -->
		
		<xsl:choose>
				<xsl:when test="count(actualUse)=2">
					<actualUseInfo>
						<xsl:apply-templates select="foreseenUse[1]"/>
					</actualUseInfo>	
					<actualUseInfo>	
						<xsl:apply-templates select="actualUse[2]"/>	
						<xsl:apply-templates select="useNLPSpecific"/>	
						<xsl:apply-templates select="publication"/>	
						<xsl:apply-templates select="outcome"/>	
						<xsl:apply-templates select="usageProject"/>	
						<xsl:apply-templates select="actualUseDetails"/>	
					</actualUseInfo>	
				</xsl:when>
				<xsl:otherwise>
					<actualUseInfo>
						<xsl:apply-templates select="actualUse"/>	
						<xsl:apply-templates select="useNLPSpecific"/>	
						<xsl:apply-templates select="publication"/>	
						<xsl:apply-templates select="outcome"/>	
						<xsl:apply-templates select="usageProject"/>	
						<xsl:apply-templates select="actualUseDetails"/>	
					</actualUseInfo>
				</xsl:otherwise>
			</xsl:choose>
	</xsl:template><!--#29 -->
	
	<xsl:template match="Resource/UsageInfo/ActualUseInfo/usageProject">
		<usageProject>
			<xsl:apply-templates select="projectName"/>
			<xsl:apply-templates select="projectShortName"/>
			<xsl:apply-templates select="projectID"/>
			<xsl:apply-templates select="url"/>
			<xsl:apply-templates select="fundingType"/>
			<xsl:apply-templates select="funder"/>
			<xsl:apply-templates select="fundingCountry"/>
			<xsl:apply-templates select="projectStartDate"/>
			<xsl:apply-templates select="projectEndDate"/>
		</usageProject>
	</xsl:template>
	

	<xsl:template match="Resource/UsageInfo/ActualUseInfo/publication"><!--#31 -->
		<usageReport>
			<documentUnstructured>
				<xsl:apply-templates select="@*|node()"/>
			</documentUnstructured>	
		</usageReport>
	</xsl:template><!--#31 -->

	<xsl:template match="Resource/UsageInfo/ActualUseInfo/outcome"><!--#32 -->
		<derivedResource>
			<targetResourceNameURI>
				<xsl:apply-templates select="@*|node()"/>
			</targetResourceNameURI>	
		</derivedResource>
	</xsl:template><!--#32 -->

	<xsl:template match="Resource/ResourceDocumentationInfo"><!--#33 -->
		<resourceDocumentationInfo>
			<xsl:apply-templates select="publication"/>	
			<xsl:apply-templates select="samplesLocation"/>	
			<xsl:apply-templates select="toolDocumentationType"/>	
		</resourceDocumentationInfo>
	</xsl:template><!--#33 -->

	<xsl:template match="Resource/ResourceDocumentationInfo/publication"><!--#34 -->
		<documentation>
			<documentUnstructured>
				<xsl:apply-templates select="@*|node()"/>
			</documentUnstructured>	
		</documentation>
	</xsl:template><!--#34 -->

	<xsl:template match="Resource/ResourceCreationInfo"><!--#35 -->
		<resourceCreationInfo>
			<xsl:apply-templates select="resourceCreator"/>	
			<xsl:apply-templates select="FundingInfo/ProjectInfo"/>	
			<xsl:apply-templates select="creationStartDate"/>	
			<xsl:apply-templates select="creationEndDate"/>	
		</resourceCreationInfo>
	</xsl:template><!--#35 -->

	<xsl:template match="Resource/LexicalConceptualResourceInfo"><!--#121 -->
			<lexicalConceptualResourceInfo>
				<resourceType>lexicalConceptualResource</resourceType>
				<xsl:apply-templates select="lexicalConceptualResourceType"/>	
				<xsl:apply-templates select="LexicalConceptualResourceEncodingInfo[1]"/>	
				<xsl:apply-templates select="LexicalConceptualResourceCreationInfo[1]"/>		
				<lexicalConceptualResourceMediaType>
					<xsl:apply-templates select="../TextInfo[1]"/>	
				</lexicalConceptualResourceMediaType>
			</lexicalConceptualResourceInfo>	
	</xsl:template><!--#121 -->

	<xsl:template match="Resource/LexicalConceptualResourceInfo/LexicalConceptualResourceCreationInfo"><!--#122 -->
		<creationInfo>
			<xsl:apply-templates select="originalSource"/>
			<xsl:apply-templates select="creationMode"/>	
			<xsl:apply-templates select="creationModeDetails"/>	
			<xsl:apply-templates select="creationTool"/>		
		</creationInfo>
	</xsl:template><!--#122 -->

	<xsl:template match="Resource/LexicalConceptualResourceInfo/LexicalConceptualResourceCreationInfo/originalSource"><!--#123 -->
		<originalSource>
			<targetResourceNameURI>
				<xsl:apply-templates select="@*|node()"/>
			</targetResourceNameURI>	
		</originalSource>
	</xsl:template><!--#123 -->

	<xsl:template match="Resource/LexicalConceptualResourceInfo/LexicalConceptualResourceCreationInfo/creationTool"><!--#124 -->
		<creationTool>
			<targetResourceNameURI>
				<xsl:apply-templates select="@*|node()"/>
			</targetResourceNameURI>	
		</creationTool>
	</xsl:template><!--#124 -->
	
	<xsl:template match="Resource/LexicalConceptualResourceInfo/LexicalConceptualResourceEncodingInfo"><!--#125 -->
		<lexicalConceptualResourceEncodingInfo>
			<xsl:apply-templates select="encodingLevel"/>	
			<xsl:apply-templates select="linguisticInformation"/>	
			<xsl:apply-templates select="conformanceToStandardsBestPractice"/>	
			<xsl:apply-templates select="theoreticModel"/>	
			<xsl:apply-templates select="externalRef"/>	
			<xsl:apply-templates select="extratextualInformation"/>	
			<xsl:apply-templates select="extratextualInformationUnit"/>	
		</lexicalConceptualResourceEncodingInfo>
	</xsl:template><!--#125 -->

	<xsl:template match="Resource/LexicalConceptualResourceInfo/LexicalConceptualResourceEncodingInfo/conformanceToStandardsBestPractice"><!--#126 -->
		<conformanceToStandardsBestPractices>
			<xsl:apply-templates select="@*|node()"/>	
		</conformanceToStandardsBestPractices>
	</xsl:template><!--#126 -->

	<xsl:template match="Resource/ToolServiceInfo"><!--#144 went to the end-->  
		<toolServiceInfo>
			<resourceType>toolService</resourceType>
			<xsl:apply-templates select="@*|node()"/>	
		</toolServiceInfo>
	</xsl:template><!--#144 -->

	<xsl:template match="Resource/ToolServiceInfo/InputInfo"><!--#146 -->
		<inputInfo>
			<xsl:apply-templates select="mediaType[text()!='sensorimotor']"/>	
			<xsl:apply-templates select="resourceType"/>	
			<xsl:apply-templates select="modalityType"/>	
		</inputInfo>
	</xsl:template><!--#146 -->

	<xsl:template match="Resource/ToolServiceInfo/OutputInfo"><!--#147 -->
		<outputInfo>
			<xsl:apply-templates select="mediaType[text()!='sensorimotor']"/>	
			<xsl:apply-templates select="resourceType"/>	
			<xsl:apply-templates select="modalityType"/>	
		</outputInfo>
	</xsl:template><!--#147 -->

	<xsl:template match="Resource/ToolServiceInfo/ToolServiceOperationInfo"><!--#148 -->
		<toolServiceOperationInfo>
			<xsl:apply-templates select="@*|node()"/>	
		</toolServiceOperationInfo>
	</xsl:template><!--#148 -->

	<xsl:template match="Resource/ToolServiceInfo/ToolServiceOperationInfo/RunningEnvironmentInfo"><!--#149 -->
		<runningEnvironmentInfo>
			<xsl:apply-templates select="@*|node()"/>	
		</runningEnvironmentInfo>
	</xsl:template><!--#149 -->

	<xsl:template match="Resource/ToolServiceInfo/ToolServiceOperationInfo/RunningEnvironmentInfo/requiredLRs"><!--#150 -->
		<requiredLRs>
			<targetResourceNameURI>
				<xsl:apply-templates select="@*|node()"/>	
			</targetResourceNameURI>
		</requiredLRs>
	</xsl:template><!--#150 -->

	<xsl:template match="Resource/ToolServiceInfo/ToolServiceEvaluationInfo"><!--#151 -->
		<toolServiceEvaluationInfo>
			<xsl:apply-templates select="@*|node()"/>	
		</toolServiceEvaluationInfo>
	</xsl:template><!--#151 -->

	<xsl:template match="Resource/ToolServiceInfo/ToolServiceEvaluationInfo/evaluationReport"><!--#153 -->
		<evaluationReport>
			<documentUnstructured>
				<xsl:apply-templates select="@*|node()"/>	
			</documentUnstructured>
		</evaluationReport>
	</xsl:template><!--#153 -->

	<xsl:template match="Resource/ToolServiceInfo/ToolServiceEvaluationInfo/evaluationTool"><!--#154 -->
		<evaluationTool>
			<targetResourceNameURI>
				<xsl:apply-templates select="@*|node()"/>	
			</targetResourceNameURI>
		</evaluationTool>
	</xsl:template><!--#154 -->

	<xsl:template match="Resource/ToolServiceInfo/ToolServiceCreationInfo"><!--#155 -->
		<toolServiceCreationInfo>
			<xsl:apply-templates select="@*|node()"/>	
		</toolServiceCreationInfo>
	</xsl:template><!--#155 -->

	<xsl:template match="//OrganizationInfo"><!--#158 -->
		<organizationInfo>
			<xsl:choose>
				<xsl:when test="not(organizationName)">
				<organizationName>N/A</organizationName>					
				</xsl:when>
			</xsl:choose>
			<xsl:apply-templates select="node()"/>
			<xsl:choose>
				<xsl:when test="not(CommunicationInfo)">
					<communicationInfo>
						<email>example@example.com</email>
					</communicationInfo>					
				</xsl:when>
			</xsl:choose>	
		</organizationInfo>
	</xsl:template><!--#158 -->

	<xsl:template match="//CommunicationInfo"><!--#159 -->
		<communicationInfo>
			<xsl:choose>
				<xsl:when test="not(email)">
					<email>example@example.com</email>
				</xsl:when>
			</xsl:choose>
			<xsl:apply-templates select="email"/>
			<xsl:apply-templates select="url"/>
			<xsl:apply-templates select="address"/>
			<xsl:apply-templates select="zipCode"/>
			<xsl:apply-templates select="city"/>
			<xsl:apply-templates select="region"/>
			<xsl:apply-templates select="country"/>
			<xsl:apply-templates select="telephoneNumber"/>
			<xsl:apply-templates select="faxNumber"/>
		</communicationInfo>
	</xsl:template><!--#159 -->

	<xsl:template match="Resource/DistributionInfo/LicenseInfo"><!--#8 ,#9,#7-->
		<licenceInfo>
        	<xsl:apply-templates select="license"/>
        	<xsl:apply-templates select="restrictionsOfUse"/>
        	<xsl:apply-templates select="distributionAccessMedium"/>
        	<xsl:apply-templates select="downloadLocation"/>
        	<xsl:apply-templates select="executionLocation"/>
        	<xsl:apply-templates select="price"/>
        	<xsl:apply-templates select="attributionText"/>
        	<xsl:apply-templates select="licenseSignatory"/>
        	<xsl:apply-templates select="distributor"/>
    	</licenceInfo>
	</xsl:template><!--#8,#9,#7 -->
	
	<xsl:template match="Resource/DistributionInfo/LicenseInfo/restrictionsOfUse[.='informResourceOwner']"><!--#12 -->
		<restrictionsOfUse><!--
			-->informLicensor<!--
		--></restrictionsOfUse>
	</xsl:template>
	<xsl:template match="Resource/DistributionInfo/LicenseInfo/restrictionsOfUse[.='noModifications']">
		<restrictionsOfUse><!--
   			-->other<!--
		--></restrictionsOfUse>
	</xsl:template><!--#12 -->

	<xsl:template match="Resource/DistributionInfo/availability[.='notAvailable']"><!--#6 -->
		<availability><!--
   			-->notAvailableThroughMetaShare<!--
		--></availability>
	</xsl:template><!--#6 -->


	<xsl:template match="Resource/DistributionInfo/LicenseInfo/license"><!--#11-->
		<licence>
			<xsl:choose>
				<xsl:when test="text()='MSCommons'"><!--
					-->MSCommons_BY<!--
				--></xsl:when>
				<xsl:when test="text()='GFDL '"><!--
					-->GFDL<!--
				--></xsl:when>
				<xsl:when test="text()='GeneralLicenseGrant'"><!--
					-->GeneralLicenceGrant<!--
				--></xsl:when>
				<xsl:otherwise>
					<xsl:apply-templates select="@*|node()"/>
				</xsl:otherwise>
			</xsl:choose>
		</licence>
	</xsl:template>
	

	<xsl:template match="Resource/UsageInfo/ForeseenUseInfo/useNLPSpecific"><!--#28 -->
		<xsl:copy copy-namespaces="no">
		<xsl:choose>
			<xsl:when test="text()='automaticSpeechRecognition'"><!--
   				-->speechRecognition<!--
		    --></xsl:when>
		    <xsl:when test="text()='acquisition'"><!--
   				-->lexiconAcquisitionFromCorpora<!--
		    --></xsl:when>
		     <xsl:when test="text()='automaticTextGeneration'"><!--
   				-->textGeneration<!--
		    --></xsl:when>
		 
			<xsl:when test="text()='automaticPersonRecognition'"><!--
   				-->personRecognition<!--
		    --></xsl:when>
		    <xsl:when test="text()='automaticTextGeneration'"><!--
   				-->textGeneration<!--
		    --></xsl:when>
		     <xsl:when test="text()='automaticTextSummarization'"><!--
   				-->summarization<!--
		    --></xsl:when>
			<xsl:otherwise>
				<xsl:apply-templates select="@*|node()"/>
			</xsl:otherwise>
		</xsl:choose>
		</xsl:copy>
	</xsl:template>
	
	<xsl:template match="Resource/UsageInfo/ActualUseInfo/useNLPSpecific"><!--#30 -->
		<xsl:copy copy-namespaces="no">
		<xsl:choose>
			<xsl:when test="text()='automaticSpeechRecognition'"><!--
   				-->speechRecognition<!--
		    --></xsl:when>
		    <xsl:when test="text()='acquisition'"><!--
   				-->lexiconAcquisitionFromCorpora<!--
		    --></xsl:when>
		     <xsl:when test="text()='automaticTextGeneration'"><!--
   				-->textGeneration<!--
		    --></xsl:when>
		 
			<xsl:when test="text()='automaticPersonRecognition'"><!--
   				-->personRecognition<!--
		    --></xsl:when>
		    <xsl:when test="text()='automaticTextGeneration'"><!--
   				-->textGeneration<!--
		    --></xsl:when>
		     <xsl:when test="text()='automaticTextSummarization'"><!--
   				-->summarization<!--
		    --></xsl:when>
			<xsl:otherwise>
				<xsl:apply-templates select="@*|node()"/>
			</xsl:otherwise>
		</xsl:choose>
		</xsl:copy>
	</xsl:template>
	
	<xsl:template match="Resource/ResourceCreationInfo/FundingInfo"><!--#36 -->
		<xsl:apply-templates select="ProjectInfo"/>
	</xsl:template>
	<xsl:template match="Resource/ResourceCreationInfo/FundingInfo/ProjectInfo">
		<fundingProject>
			<xsl:apply-templates select="projectName"/>
			<xsl:apply-templates select="projectShortName"/>
			<xsl:apply-templates select="projectID"/>
			<xsl:apply-templates select="url"/>
			<xsl:apply-templates select="fundingType"/>
			<xsl:apply-templates select="funder"/>
			<xsl:apply-templates select="fundingCountry"/>
			<xsl:apply-templates select="projectStartDate"/>
			<xsl:apply-templates select="projectEndDate"/>
		</fundingProject>
	</xsl:template><!--#36 -->
	
	<xsl:template match="Resource/UsageInfo/ActualUseInfo/usageProject/fundingType">
		<xsl:choose>
			<xsl:when test="text()='otherFunds'">
				<xsl:copy copy-namespaces="no">other</xsl:copy>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no"><xsl:apply-templates select="@*|node()"/></xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>	
	
	
	<xsl:template match="Resource/ResourceCreationInfo/FundingInfo/ProjectInfo/fundingType">
		<xsl:choose>
			<xsl:when test="text()='otherFunds'">
				<xsl:copy copy-namespaces="no">other</xsl:copy>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no"><xsl:apply-templates select="@*|node()"/></xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>	
	
	
	<xsl:template match="//PersonInfo"><!--#157,#156 -->
		<personInfo>
			<xsl:choose>
				<xsl:when test="not(surname)">
					<surname>N/A</surname>
				</xsl:when>
			</xsl:choose>
			
			<xsl:apply-templates select="surname"/>
			<xsl:apply-templates select="givenName"/>
			<xsl:apply-templates select="CommunicationInfo"/>
			<xsl:apply-templates select="position"/>
			<xsl:apply-templates select="affiliation"/>
		</personInfo>
	</xsl:template><!--#157-->

	<xsl:template match="Resource/ToolServiceInfo/ToolServiceEvaluationInfo[not(evaluated)]"><!--#152-->
		<toolServiceEvaluationInfo>
			<evaluated>TRUE</evaluated>
			<xsl:apply-templates select="@*|node()"/>
		</toolServiceEvaluationInfo>
	</xsl:template><!--#152-->

	<xsl:template match="Resource/ToolServiceInfo[not(languageDependent)]"><!--#145-->
		<resourceComponentType>
			<toolServiceInfo>
				<languageDependent>FALSE</languageDependent>
				<xsl:apply-templates select="@*|node()"/>
			</toolServiceInfo>
		</resourceComponentType>
	</xsl:template><!--#145-->

	<xsl:template match="Resource/TextInfo/SizeInfo/sizeUnit">
		<xsl:copy copy-namespaces="no">
		<xsl:choose>
			<xsl:when test="text()='T-Hpairs'">T-HPairs</xsl:when>
			<xsl:when test="text()='questions'">units</xsl:when>
			<xsl:otherwise>
				<xsl:apply-templates select="@*|node()"/>
			</xsl:otherwise>
		</xsl:choose>
		</xsl:copy>
	</xsl:template>
	<xsl:template match="Resource/TextInfo"><!--#40, #128, #38 -->
		<xsl:choose>
			<xsl:when test="../ContentInfo/resourceType='corpus'">
				<corpusTextInfo>
					<mediaType>text</mediaType>
					<xsl:apply-templates select="LingualityInfo"/>
					<xsl:apply-templates select="LanguageInfo"/>
					<xsl:apply-templates select="LingualityInfo/modalityType"/>
					<xsl:choose>
						<xsl:when test="not(SizeInfo)">
							<sizeInfo>
								<size>0</size>
							</sizeInfo>
						</xsl:when>
					</xsl:choose>
					<xsl:apply-templates select="SizeInfo"/>
					<xsl:apply-templates select="TextFormatInfo"/>
					<xsl:apply-templates select="CharacterEncodingInfo"/>
					<xsl:apply-templates select="AnnotationInfo"/>
					<xsl:apply-templates select="DomainInfo"/>
					<xsl:apply-templates select="TextClassificationInfo"/>
					<xsl:apply-templates select="TimeCoverageInfo"/>
					<xsl:apply-templates select="GeographicCoverageInfo"/>
					<xsl:apply-templates select="TextCreationInfo[1]"/>
				</corpusTextInfo>
			</xsl:when>
			<xsl:when test="../ContentInfo/resourceType='lexicalConceptualResource'">
				<lexicalConceptualResourceTextInfo>
					<xsl:apply-templates select="../ContentInfo/mediaType[text()!='audio' and text()!='video' and text()!='image']"/>
   					<xsl:apply-templates select="LingualityInfo"/>
					<xsl:apply-templates select="LanguageInfo"/>
					<xsl:apply-templates select="LingualityInfo/modalityType"/>
					<xsl:choose>
						<xsl:when test="not(SizeInfo)">
							<sizeInfo>
								<size>0</size>
							</sizeInfo>
						</xsl:when>
					</xsl:choose>
					<xsl:apply-templates select="SizeInfo"/>
					<xsl:apply-templates select="TextFormatInfo"/>
					<xsl:apply-templates select="CharacterEncodingInfo"/>
					<xsl:apply-templates select="DomainInfo"/>
					<xsl:apply-templates select="TimeCoverageInfo"/>
					<xsl:apply-templates select="GeographicCoverageInfo"/>
				</lexicalConceptualResourceTextInfo>
			</xsl:when>
			<xsl:otherwise>	
   				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="../ContentInfo/mediaType"/>
   					<xsl:apply-templates select="LingualityInfo"/>
					<xsl:apply-templates select="LanguageInfo"/>
					<xsl:apply-templates select="LingualityInfo/modalityType"/>
					<xsl:choose>
						<xsl:when test="not(SizeInfo)">
							<sizeInfo>
								<size>0</size>
							</sizeInfo>
						</xsl:when>
					</xsl:choose>
					<xsl:apply-templates select="SizeInfo"/>
					<xsl:apply-templates select="TextFormatInfo"/>
					<xsl:apply-templates select="CharacterEncodingInfo"/>
					<xsl:apply-templates select="DomainInfo"/>
					<xsl:apply-templates select="TimeCoverageInfo"/>
					<xsl:apply-templates select="GeographicCoverageInfo"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#40-->
		
	<xsl:template match="Resource/TextInfo/LingualityInfo"><!--#41 #129-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<lingualityInfo>
							<xsl:apply-templates select="@*|node()[not(self::modalityType)]"/>
				</lingualityInfo>
			</xsl:when>
			<xsl:when test="../../ContentInfo/resourceType='lexicalConceptualResource'">
				<lingualityInfo>
					<xsl:apply-templates select="@*|node()[not(self::modalityType)]"/>
				</lingualityInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()[not(self::modalityType)]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#41-->		
	
	

	<xsl:template match="Resource/TextInfo/LingualityInfo/modalityType"><!--#42-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<modalityInfo>
					<modalityType>
							<xsl:choose>
								<xsl:when test="text()!='bodyGesture' and text()!='facialExpression' and text()!='voice' and text()!='combinationOfModalities' and text()!='signLanguage' and text()!='writtenLanguage' and text()!='spokenLanguage'"><!--
									-->other<!--
								--></xsl:when>
								<xsl:otherwise>
									<xsl:apply-templates select="@*|node()"/>
								</xsl:otherwise>
							</xsl:choose>
					</modalityType>
				</modalityInfo>
			</xsl:when>
			<xsl:when test="../../../ContentInfo/resourceType='lexicalConceptualResource'">
				<modalityInfo>
					<modalityType>
							<xsl:choose>
								<xsl:when test="text()!='bodyGesture' and text()!='facialExpression' and text()!='voice' and text()!='combinationOfModalities' and text()!='signLanguage' and text()!='writtenLanguage' and text()!='spokenLanguage'"><!--
									-->other<!--
								--></xsl:when>
								<xsl:otherwise>
									<xsl:apply-templates select="@*|node()"/>
								</xsl:otherwise>
							</xsl:choose>
					</modalityType>
				</modalityInfo>
			</xsl:when> 
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#42-->			
	
	<xsl:template match="Resource/TextInfo/LanguageInfo"><!--#43, #131-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<languageInfo>
					<xsl:choose>
						<xsl:when test="not(languageId)">
							<languageId>N/A</languageId>
						</xsl:when>
					</xsl:choose>	
					<xsl:apply-templates select="languageId"/>
					<xsl:apply-templates select="languageName"/>
					<xsl:apply-templates select="languageScript"/>
					<xsl:apply-templates select="sizePerLanguage"/>
					<xsl:apply-templates select="LanguageVarietyInfo"/>
				</languageInfo>
			</xsl:when>
			<xsl:when test="../../ContentInfo/resourceType='lexicalConceptualResource'">
				<languageInfo>
					<xsl:choose>
						<xsl:when test="not(languageId)">
							<languageId>N/A</languageId>
						</xsl:when>
					</xsl:choose>	
					<xsl:apply-templates select="languageId"/>
					<xsl:apply-templates select="languageName"/>
					<xsl:apply-templates select="languageScript"/>
					<xsl:apply-templates select="sizePerLanguage"/>
					<xsl:apply-templates select="LanguageVarietyInfo"/>
				</languageInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="languageId"/>
					<xsl:apply-templates select="languageName"/>
					<xsl:apply-templates select="languageScript"/>
					<xsl:apply-templates select="sizePerLanguage"/>
					<xsl:apply-templates select="LanguageVarietyInfo"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#43-->	

	<xsl:template match="Resource/TextInfo/LanguageInfo/languageCoding"><!--#44,#132-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">		
			</xsl:when>
			<xsl:when test="../../../ContentInfo/resourceType='lexicalConceptualResource'">
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#44-->	

	

	<xsl:template match="Resource/TextInfo/TextCreationInfo"><!--#46-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<creationInfo>
							<xsl:apply-templates select="@*|node()"/>
				</creationInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#46-->		

	<xsl:template match="Resource/TextInfo/TextCreationInfo/originalSource"><!--#47-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<originalSource>
					<targetResourceNameURI>
							<xsl:apply-templates select="@*|node()"/>
					</targetResourceNameURI>
				</originalSource>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#47-->	
	
	<xsl:template match="Resource/TextInfo/TextCreationInfo/creationTool"><!--#48-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<creationTool>
					<targetResourceNameURI>
							<xsl:apply-templates select="@*|node()"/>
					</targetResourceNameURI>
				</creationTool>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#48-->	

	<xsl:template match="Resource/TextInfo/SizeInfo"><!--#49,#134-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<sizeInfo>
					<xsl:choose>
							<xsl:when test="not(size)">
								<size>0</size>
							</xsl:when>
					</xsl:choose>
					<xsl:apply-templates select="@*|node()"/>
				</sizeInfo>
			</xsl:when>
			<xsl:when test="../../ContentInfo/resourceType='lexicalConceptualResource'">
				<sizeInfo>
					<xsl:choose>
							<xsl:when test="not(size)">
								<size>0</size>
							</xsl:when>
					</xsl:choose>
					<xsl:apply-templates select="@*|node()"/>
				</sizeInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
					<xsl:choose>
							<xsl:when test="not(size)">
								<size>0</size>
							</xsl:when>
						
					</xsl:choose>
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#49-->			

	<xsl:template match="//size"><!--#50-->
		<xsl:choose>
			<xsl:when test="../sizeUnitMultiplier='kilo'">
				<xsl:copy copy-namespaces="no">
					<xsl:value-of select="text()*1000"/>
				</xsl:copy>
			</xsl:when>
			<xsl:when test="../sizeUnitMultiplier='hundred'">
				<xsl:copy copy-namespaces="no">
					<xsl:value-of select="text()*100"/>
				</xsl:copy>
			</xsl:when>
			<xsl:when test="../sizeUnitMultiplier='mega'">
				<xsl:copy copy-namespaces="no">
					<xsl:value-of select="format-number(text()*1000000,'0')"/>
				</xsl:copy>
			</xsl:when>
			<xsl:when test="../sizeUnitMultiplier='tera'">
				<xsl:copy copy-namespaces="no">
					<xsl:value-of select="format-number(text()*1000000000000,'0')"/>
				</xsl:copy>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#50-->

	<xsl:template match="//sizeUnitMultiplier"><!--#51-->
	</xsl:template><!--#51-->

	<xsl:template match="Resource/TextInfo/TextFormatInfo"><!--#52--><!--#135-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<textFormatInfo>
					<xsl:apply-templates select= "mime-type[1]"/>
					<xsl:apply-templates select= "sizePerTextFormat[1]"/>
				</textFormatInfo>
			</xsl:when>
			<xsl:when test="../../ContentInfo/resourceType='lexicalConceptualResource'">
				<textFormatInfo>
					<xsl:apply-templates select= "mime-type[1]"/>
					<xsl:apply-templates select= "sizePerTextFormat[1]"/>
				</textFormatInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select= "mime-type[1]"/>
					<xsl:apply-templates select= "sizePerTextFormat[1]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#52-->	

	<xsl:template match="Resource/TextInfo/TextFormatInfo/mime-type"><!--#53 #136-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<mimeType>
					<xsl:apply-templates select="@*|node()"/>
				</mimeType>
			</xsl:when>
				<xsl:when test="../../../ContentInfo/resourceType='lexicalConceptualResource'">
				<mimeType>
					<xsl:apply-templates select="@*|node()"/>
				</mimeType>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#53-->	
	
	<xsl:template match="Resource/TextInfo/CharacterEncodingInfo"><!--#54,#140-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<characterEncodingInfo>
					<xsl:apply-templates select="characterEncoding[1]"/>
				
					<xsl:apply-templates select="sizePerCharacterEncoding[1]"/>
				</characterEncodingInfo>
			</xsl:when>
			<xsl:when test="../../ContentInfo/resourceType='lexicalConceptualResource'">
				<characterEncodingInfo>
					<xsl:apply-templates select="characterEncoding[1]"/>
					<xsl:apply-templates select="sizePerCharacterEncoding[1]"/>
				</characterEncodingInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="characterEncoding[1]"/>
   					<xsl:apply-templates select="characterSet"/>
					<xsl:apply-templates select="sizePerCharacterEncoding[1]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#54-->	


	<xsl:template match="Resource/TextInfo/CharacterEncodingInfo/characterSet"><!--#56,#131-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">	
			</xsl:when>
			<xsl:when test="../../../ContentInfo/resourceType='lexicalConceptualResource'">
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#56-->
	
	<xsl:template match="Resource/TextInfo/CharacterEncodingInfo/characterEncoding"><!--#55-->
	<xsl:copy copy-namespaces="no">
		<xsl:choose>
		
			<xsl:when test="../../../ContentInfo/resourceType='corpus' and text()!='US-ASCII' and text()!='windows-1250' and text()!='windows-1251' and text()!='windows-1252' and text()!='windows-1253' and text()!='windows-1254' and text()!='windows-1257' and text()!='ISO-8859-1' and text()!='ISO-8859-2' and text()!='ISO-8859-4' and text()!='ISO-8859-5' and text()!='ISO-8859-7' and text()!='ISO-8859-9' and text()!='ISO-8859-13' and text()!='ISO-8859-15' and text()!='UTF-8' "><!--	
				-->MacDingbat<!--
			--></xsl:when>
				<xsl:when test="../../../ContentInfo/resourceType='lexicalConceptualResource' and text()!='US-ASCII' and text()!='windows-1250' and text()!='windows-1251' and text()!='windows-1252' and text()!='windows-1253' and text()!='windows-1254' and text()!='windows-1257' and text()!='ISO-8859-1' and text()!='ISO-8859-2' and text()!='ISO-8859-4' and text()!='ISO-8859-5' and text()!='ISO-8859-7' and text()!='ISO-8859-9' and text()!='ISO-8859-13' and text()!='ISO-8859-15' and text()!='UTF-8' "><!--	
				-->MacDingbat<!--
			--></xsl:when>
			<xsl:otherwise>
   					<xsl:apply-templates select="@*|node()"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:copy>
	</xsl:template><!--#55 -->	

	<xsl:template match="Resource/TextInfo/DomainInfo"><!--#57-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<domainInfo>
					<xsl:apply-templates select="domain"/>
					<xsl:apply-templates select="sizePerDomain[1]"/>
				</domainInfo>
			</xsl:when>
			<xsl:when test="../../ContentInfo/resourceType='lexicalConceptualResource'">
				<domainInfo>
					<xsl:apply-templates select="domain"/>
					<xsl:apply-templates select="sizePerDomain[1]"/>
				</domainInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="domain"/>
					<xsl:apply-templates select="sizePerDomain[1]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#57-->	

	<xsl:template match="Resource/TextInfo/TimeCoverageInfo"><!--#58,#141-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<timeCoverageInfo>
					<xsl:apply-templates select="timeCoverage"/>
					<xsl:apply-templates select="sizePerTimeCoverage[1]"/>
				</timeCoverageInfo>
			</xsl:when>
			<xsl:when test="../../ContentInfo/resourceType='lexicalConceptualResource'">
				<timeCoverageInfo>
					<xsl:apply-templates select="timeCoverage"/>
					<xsl:apply-templates select="sizePerTimeCoverage[1]"/>
				</timeCoverageInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="timeCoverage"/>
					<xsl:apply-templates select="sizePerTimeCoverage[1]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#58-->	

	

	<xsl:template match="Resource/TextInfo/TextClassificationInfo"><!--#60-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<textClassificationInfo>
					<xsl:apply-templates select="textGenre"/>
					<xsl:apply-templates select="textType"/>
					<xsl:apply-templates select="register"/>
					<xsl:apply-templates select="subject_Topic"/>
					<xsl:apply-templates select="conformanceToClassificationScheme"/>
					<xsl:apply-templates select="sizePerTextClassification[1]"/>
				</textClassificationInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="textGenre"/>
					<xsl:apply-templates select="textType"/>
					<xsl:apply-templates select="register"/>
					<xsl:apply-templates select="subject_Topic"/>
					<xsl:apply-templates select="conformanceToClassificationScheme"/>
					<xsl:apply-templates select="sizePerTextClassification[1]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#60-->	

	<xsl:template match="Resource/TextInfo/TextClassificationInfo/conformanceToClassificationScheme"><!--#61-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<xsl:copy copy-namespaces="no">
					<xsl:choose>
						<xsl:when test="text()!='ANC_domainClassification' and text()!='ANC_genreClassification' and text()!='BNC_domainClassification' and text()!='BNC_textTypeClassification' and text()!='DDC_classification' and text()!='libraryOfCongress_domainClassification' and text()!='libraryofCongressSubjectHeadings_classification' and text()!='MeSH_classification' and text()!='NLK_classification' and text()!='PAROLE_topicClassification' and text()!='PAROLE_genreClassification'  and text()!='UDC_classification'">other</xsl:when>
						<xsl:otherwise>	
   							<xsl:apply-templates select="@*|node()"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:copy>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#61-->	
	
	
	
	<xsl:template match="Resource/TextInfo/AnnotationInfo"><!--#62-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<annotationInfo>
					<xsl:apply-templates select="annotationType"/>
					<xsl:apply-templates select="annotatedElements"/>
					<xsl:apply-templates select="annotationStandoff"/>
					<xsl:apply-templates select="segmentationLevel"/>
					<xsl:apply-templates select="annotationFormat"/>
					<xsl:apply-templates select="tagset"/>
					<xsl:apply-templates select="tagsetLanguageId"/>
					<xsl:apply-templates select="conformanceToStandardsBestPractice"/>
					<xsl:apply-templates select="theoreticModel"/>
					<xsl:apply-templates select="annotationManual"/>
					<xsl:apply-templates select="annotationMode"/>
					<xsl:apply-templates select="annotationModeDetails"/>
					<xsl:apply-templates select="annotationTool"/>
					<xsl:apply-templates select="annotationStartDate"/>
					<xsl:apply-templates select="annotationEndDate"/>
					<xsl:apply-templates select="sizePerAnnotation"/>
					<xsl:apply-templates select="interAnnotatorAggreement"/>
					<xsl:apply-templates select="intraAnnotatorAggreement"/>
					<xsl:apply-templates select="annotator"/>
					
				</annotationInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="annotationType"/>
					<xsl:apply-templates select="annotatedElements"/>
					<xsl:apply-templates select="annotationStandoff"/>
					<xsl:apply-templates select="segmentationLevel"/>
					<xsl:apply-templates select="annotationFormat"/>
					<xsl:apply-templates select="tagset"/>
					<xsl:apply-templates select="tagsetLanguageId"/>
					<xsl:apply-templates select="conformanceToStandardsBestPractice"/>
					<xsl:apply-templates select="theoreticModel"/>
					<xsl:apply-templates select="annotationManual"/>
					<xsl:apply-templates select="annotationMode"/>
					<xsl:apply-templates select="annotationModeDetails"/>
					<xsl:apply-templates select="annotationTool"/>
					<xsl:apply-templates select="annotationStartDate"/>
					<xsl:apply-templates select="annotationEndDate"/>
					<xsl:apply-templates select="sizePerAnnotation"/>
					<xsl:apply-templates select="interAnnotatorAggreement"/>
					<xsl:apply-templates select="intraAnnotatorAggreement"/>
					<xsl:apply-templates select="annotator"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#62-->	
	
	<xsl:template match="Resource/TextInfo/AnnotationInfo/annotationType"><!--#63-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<xsl:copy copy-namespaces="no">
					<xsl:choose>
						<xsl:when test="text()='audienceReactions'"><!--
							-->discourseAnnotation-audienceReactions</xsl:when>
						<xsl:when test="text()='semanticAnnotation-Events'"><!--
							-->semanticAnnotation-events</xsl:when>
						<xsl:when test="text()='questionTopicalTarget'"><!--
							-->semanticAnnotation-questionTopicalTarget</xsl:when>
						<xsl:when test="text()='textualEntailment'"><!--
							-->semanticAnnotation-textualEntailment</xsl:when>
						<xsl:when test="text()='speechActs'"><!--
							-->semanticAnnotation-speechActs</xsl:when>
						<xsl:when test="text()='morphosyntacticAnnotation'"><!--
							-->morphosyntacticAnnotation-bPosTagging<!--
					--></xsl:when>
						<xsl:when test="text()='PosTagging'"><!--
							-->morphosyntacticAnnotation-posTagging<!--
							--></xsl:when>
						<xsl:when test="text()='coreference'"><!--
							-->discourseAnnotation-coreference<!--
							--></xsl:when>
						<xsl:when test="text()='morphosyntacticAnnotation-bposTagging'"><!--
							-->morphosyntacticAnnotation-bPosTagging<!--
					--></xsl:when>
						<xsl:when test="text()='nounPhrase'"><!--
							-->syntacticAnnotation-shallowParsing<!--
					--></xsl:when>
						<xsl:when test="text()='orthographicTranscription'"><!--
							-->speechAnnotation-orthographicTranscription<!--
					--></xsl:when>
						<xsl:when test="text()='soundToTextAlignment'"><!--
							-->speechAnnotation-soundToTextAlignment<!--
					--></xsl:when>
						<xsl:otherwise>	
   							<xsl:apply-templates select="@*|node()"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:copy>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#63-->	

	<xsl:template match="Resource/TextInfo/AnnotationInfo/annotationManual"><!--#64-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<annotationManual>
					<documentUnstructured>
						<xsl:apply-templates select="@*|node()"/>
					</documentUnstructured>
				</annotationManual>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#64-->	


	<xsl:template match="Resource/TextInfo/AnnotationInfo/conformanceToStandardsBestPractice"><!--#65-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<conformanceToStandardsBestPractices>
					<xsl:choose>
						<xsl:when test="text()='PDT'">pragueTreebank</xsl:when>
						<xsl:when test="text()='SYNAF'">SynAF</xsl:when>
						<xsl:when test="text()='EAGLES'">other</xsl:when>
						<xsl:when test="text()='GrAF'">other</xsl:when>
						<xsl:otherwise>	
   							<xsl:apply-templates select="@*|node()"/>
						</xsl:otherwise>
					</xsl:choose>
				</conformanceToStandardsBestPractices>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#65-->	
	
	
	<xsl:template match="Resource/TextInfo/AnnotationInfo/annotationTool"><!--#66-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<annotationTool>
					<targetResourceNameURI>
						<xsl:apply-templates select="@*|node()"/>
					</targetResourceNameURI>
				</annotationTool>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#66-->	
	
	<xsl:template match="Resource/AudioInfo/AudioAnnotationInfo/annotationTool"><!--#106-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<annotationTool>
					<targetResourceNameURI>
						<xsl:apply-templates select="@*|node()"/>
					</targetResourceNameURI>
				</annotationTool>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#106-->	

	<xsl:template match="Resource/TextInfo/AnnotationInfo/annotator"><!--#67-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<annotator>
					<personInfo>
						<xsl:choose>
							<xsl:when test="not(surname)">
							<surname>N/A</surname>
							</xsl:when>
						</xsl:choose>
				
						<xsl:apply-templates select="surname"/>
						<xsl:apply-templates select="givenName"/>
						<xsl:apply-templates select="CommunicationInfo"/>
						<xsl:apply-templates select="position"/>
						<xsl:apply-templates select="affiliation"/>
						
						
						
					</personInfo>
				</annotator>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#67-->	

	<!--<xsl:template match="Resource/TextInfo/AnnotationInfo/annotator[not(surname)]"><#68 !attention!
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<annotator>
					<surname>N/A</surname>
					<xsl:apply-templates select="@*|node()"/>
				</annotator>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>#68-->
	
	<xsl:template match="Resource/AudioInfo"><!--#69 ,#39b-->
	 	<corpusAudioInfo>
	 		<mediaType>audio</mediaType>
	 		<xsl:apply-templates select="LingualityInfo"/>
	 		<xsl:choose>
	 			<xsl:when test="not(LanguageInfo)">
					<xsl:apply-templates select="../TextInfo/LanguageInfo"/>
	 			</xsl:when>
	 		</xsl:choose>
	 		<xsl:apply-templates select="LanguageInfo"/>
	 		<xsl:apply-templates select="modalityType"/>
	 		<xsl:choose>
	 			<xsl:when test="not(AudioSizeInfo)">
					<audioSizeInfo><sizeInfo><size>0</size><sizeUnit>hours</sizeUnit></sizeInfo></audioSizeInfo>
	 			</xsl:when>
	 		</xsl:choose>
	 		<xsl:apply-templates select="LingualityInfo/modalityType"/>
	 		<xsl:apply-templates select="AudioSizeInfo"/>
	 		<xsl:apply-templates select="AudioContentInfo"/>
	 		<xsl:apply-templates select="AudioSettingInfo"/>
	 		<xsl:apply-templates select="AudioFormatInfo"/>
	 		<xsl:apply-templates select="AudioAnnotationInfo"/>
	 		<xsl:apply-templates select="DomainInfo"/>
	 		<xsl:apply-templates select="TextClassificationInfo"/>
	 		<xsl:apply-templates select="TimeCoverageInfo"/>
	 		<xsl:apply-templates select="GeographicCoverageInfo"/>
	 		<xsl:apply-templates select="AudioclassificationInfo"/>
	 		<xsl:apply-templates select="AudioRecordingInfo"/>
	 		<xsl:apply-templates select="AudioRecordingInfo/AudioCaptureInfo[1]"/>
	 		<xsl:apply-templates select="AudioRecordingInfo/originalSource[1]"/>	
	 	</corpusAudioInfo>
	</xsl:template>

	<xsl:template match="Resource/AudioInfo/LingualityInfo"><!--#70-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<lingualityInfo>
					<xsl:apply-templates select="@*|node()[not(self::modalityType)]"/>
				</lingualityInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#70-->	
	
	
	<xsl:template match="Resource/AudioInfo/LingualityInfo/modalityType"><!--#71-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<modalityInfo>
					<modalityType>
							<xsl:choose>
								<xsl:when test="text()!='bodyGesture' and text()!='facialExpression' and text()!='voice' and text()!='combinationOfModalities' and text()!='signLanguage' and text()!='writtenLanguage' and text()!='spokenLanguage'"><!--
									-->other<!--
								--></xsl:when>
								<xsl:otherwise>
									<xsl:apply-templates select="@*|node()"/>
								</xsl:otherwise>
							</xsl:choose>
					</modalityType>
				</modalityInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#71-->	
			
			
	<xsl:template match="Resource/AudioInfo/LanguageInfo"><!--#72-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<languageInfo>
					<xsl:choose>
						<xsl:when test="not(languageId)">
							<languageId>N/A</languageId>
						</xsl:when>
					</xsl:choose>	
					<xsl:apply-templates select="languageId"/>
					<xsl:apply-templates select="languageName"/>
					<xsl:apply-templates select="languageScript"/>
					<xsl:apply-templates select="sizePerLanguage"/>
					<xsl:apply-templates select="LanguageVarietyInfo"/>
				</languageInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:choose>
						<xsl:when test="not(languageId)">
							<languageId>N/A</languageId>
						</xsl:when>
					</xsl:choose>	
					<xsl:apply-templates select="languageId"/>
					<xsl:apply-templates select="languageName"/>
					<xsl:apply-templates select="languageScript"/>
					<xsl:apply-templates select="sizePerLanguage"/>
					<xsl:apply-templates select="LanguageVarietyInfo"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#72-->	

	<xsl:template match="Resource/AudioInfo/LanguageInfo/languageCoding"><!--#73-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">		
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#73-->

	<xsl:template match="Resource/AudioInfo/LanguageInfo/LanguageVarietyInfo"><!--#74-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<languageVarietyInfo>
					<xsl:apply-templates select="languageVarietyType"/>
					<xsl:apply-templates select="languageVarietyName"/>
					<xsl:apply-templates select="sizePerLanguageVariety[1]"/>
					<xsl:choose>
					
						<xsl:when test="not(sizePerLanguageVariety)">
							<sizePerLanguageVariety>
								<size>0</size>
								<sizeUnit>units</sizeUnit>
							</sizePerLanguageVariety>
						</xsl:when>
					</xsl:choose>
				</languageVarietyInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="languageVarietyType"/>
					<xsl:apply-templates select="languageVarietyName"/>
					<xsl:apply-templates select="sizePerLanguageVariety[1]"/>
					<xsl:choose>
						<xsl:when test="not(sizePerLanguageVariety)">
							<sizePerLanguageVariety>
								<size>0</size>
								<sizeUnit>units</sizeUnit>
							</sizePerLanguageVariety>
						</xsl:when>
					</xsl:choose>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#74-->	
	
	<xsl:template match="Resource/AudioInfo/AudioContentInfo"><!--#75-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<audioContentInfo>
					<xsl:apply-templates select="speechItems"/>
					<xsl:apply-templates select="nonSpeechItems"/>
					<xsl:apply-templates select="textualDescription"/>
					<xsl:apply-templates select="../AudioSettingInfo/noiseLevel"/>
					
				</audioContentInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#75-->	
	<xsl:template match="Resource/AudioInfo/AudioContentInfo/nonSpeechItems"><!--#76-->
				<xsl:choose>
					<xsl:when test="text()!='notes' and text()!='tempo' and text()!='sounds'  and text()!='noise' and text()!='music' and text()!='commercial' and text()!='other' ">
						<xsl:copy copy-namespaces="no">other</xsl:copy>
					</xsl:when>
					<xsl:otherwise>
						<xsl:copy copy-namespaces="no">
	   						<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
					</xsl:otherwise>
				</xsl:choose>
	</xsl:template>
	
	
	<xsl:template match="Resource/AudioInfo/AudioContentInfo/speechItems"><!--#76-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<xsl:choose>
					<xsl:when test="text()!='isolatedWords' and text()!='isolatedDigits' and text()!='naturalNumbers'  and text()!='properNouns' and text()!='applicationWords' and text()!='phoneticallyRichSentences' and text()!='phoneticallyRichWords' and text()!='phoneticallyBalancedSentences' and text()!='moneyAmounts' and text()!='creditCardNumbers' and text()!='telephoneNumbers' and text()!='yesNoQuestions' and text()!='vcvSequences' and text()!='freeSpeech'">
						<xsl:copy copy-namespaces="no">other</xsl:copy>
					</xsl:when>
					<xsl:otherwise>
						<xsl:copy copy-namespaces="no">
	   						<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:otherwise>
				<xsl:choose>
					<xsl:when test="text()!='isolatedWords' and text()!='isolatedDigits' and text()!='naturalNumbers'  and text()!='properNouns' and text()!='applicationWords' and text()!='phoneticallyRichSentences' and text()!='phoneticallyRichWords' and text()!='phoneticallyBalancedSentences' and text()!='moneyAmounts' and text()!='creditCardNumbers' and text()!='telephoneNumbers' and text()!='yesNoQuestions' and text()!='vcvSequences' and text()!='freeSpeech'">
						<xsl:copy copy-namespaces="no">
	   						other
						</xsl:copy>
					</xsl:when>
					<xsl:otherwise>
						<xsl:copy copy-namespaces="no">
	   						<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#76-->	

	<xsl:template match="Resource/AudioInfo/AudioSizeInfo"><!--#77-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<audioSizeInfo>
					<sizeInfo>
						<xsl:choose>
							<xsl:when test="not(size)">
								<size>0</size>
							</xsl:when>
						</xsl:choose>
						<xsl:apply-templates select="size"/>
						<xsl:apply-templates select="sizeUnit"/>
					</sizeInfo>
						<xsl:apply-templates select="DurationOfEffectiveSpeechInfo"/>
						<xsl:apply-templates select="DurationOfAudioInfo"/>
				</audioSizeInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#77-->	
	
	<xsl:template match="Resource/AudioInfo/AudioSizeInfo/DurationOfEffectiveSpeechInfo"><!--#78-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<durationOfEffectiveSpeechInfo>
					<xsl:apply-templates select="@*|node()"/>
				</durationOfEffectiveSpeechInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#78-->	

	<xsl:template match="Resource/AudioInfo/AudioSizeInfo/DurationOfEffectiveSpeechInfo/sizeUnit"><!--#79-->
		<xsl:choose>
			<xsl:when test="../../../../ContentInfo/resourceType='corpus'">
				<durationUnit>
					<xsl:choose>
						<xsl:when test="text()='T-Hpairs'">T-HPairs</xsl:when>
						<xsl:when test="text()='questions'">units</xsl:when>
						<xsl:otherwise>
							<xsl:apply-templates select="@*|node()"/>
						</xsl:otherwise>
					</xsl:choose>
				</durationUnit>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#79-->	

	<xsl:template match="Resource/AudioInfo/AudioSizeInfo/DurationOfAudioInfo"><!--#80-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<durationOfAudioInfo>
					<xsl:apply-templates select="@*|node()"/>
				</durationOfAudioInfo>
			</xsl:when>
			<xsl:otherwise>
				<durationOfAudioInfo>
   					<xsl:apply-templates select="@*|node()"/>
				</durationOfAudioInfo>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#80-->	
	
	<xsl:template match="Resource/AudioInfo/AudioSizeInfo/DurationOfAudioInfo/sizeUnit"><!--#81-->
		<xsl:choose>
			<xsl:when test="../../../../ContentInfo/resourceType='corpus'">
				<durationUnit>
					<xsl:choose>
						<xsl:when test="text()='T-Hpairs'">T-HPairs</xsl:when>
						<xsl:when test="text()='questions'">units</xsl:when>
						<xsl:otherwise>
							<xsl:apply-templates select="@*|node()"/>
						</xsl:otherwise>
					</xsl:choose>
				</durationUnit>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#81-->	
	
	<xsl:template match="Resource/AudioInfo/AudioFormatInfo"><!--#82-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<audioFormatInfo>
					<xsl:apply-templates select="mime-type[1]"/>
					<xsl:apply-templates select="signalEncoding"/>
					<xsl:apply-templates select="samplingRate"/>
					<xsl:apply-templates select="quantization"/>
					<xsl:apply-templates select="byteOrder"/>
					<xsl:apply-templates select="signConvention"/>
					<xsl:apply-templates select="compression"/>
					<xsl:apply-templates select="audioQualityMeasuresIncluded"/>
					<xsl:apply-templates select="numberOfTracks"/>
					<xsl:apply-templates select="recordingQuality"/>
					<xsl:apply-templates select="sizePerAudioFormat[1]"/>
				</audioFormatInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="mime-type[1]"/>
					<xsl:apply-templates select="signalEncoding"/>
					<xsl:apply-templates select="samplingRate"/>
					<xsl:apply-templates select="quantization"/>
					<xsl:apply-templates select="byteOrder"/>
					<xsl:apply-templates select="signConvention"/>
					<xsl:apply-templates select="compression"/>
					<xsl:apply-templates select="audioQualityMeasuresIncluded"/>
					<xsl:apply-templates select="numberOfTracks"/>
					<xsl:apply-templates select="recordingQuality"/>
					<xsl:apply-templates select="sizePerAudioFormat[1]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#82-->	
	
	
	<xsl:template match="Resource/AudioInfo/AudioFormatInfo/mime-type"><!--#83-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<mimeType>
					<xsl:apply-templates select="@*|node()"/>
				</mimeType>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#83-->	 
	
	<xsl:template match="Resource/AudioInfo/AudioFormatInfo/byteOrder"><!--#84-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<xsl:copy copy-namespaces="no">
					<xsl:choose>
						<xsl:when test="text()='lowHi'"><!--
							-->littleEndian<!--
						--></xsl:when>
						<xsl:when test="text()='hiLow'"><!--
							-->bigEndian<!--
						--></xsl:when>
						<xsl:otherwise>
							<xsl:apply-templates select="@*|node()"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:copy>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:choose>
						<xsl:when test="text()='lowHi'"><!--
							-->littleEndian<!--
						--></xsl:when>
						<xsl:when test="text()='hiLow'"><!--
							-->bigEndian<!--
						--></xsl:when>
						<xsl:otherwise>
							<xsl:apply-templates select="@*|node()"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#84-->
	
	<xsl:template match="Resource/AudioInfo/AudioFormatInfo/signalEncoding"><!--#84-->
		<xsl:copy copy-namespaces="no">
			<xsl:choose>
				<xsl:when test="text()='microLaw'"><!--
					-->µ-law<!--
					--></xsl:when>
				<xsl:otherwise>
					<xsl:apply-templates select="@*|node()"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:copy>	
	</xsl:template><!--#84-->
		
	<xsl:template match="Resource/AudioInfo/AudioFormatInfo/samplingRate"><!--#84-->
		<xsl:copy copy-namespaces="no">
			<xsl:choose>
				<xsl:when test="text()!='8000' and text()!='16000' and text()!='44100' and text()!='48000' and text()!='9600' ">44100</xsl:when>
				<xsl:otherwise>
					<xsl:apply-templates select="@*|node()"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:copy>
	</xsl:template><!--#84-->	
	
	<xsl:template match="Resource/AudioInfo/AudioFormatInfo/signConvention"><!--#85-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<xsl:copy copy-namespaces="no">
					<xsl:choose>
						<xsl:when test="text()='signed'">signedInteger</xsl:when>
						<xsl:when test="text()='unsigned'">unsignedInteger</xsl:when>
						<xsl:otherwise>
							<xsl:apply-templates select="@*|node()"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:copy>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#85-->	
	
	<xsl:template match="Resource/AudioInfo/AudioFormatInfo/compression"><!--#86-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<compressionInfo>
					<compression>
						<xsl:apply-templates select="@*|node()"/>
					</compression>
					<xsl:apply-templates select="../compressionName"/>
					<xsl:apply-templates select="../compressionLoss"/>
					
				</compressionInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#86-->	

	<xsl:template match="Resource/AudioInfo/AudioFormatInfo/compressionName"><!--#87-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<xsl:copy copy-namespaces="no">
					<xsl:choose>
						<xsl:when test="text()='vorbis'"><!--
							-->oggVorbis<!--
					--></xsl:when>
						<xsl:otherwise>
							<xsl:apply-templates select="@*|node()"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:copy>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#87-->	


	<xsl:template match="Resource/AudioInfo/AudioFormatInfo/compressionLoss"><!--#88-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
					<compressionLoss>
						<xsl:apply-templates select="@*|node()"/>
					</compressionLoss>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#88-->	
	
	
	<xsl:template match="Resource/AudioInfo/AudioFormatInfo/numberOfTracks"><!--#89-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<xsl:copy copy-namespaces="no">
					<xsl:choose>
						<xsl:when test="text()='mono'">1</xsl:when>
						<xsl:when test="text()='stereo'">2</xsl:when>
						<xsl:otherwise>
							<xsl:apply-templates select="@*|node()"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:copy>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#89-->	
	
	<xsl:template match="Resource/AudioInfo/AudioSettingInfo"><!--#91-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<settingInfo>
					<xsl:apply-templates select="typeOfSituationOfCommunication"/>
					<xsl:apply-templates select="speechSetting[1]"/>
					<xsl:apply-templates select="speechTask[1]"/>
					<xsl:apply-templates select="audience"/>
					<xsl:apply-templates select="interactivity"/>
				</settingInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#91-->	
	
	<xsl:template match="Resource/AudioInfo/AudioSettingInfo/typeOfSituationOfCommunication"><!--#92-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<naturality>
					<xsl:choose>
						<xsl:when test="text()='plannedSpeech'"><!--
							-->planned<!--
						--></xsl:when>
						<xsl:when test="text()='semiPlannedSpeech'"><!--
							-->semiPlanned<!--
						--></xsl:when>
						<xsl:when test="text()='spontaneousSpeech'"><!--
							-->spontaneous<!--
						--></xsl:when>
						<xsl:when test="text()='emotionalSpeech'"><!--
							-->other<!--
						--></xsl:when>
						<xsl:otherwise>	
   							<xsl:apply-templates select="@*|node()"/>
						</xsl:otherwise>
					</xsl:choose>
				</naturality>
			</xsl:when>
			<xsl:otherwise>
				<naturality>
					<xsl:choose>
						<xsl:when test="text()='plannedSpeech'"><!--
							-->planned<!--
						--></xsl:when>
						<xsl:when test="text()='semiPlannedSpeech'"><!--
							-->semiPlanned<!--
						--></xsl:when>
						<xsl:when test="text()='spontaneousSpeech'"><!--
							-->spontaneous<!--
						--></xsl:when>
						<xsl:when test="text()='emotionalSpeech'"><!--
							-->other<!--
						--></xsl:when>
						<xsl:otherwise>	
   							<xsl:apply-templates select="@*|node()"/>
						</xsl:otherwise>
					</xsl:choose>
				</naturality>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#92-->	
	
	
	<xsl:template match="Resource/AudioInfo/AudioSettingInfo/speechSetting"><!--#93-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<conversationalType>
					<xsl:apply-templates select="@*|node()"/>
				</conversationalType>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#93-->	

	<xsl:template match="Resource/AudioInfo/AudioSettingInfo/speechTask"><!--#94-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<scenarioType>
					<xsl:choose>
						<xsl:when test="text()='lecture'">other</xsl:when>
						<xsl:when test="text()='meeting'">other</xsl:when>
						<xsl:otherwise>	
   							<xsl:apply-templates select="@*|node()"/>
						</xsl:otherwise>
					</xsl:choose>
				</scenarioType>
			</xsl:when>
			<xsl:otherwise>
				<scenarioType>
					<xsl:choose>
						<xsl:when test="text()='lecture'">other</xsl:when>
						<xsl:when test="text()='meeting'">other</xsl:when>
						<xsl:otherwise>	
   							<xsl:apply-templates select="@*|node()"/>
						</xsl:otherwise>
					</xsl:choose>
				</scenarioType>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#94-->	
	
	
	<xsl:template match="Resource/AudioInfo/DomainInfo"><!--#96-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<domainInfo>
					<xsl:apply-templates select="domain"/>
					<xsl:apply-templates select="sizePerDomain[1]"/>
				</domainInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
					<xsl:apply-templates select="domain"/>
					<xsl:apply-templates select="sizePerDomain[1]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#96-->	
	
	<xsl:template match="Resource/AudioInfo/TimeCoverageInfo"><!--#97-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<timeCoverageInfo>
					<xsl:apply-templates select="timeCoverage"/>
					<xsl:apply-templates select="sizePerTimeCoverage[1]"/>
				</timeCoverageInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="timeCoverage"/>
					<xsl:apply-templates select="sizePerTimeCoverage[1]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#97-->	
	
	<xsl:template match="Resource/AudioInfo/GeographicCoverageInfo"><!--#98-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<geographicCoverageInfo>
					<xsl:apply-templates select="geographicCoverage"/>
					<xsl:apply-templates select="sizePerGeographicCoverage[1]"/>
				</geographicCoverageInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="geographicCoverage"/>
					<xsl:apply-templates select="sizePerGeographicCoverage[1]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#98-->	
	
	<xsl:template match="Resource/AudioInfo/AudioClassificationInfo"><!--#99-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<audioClassificationInfo>
					<xsl:apply-templates select="@*|node()"/>
				</audioClassificationInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#99-->	
	
	
	
	<xsl:template match="Resource/AudioInfo/AudioClassificationInfo/speechGenre"><!--#100-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<xsl:copy copy-namespaces="no">
					<xsl:choose>
						<xsl:when test="text()='broadcast'">
							broadcastNews
						</xsl:when>
						<xsl:when test="text()='news'">semiPlanned</xsl:when>
						<xsl:when test="text()='emotional_expressive'">emotionalExpressive</xsl:when>
						<xsl:when test="text()='wideband' or text()='spontaneous' or text()='animalSpeech' ">other</xsl:when>
						<xsl:otherwise>	
   							<xsl:apply-templates select="@*|node()"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:copy>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#100-->	
	
	<xsl:template match="Resource/AudioInfo/AudioClassificationInfo/conformanceToClassificationScheme"><!--#101-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<xsl:copy copy-namespaces="no">
					<xsl:choose>
						<xsl:when test="text()!='ANC_domainClassification' and text()!='ANC_genreClassification' and text()!='BNC_domainClassification' and text()!='BNC_textTypeClassification' and text()!='DDC_classification' and text()!='libraryOfCongress_domainClassification' and text()!='libraryofCongressSubjectHeadings_classification' and text()!='MeSH_classification' and text()!='NLK_classification' and text()!='PAROLE_topicClassification' and text()!='PAROLE_genreClassification'  and text()!='UDC_classification'">other</xsl:when>
						<xsl:otherwise>	
   							<xsl:apply-templates select="@*|node()"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:copy>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#101-->	
	
	<xsl:template match="Resource/AudioInfo/AudioAnnotationInfo"><!--#102-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<annotationInfo>
					<xsl:apply-templates select="annotationType"/>
					<xsl:apply-templates select="annotatedElements"/>
					<xsl:apply-templates select="annotationStandoff"/>
					<xsl:apply-templates select="segmentationLevel"/>
					<xsl:apply-templates select="annotationFormat"/>
					<xsl:apply-templates select="tagset"/>
					<xsl:apply-templates select="tagsetLanguageId"/>
					<xsl:apply-templates select="conformanceToStandardsBestPractice"/>
					<xsl:apply-templates select="theoreticModel"/>
					<xsl:apply-templates select="annotationManual"/>
					<xsl:apply-templates select="annotationMode"/>
					<xsl:apply-templates select="annotationModeDetails"/>
					<xsl:apply-templates select="annotationTool"/>
					<xsl:apply-templates select="annotationStartDate"/>
					<xsl:apply-templates select="annotationEndDate"/>
					<xsl:apply-templates select="sizePerAnnotation"/>
					<xsl:apply-templates select="interAnnotatorAggreement"/>
					<xsl:apply-templates select="intraAnnotatorAggreement"/>
					<xsl:apply-templates select="annotator"/>
				</annotationInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="annotationType"/>
					<xsl:apply-templates select="annotatedElements"/>
					<xsl:apply-templates select="annotationStandoff"/>
					<xsl:apply-templates select="segmentationLevel"/>
					<xsl:apply-templates select="annotationFormat"/>
					<xsl:apply-templates select="tagset"/>
					<xsl:apply-templates select="tagsetLanguageId"/>
					<xsl:apply-templates select="conformanceToStandardsBestPractice"/>
					<xsl:apply-templates select="theoreticModel"/>
					<xsl:apply-templates select="annotationManual"/>
					<xsl:apply-templates select="annotationMode"/>
					<xsl:apply-templates select="annotationModeDetails"/>
					<xsl:apply-templates select="annotationTool"/>
					<xsl:apply-templates select="annotationStartDate"/>
					<xsl:apply-templates select="annotationEndDate"/>
					<xsl:apply-templates select="sizePerAnnotation"/>
					<xsl:apply-templates select="interAnnotatorAggreement"/>
					<xsl:apply-templates select="intraAnnotatorAggreement"/>
					<xsl:apply-templates select="annotator"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#102-->	
	
	<xsl:template match="Resource/AudioInfo/AudioAnnotationInfo/annotationType"><!--#103-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<xsl:copy copy-namespaces="no">
					<xsl:choose>
						<xsl:when test="text()='audienceReactions'"><!--
							-->discourseAnnotation-audienceReactions<!--
							--></xsl:when>
						<xsl:when test="text()='semanticAnnotation-Events'"><!--
							-->semanticAnnotation-events<!--
							--></xsl:when>
						<xsl:when test="text()='semanticAnnotation-Events'"><!--
							-->emotionalExpressive<!--
							--></xsl:when>
						<xsl:when test="text()='questionTopicalTarget' "><!--
							-->semanticAnnotation-questionTopicalTarget<!--
							--></xsl:when>
						<xsl:when test="text()='textualEntailment' "><!--
							-->semanticAnnotation-textualEntailment<!--
							--></xsl:when>
						<xsl:when test="text()='speechActs' "><!--
							-->semanticAnnotation-speechActs<!--
							--></xsl:when>
						<xsl:when test="text()='morphosyntacticAnnotation' "><!--
							-->morphosyntacticAnnotation-bPosTagging<!--
							--></xsl:when>
						<xsl:when test="text()='morphosyntacticAnnotation-bposTagging' "><!--
							-->morphosyntacticAnnotation-bPosTagging<!--
							--></xsl:when>
						<xsl:when test="text()='PosTagging'"><!--
							-->morphosyntacticAnnotation-posTagging<!--
							--></xsl:when>
						<xsl:when test="text()='coreference'"><!--
							-->discourseAnnotation-coreference<!--
							--></xsl:when>
						<xsl:when test="text()='morphosyntacticAnnotation-bposTagging'"><!--
							-->morphosyntacticAnnotation-bPosTagging<!--
							--></xsl:when>
						<xsl:when test="text()='nounPhrase'"><!--
							-->syntacticAnnotation-shallowParsing<!--
							--></xsl:when>
						<xsl:when test="text()='orthographicTranscription'"><!--
							-->speechAnnotation-orthographicTranscription<!--
							--></xsl:when>
						<xsl:when test="text()='soundToTextAlignment'"><!--
							-->speechAnnotation-soundToTextAlignment<!--
							--></xsl:when>
						<xsl:otherwise>	
   							<xsl:apply-templates select="@*|node()"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:copy>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#103-->	
	
	<xsl:template match="Resource/AudioInfo/AudioAnnotationInfo/annotationManual"><!--#104-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<annotationManual>
					<documentUnstructured>
						<xsl:apply-templates select="@*|node()"/>
					</documentUnstructured>
				</annotationManual>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#104-->	
	
	
	<xsl:template match="Resource/AudioInfo/AudioAnnotationInfo/conformanceToStandardsBestPractice"><!--#105-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<conformanceToStandardsBestPractices>
					<xsl:choose>
						<xsl:when test="text()='PDT'">pragueTreebank</xsl:when>
						<xsl:when test="text()='SYNAF'">SynAF</xsl:when>
						<xsl:when test="text()='EAGLES'">other</xsl:when>
						<xsl:when test="text()='GrAF'">other</xsl:when>
						<xsl:otherwise>	
   							<xsl:apply-templates select="@*|node()"/>
						</xsl:otherwise>
					</xsl:choose>
				</conformanceToStandardsBestPractices>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#105-->	
	
	<xsl:template match="Resource/AudioInfo/AudioAnnotationInfo/annotator"><!--#107-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<annotator>
					<personInfo>
						<xsl:choose>
							<xsl:when test="not(surname)">
							<surname>N/A</surname>
							</xsl:when>
						</xsl:choose>
				
						<xsl:apply-templates select="surname"/>
						<xsl:apply-templates select="givenName"/>
						<xsl:apply-templates select="CommunicationInfo"/>
						<xsl:apply-templates select="position"/>
						<xsl:apply-templates select="affiliation"/>
					</personInfo>
				</annotator>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#107-->	
	
	<xsl:template match="Resource/AudioInfo/AudioRecordingInfo"><!--#108-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<recordingInfo>
					<xsl:apply-templates select="@*|node()[not(self::originalSource or self::recordingMode or self::recordingModeDetails or self::AudioCaptureInfo)]"/>
				</recordingInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#108-->	
	
	
	<xsl:template match="Resource/AudioInfo/AudioRecordingInfo/recordingDeviceType"><!--#109-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<recordingDeviceType>
					<xsl:choose>
						<xsl:when test="text()='hardDiskRecorder'">hardDisk</xsl:when>
						<xsl:when test="text()='analogCassetteRecorder'">other</xsl:when>
						<xsl:when test="text()='digitalAudioTapeRecorder'">other</xsl:when>
						<xsl:when test="text()='minidiskRecorder' or text()='cdRecorder' or text()='pcCard'">other</xsl:when>
						<xsl:otherwise>	
   							<xsl:apply-templates select="@*|node()"/>
						</xsl:otherwise>
					</xsl:choose>
				</recordingDeviceType>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#109-->	
	
	<xsl:template match="Resource/AudioInfo/AudioRecordingInfo/recordingEnvironment"><!--#110-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<recordingEnvironment>
					<xsl:choose>
						<xsl:when test="text()='car'">inCar</xsl:when>
						<xsl:when test="text()='publicPlace'">closedPublicPlace</xsl:when>
						<xsl:otherwise>	
   							<xsl:apply-templates select="@*|node()"/>
						</xsl:otherwise>
					</xsl:choose>
				</recordingEnvironment>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#110-->	
	
	<xsl:template match="Resource/AudioInfo/AudioRecordingInfo/sourceChannel"><!--#111-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<sourceChannel>
					<xsl:choose>
						<xsl:when test="text()='internet'">other</xsl:when>
						<xsl:when test="text()='radio'">other</xsl:when>
						<xsl:otherwise>	
   							<xsl:apply-templates select="@*|node()"/>
						</xsl:otherwise>
					</xsl:choose>
				</sourceChannel>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#111-->	
	
	<xsl:template match="Resource/AudioInfo/AudioRecordingInfo/recorder"><!--#112-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<recorder>
					<personInfo>
						<xsl:choose>
							<xsl:when test="not(surname)">
							<surname>N/A</surname>
							</xsl:when>
						</xsl:choose>
				
						<xsl:apply-templates select="surname"/>
						<xsl:apply-templates select="givenName"/>
						<xsl:apply-templates select="CommunicationInfo"/>
						<xsl:apply-templates select="position"/>
						<xsl:apply-templates select="affiliation"/>
					</personInfo>
				</recorder>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#112-->	
	
	<!--<xsl:template match="Resource/AudioInfo/AudioRecordingInfo/recorder">#113
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<recorder>
					<personInfo>
					<xsl:choose>
						<xsl:when test="not(PersonInfo) and not(surname)"
								<surname>N/A</surname>
						</xsl:when>
					</xsl:choose>
					<xsl:apply-templates select="@*|node()"/>
					</personInfo>
				</recorder>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>#113-->

	<xsl:template match="Resource/AudioInfo/AudioRecordingInfo/originalSource"><!--#113-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<creationInfo>
					<originalSource>
						<targetResourceNameURI>
							<xsl:apply-templates select="@*|node()"/>
						</targetResourceNameURI>
						
					</originalSource>
					<xsl:apply-templates select="../AudioRecordingInfo/recordingMode"/>
					<xsl:apply-templates select="../AudioRecordingInfo/recordingModeDetails"/>
				</creationInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#113-->
	
	<xsl:template match="Resource/AudioInfo/AudioRecordingInfo/AudioCaptureInfo"><!--#117-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<captureInfo>
					<xsl:apply-templates select="@*|node()"/>
				</captureInfo>
			</xsl:when>
			<xsl:otherwise>
				<captureInfo>
					<xsl:apply-templates select="@*|node()"/>
				</captureInfo>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#117-->

	<xsl:template match="Resource/AudioInfo/AudioRecordingInfo/AudioCaptureInfo/PersonSourceSetInfo"><!--#118-->
		<xsl:choose>
			<xsl:when test="../../../../ContentInfo/resourceType='corpus'">
				<personSourceSetInfo>
					<xsl:apply-templates select="numberOfPersons"/>
					<xsl:apply-templates select="ageOfPersons"/>
					<xsl:apply-templates select="ageRangeStart"/>
					<xsl:apply-templates select="ageRangeEnd"/>
					<xsl:apply-templates select="sexOfPersons"/>
					<xsl:apply-templates select="originOfPersons"/>
					<xsl:apply-templates select="dialectAccentOfPersons"/>
					<xsl:apply-templates select="geographicDistributionOfPersons"/>
					<xsl:apply-templates select="hearingImpairmentOfPersons"/>
					<xsl:apply-templates select="speakingImpairmentOfPersons"/>
					<xsl:apply-templates select="numberOfTrainedSpeakers"/>
					<xsl:apply-templates select="speechInfluences"/>
					<xsl:apply-templates select="ParticipantInfo"/>
				</personSourceSetInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="numberOfPersons"/>
					<xsl:apply-templates select="ageOfPersons"/>
					<xsl:apply-templates select="ageRangeStart"/>
					<xsl:apply-templates select="ageRangeEnd"/>
					<xsl:apply-templates select="sexOfPersons"/>
					<xsl:apply-templates select="originOfPersons"/>
					<xsl:apply-templates select="dialectAccentOfPersons"/>
					<xsl:apply-templates select="geographicDistributionOfPersons"/>
					<xsl:apply-templates select="hearingImpairmentOfPersons"/>
					<xsl:apply-templates select="speakingImpairmentOfPersons"/>
					<xsl:apply-templates select="numberOfTrainedSpeakers"/>
					<xsl:apply-templates select="speechInfluences"/>
					<xsl:apply-templates select="ParticipantInfo"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#118-->

	<xsl:template match="Resource/AudioInfo/AudioRecordingInfo/AudioCaptureInfo/PersonSourceSetInfo/participant"><!--#119-->
		<xsl:choose>
			<xsl:when test="../../../../../ContentInfo/resourceType='corpus'">
				<participantInfo>
					<xsl:apply-templates select="@*|node()"/>
				</participantInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#119-->

	
	<xsl:template match="Resource/TextInfo/LanguageInfo/LanguageVarietyInfo"><!--#133-->
		<xsl:choose>
			<xsl:when test="../../../ContentInfo/resourceType='lexicalConceptualResource'">
				<languageVarietyInfo>
					<xsl:apply-templates select="languageVarietyType"/>
					<xsl:apply-templates select="languageVarietyName"/>
					<xsl:apply-templates select="sizePerLanguageVariety[1]"/>
					<xsl:choose>
						<xsl:when test="not(sizePerLanguageVariety)">
							<sizePerLanguageVariety>
								<size>0</size>
								<sizeUnit>units</sizeUnit>
							</sizePerLanguageVariety>
						</xsl:when>
					</xsl:choose>
				</languageVarietyInfo>
			</xsl:when>
			<xsl:when test="../../../ContentInfo/resourceType='corpus'">
				<languageVarietyInfo>
					<xsl:apply-templates select="languageVarietyType"/>
					<xsl:apply-templates select="languageVarietyName"/>
					<xsl:apply-templates select="sizePerLanguageVariety[1]"/>
					<xsl:choose>
						<xsl:when test="not(sizePerLanguageVariety)">
							<sizePerLanguageVariety>
								<size>0</size>
								<sizeUnit>units</sizeUnit>
							</sizePerLanguageVariety>
						</xsl:when>
					</xsl:choose>
				</languageVarietyInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#133-->


	<xsl:template match="Resource/TextInfo/GeographicCoverageInfo"><!--#142-->
		<xsl:choose>
			<xsl:when test="../../ContentInfo/resourceType='corpus'">
				<geographicCoverageInfo>
					<xsl:apply-templates select="geographicCoverage"/>
					<xsl:apply-templates select="sizePerGeographicCoverage[1]"/>
				</geographicCoverageInfo>
			</xsl:when>
			<xsl:when test="../../ContentInfo/resourceType='lexicalConceptualResource'">
				<geographicCoverageInfo>
					<xsl:apply-templates select="geographicCoverage"/>
					<xsl:apply-templates select="sizePerGeographicCoverage[1]"/>
				</geographicCoverageInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
					<xsl:apply-templates select="geographicCoverage"/>
					<xsl:apply-templates select="sizePerGeographicCoverage[1]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#142-->

	<xsl:template match="Resource/VersionInfo"><!--#162 -->
		<versionInfo> <!--#19 -->
			<xsl:for-each select="@*|node()">
				<xsl:choose>
					<xsl:when test="name()='revision'">
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
						<xsl:apply-templates select="../lastDateUpdated"/>
					</xsl:when>
					<xsl:when test="name()='version' and not(../revision)">
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
						<xsl:apply-templates select="../lastDateUpdated"/>
					</xsl:when>
					<xsl:when test="name()='lastDateUpdated'">
					</xsl:when>
					<xsl:otherwise>
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each >
		</versionInfo><!--#19 -->
	</xsl:template><!--#162 -->	
	
	<!--<xsl:template match="Resource/DistributionInfo/LicenseInfo">
		<xsl:copy copy-namespaces="no">
			<xsl:for-each select="@*|node()">
				<xsl:choose>
					<xsl:when test="name()='executionLocation' ">
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
						<xsl:apply-templates select="../price"/>
					</xsl:when>
					<xsl:when test="name()='downloadLocation' and not(../executionLocation)">
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
						<xsl:apply-templates select="../price"/>
					</xsl:when>
					<xsl:when test="name()='distributionAccessMedium' and not(../downloadLocation) and not(../executionLocation)">
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
						<xsl:apply-templates select="../price"/>
					</xsl:when>
					<xsl:when test="name()='restrictionsOfUse' and not(../downloadLocation) and not(../distributionAccessMedium) and not(../executionLocation)">
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
						<xsl:apply-templates select="../price"/>
					</xsl:when>
					<xsl:when test="name()='availability' and not(../downloadLocation) and not(../distributionAccessMedium) and not(../restrictionsOfUse) and not(../executionLocation)">
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
						<xsl:apply-templates select="../price"/>
					</xsl:when>
					<xsl:when test="name()='price'">
					</xsl:when>
					<xsl:otherwise>
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each >
		</xsl:copy>
	</xsl:template>	

	<xsl:template match="Resource/DistributionInfo/LicenseInfo">
		<xsl:copy copy-namespaces="no">
			<xsl:for-each select="@*|node()">
				<xsl:choose>
					<xsl:when test="name()='downloadLocation'">
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
						<xsl:apply-templates select="../executionLocation"/>
					</xsl:when>
					<xsl:when test="name()='distributionAccessMedium' and not(../downloadLocation)">
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
						<xsl:apply-templates select="../executionLocation"/>
					</xsl:when>
					<xsl:when test="name()='restrictionsOfUse' and not(../downloadLocation) and not(../distributionAccessMedium)">
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
						<xsl:apply-templates select="../executionLocation"/>
					</xsl:when>
					<xsl:when test="name()='availability' and not(../downloadLocation) and not(../distributionAccessMedium) and not(../restrictionsOfUse)">
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
						<xsl:apply-templates select="../executionLocation"/>
					</xsl:when>
					<xsl:when test="name()='executionLocation'">
					</xsl:when>
					<xsl:otherwise>
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each >
		</xsl:copy>
	</xsl:template><#164 -->	
	
	<!--<xsl:template match="Resource/UsageInfo/ActualUseInfo"> #172
		<xsl:copy copy-namespaces="no">
			<xsl:for-each select="@*|node()">
				<xsl:choose>
					<xsl:when test="name()='usageProject' ">
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
						<xsl:apply-templates select="../actualUseDetails"/>
					</xsl:when>
					<xsl:when test="name()='derivedResource' and not(../usageProject)">
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
						<xsl:apply-templates select="../actualUseDetails"/>
					</xsl:when>
					<xsl:when test="name()='distributionAccessMedium' and not(../downloadLocation) and not(../executionLocation)">
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
						<xsl:apply-templates select="actualUseDetails"/>
					</xsl:when>
					<xsl:when test="name()='restrictionsOfUse' and not(../downloadLocation) and not(../distributionAccessMedium) and not(../executionLocation)">
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
						<xsl:apply-templates select="actualUseDetails"/>
					</xsl:when>
					<xsl:when test="name()='availability' and not(../downloadLocation) and not(../distributionAccessMedium) and not(../restrictionsOfUse) and not(../executionLocation)">
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
						<xsl:apply-templates select="../price"/>
					</xsl:when>
					<xsl:when test="name()='price'">
					</xsl:when>
					<xsl:otherwise>
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each >
		</xsl:copy>
	</xsl:template>	 #172 -->



	<xsl:template match="//affiliation">
		<xsl:copy copy-namespaces="no">
			<xsl:apply-templates select="OrganizationInfo/organizationName"/>			
			<xsl:apply-templates select="OrganizationInfo/organizationShortName"/>			
			<xsl:apply-templates select="OrganizationInfo/departmentName"/>	
			<xsl:apply-templates select="OrganizationInfo/CommunicationInfo"/>
			<xsl:apply-templates select="@*|node()[not(self::OrganizationInfo)]"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="Resource/ToolServiceInfo/ToolServiceOperationInfo/RunningEnvironmentInfo/requiredSoftware">
		<xsl:copy copy-namespaces="no">
			<targetResourceNameURI>	
				<xsl:apply-templates select="@*|node()"/>
			</targetResourceNameURI>	
		</xsl:copy>
	</xsl:template>

<!--  ##############################################################-->
	<xsl:template match="Resource/ContentInfo">
		<xsl:choose>
			<xsl:when test="../ContentInfo/resourceType='corpus'">
				<resourceComponentType>
					<corpusInfo>
						<resourceType>corpus</resourceType>
						<corpusMediaType>
							<xsl:apply-templates select="../TextInfo"/>	
							<xsl:apply-templates select="../AudioInfo[1]"/>		
						</corpusMediaType>
					</corpusInfo>
				</resourceComponentType>
			</xsl:when>
			<xsl:when test="../ContentInfo/resourceType='lexicalConceptualResource'">
				<resourceComponentType>
						<xsl:apply-templates select="../LexicalConceptualResourceInfo"/>	
				</resourceComponentType>
			</xsl:when>
			<xsl:when test="../ContentInfo/resourceType='technologyToolService'">
				<resourceComponentType>
					<xsl:apply-templates select="../ToolServiceInfo"/>	
				</resourceComponentType>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	
	
		<!--<xsl:copy copy-namespaces="no">
        	<xsl:apply-templates select="child::node()[not(self::resourceType or self::description)]"/>	
    	</xsl:copy>
    	<resourceComponentType>
			<corpusInfo>
				<xsl:apply-templates select="resourceType"/>
				<corpusMediaType>
					<corpusTextInfo>
						<xsl:for-each select="../TextInfo">
							<xsl:apply-templates select="../TextInfo"/>
					</corpusTextInfo>
				</corpusMediaType>
			</corpusInfo>
		</resourceComponentType>-->
	</xsl:template><!--#38 -->









</xsl:stylesheet>
