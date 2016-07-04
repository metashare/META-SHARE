<xsl:stylesheet version="2.0" 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns="http://www.ilsp.gr/META-XMLSchema"
    xmlns:ms="http://www.ilsp.gr/META-XMLSchema"
    exclude-result-prefixes="ms"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 

>
<xsl:output indent="yes" />

	<xsl:template match="@*|node()">
	  <xsl:copy copy-namespaces="no">
		<xsl:apply-templates select="@*|node()"/>
	  </xsl:copy>
	</xsl:template><!--copy all -->

	<xsl:template match="ms:Resource"><!--#1 --><!--#160-->
		<resourceInfo  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.ilsp.gr/META-XMLSchema META-SHARE-Resource.xsd">
			<xsl:apply-templates select="ms:IdentificationInfo"/>
			<xsl:apply-templates select="ms:DistributionInfo"/>
			<xsl:apply-templates select="ms:contactPerson"/>
			<xsl:apply-templates select="ms:MetadataInfo"/>
			<xsl:apply-templates select="ms:VersionInfo"/>
			<xsl:apply-templates select="ms:ValidationInfo"/>
			<xsl:apply-templates select="ms:UsageInfo"/>
			<xsl:apply-templates select="ms:ResourceDocumentationInfo"/>
			<xsl:apply-templates select="ms:ResourceCreationInfo"/>
			<xsl:apply-templates select="ms:ContentInfo"/>	
			<!--<xsl:apply-templates select="@*|node()[not(self::contactPerson or self::TextInfo or self::LexicalConceptualResourceInfo or self::AudioInfo) ]"/>-->
		</resourceInfo>
	</xsl:template><!--#1 -->

	<xsl:template match="ms:Resource/ms:IdentificationInfo"><!--#2 -->
		<identificationInfo>
			<xsl:apply-templates select="ms:resourceName"/>
			<xsl:apply-templates select="../ms:ContentInfo/ms:description"/>
			<xsl:apply-templates select="ms:resourceShortName"/>
			<xsl:apply-templates select="ms:url"/>
			<metaShareId>
				NOT_DEFINED_FOR_V2
	  		</metaShareId>
			<xsl:apply-templates select="ms:identifier"/>
		</identificationInfo>
	</xsl:template><!--#2 -->

	<xsl:template match="ms:Resource/ms:IdentificationInfo/ms:url"><!--#3 -->
	  	<xsl:copy copy-namespaces="no">
			<xsl:apply-templates select="@*|node()"/>
	  	</xsl:copy>
		
	</xsl:template><!--#3 -->

	<xsl:template match="ms:Resource/ms:IdentificationInfo/ms:pid"><!--#4 -->
	</xsl:template><!--#4 -->

	<xsl:template match="ms:Resource/ms:DistributionInfo"><!--#5 -->
		<distributionInfo>
			<xsl:apply-templates select="ms:availability"/>
			<xsl:apply-templates select="ms:LicenseInfo"/>
			<xsl:apply-templates select="ms:iprHolder"/>
			<xsl:apply-templates select="ms:LicenseInfo[1]/ms:availabilityEndDate"/>
			<xsl:apply-templates select="ms:LicenseInfo[1]/ms:availabilityStartDate"/>
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
	<xsl:template match="ms:Resource/ms:contactPerson"><!--#161 -->
		<contactPerson>
			<xsl:choose>
				<xsl:when test="not(ms:surname)">
					<surname>N/A</surname>
				</xsl:when>
			</xsl:choose>	
			<xsl:apply-templates select="ms:surname"/>
			<xsl:apply-templates select="ms:givenName"/>
			<xsl:apply-templates select="ms:CommunicationInfo"/>
			<xsl:apply-templates select="ms:position"/>
			<xsl:apply-templates select="ms:affiliation"/>

		</contactPerson>
	</xsl:template><!--#161 -->
	
	<xsl:template match="ms:Resource/ms:MetadataInfo/ms:metadataCreator">
		<xsl:copy copy-namespaces="no">
		<xsl:choose>
				<xsl:when test="not(ms:surname)">
					<surname>N/A</surname>
				</xsl:when>
			</xsl:choose>	
			<xsl:apply-templates select="ms:surname"/>
			<xsl:apply-templates select="ms:givenName"/>
			<xsl:apply-templates select="ms:CommunicationInfo"/>
			<xsl:apply-templates select="ms:position"/>
			<xsl:apply-templates select="ms:affiliation"/>
		</xsl:copy>
	</xsl:template><!--#17 -->	

	<xsl:template match="ms:Resource/ms:DistributionInfo/ms:LicenseInfo/ms:licenseSignatory"><!--#13 -->
		<licensor>
			<xsl:apply-templates select="@*|node()"/>	
		</licensor>
	</xsl:template><!--#13 -->

	<xsl:template match="ms:Resource/ms:DistributionInfo/ms:LicenseInfo/ms:distributor"><!--#14 -->
		<distributionRightsHolder>
			<xsl:apply-templates select="@*|node()"/>	
		</distributionRightsHolder>
	</xsl:template><!--#14 -->

	<xsl:template match="ms:Resource/ms:MetadataInfo"><!--#16 -->
		<metadataInfo>
			<xsl:choose>
				<xsl:when test="not(ms:metadataCreationDate)">
					<metadataCreationDate>2011-12-31</metadataCreationDate>
				</xsl:when>
			</xsl:choose>
			<xsl:apply-templates select="ms:metadataCreationDate"/>
			<xsl:apply-templates select="ms:metadataCreator"/>	
			<xsl:apply-templates select="ms:source"/>
			<xsl:apply-templates select="ms:originalMetadataSchema[1]"/>
			<xsl:apply-templates select="ms:originalMetadataLink"/>	
			<xsl:apply-templates select="ms:metadataLanguageName"/>
			<xsl:apply-templates select="ms:metadataLanguage"/>
			<xsl:apply-templates select="ms:metadataLastDateUpdated"/>	
			<xsl:apply-templates select="ms:revision"/>		
		</metadataInfo>
	</xsl:template><!--#16 -->
	
	<xsl:template match="ms:Resource/ms:MetadataInfo/ms:metadataLanguage"><!--#186 -->
		<metadataLanguageId>
			<xsl:apply-templates select="@*|node()"/>
		</metadataLanguageId>
	</xsl:template><!--#186 -->
	
	<xsl:template match="ms:Resource/ms:MetadataInfo/ms:harvestingDate"><!--#18 -->
	</xsl:template><!--#18 -->

	<xsl:template match="ms:Resource/ms:ValidationInfo"><!--#20 -->
		<validationInfo>
			<xsl:choose>
				<xsl:when test="not(ms:validated)">
					<validated>true</validated>
				</xsl:when>
			</xsl:choose>
			<xsl:apply-templates select="ms:validated"/>
			<xsl:apply-templates select="ms:validationType"/>
			<xsl:apply-templates select="ms:validationMode"/>
			<xsl:apply-templates select="ms:validationModeDetails"/>
			<xsl:apply-templates select="ms:validationExtent"/>
			<xsl:apply-templates select="ms:validationExtentDetails"/> 
			<xsl:apply-templates select="ms:sizePerValidation"/> 
			<xsl:apply-templates select="ms:validationReport"/>
			<xsl:apply-templates select="ms:validationTool"/>	
			<xsl:apply-templates select="ms:validator"/>               
		</validationInfo><!--#166 -->
	
	</xsl:template><!--#20 -->

	<xsl:template match="ms:Resource/ms:ValidationInfo/ms:validationReport"><!--#22 -->
		<validationReport>
			<documentUnstructured>
				<xsl:apply-templates select="@*|node()"/>
			</documentUnstructured>	
		</validationReport>
	</xsl:template><!--#22 -->

	<xsl:template match="ms:Resource/ms:ValidationInfo/ms:validationTool"><!--#23 -->
		<validationTool>
			<targetResourceNameURI>
				<xsl:apply-templates select="@*|node()"/>
			</targetResourceNameURI>	
		</validationTool>
	</xsl:template><!--#23 -->

	<xsl:template match="ms:Resource/ms:UsageInfo"><!--#24 -->
		<usageInfo>
			<xsl:apply-templates select="@*|node()"/>	
		</usageInfo>
	</xsl:template><!--#24 -->

	<xsl:template match="ms:Resource/ms:UsageInfo/ms:accessTool"><!--#25 -->
		<accessTool>
			<targetResourceNameURI>
				<xsl:apply-templates select="@*|node()"/>
			</targetResourceNameURI>	
		</accessTool>
	</xsl:template><!--#25 -->

	<xsl:template match="ms:Resource/ms:UsageInfo/ms:toolAssociatedWith"><!--#26 -->
		<resourceAssociatedWith>
			<targetResourceNameURI>
				<xsl:apply-templates select="@*|node()"/>
			</targetResourceNameURI>	
		</resourceAssociatedWith>
	</xsl:template><!--#26 -->

	<xsl:template match="ms:Resource/ms:UsageInfo/ms:ForeseenUseInfo"><!--#27 -->
		
			<xsl:choose>
				<xsl:when test="count(ms:foreseenUse)=2">
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

	<xsl:template match="ms:Resource/ms:UsageInfo/ms:ActualUseInfo"><!--#29 -->
		
		<xsl:choose>
				<xsl:when test="count(ms:actualUse)=2">
					<actualUseInfo>
						<xsl:apply-templates select="ms:foreseenUse[1]"/>
					</actualUseInfo>	
					<actualUseInfo>	
						<xsl:apply-templates select="ms:actualUse[2]"/>	
						<xsl:apply-templates select="ms:useNLPSpecific"/>	
						<xsl:apply-templates select="ms:publication"/>	
						<xsl:apply-templates select="ms:outcome"/>	
						<xsl:apply-templates select="ms:usageProject"/>	
						<xsl:apply-templates select="ms:actualUseDetails"/>	
					</actualUseInfo>	
				</xsl:when>
				<xsl:otherwise>
					<actualUseInfo>
						<xsl:apply-templates select="ms:actualUse"/>	
						<xsl:apply-templates select="ms:useNLPSpecific"/>	
						<xsl:apply-templates select="ms:publication"/>	
						<xsl:apply-templates select="ms:outcome"/>	
						<xsl:apply-templates select="ms:usageProject"/>	
						<xsl:apply-templates select="ms:actualUseDetails"/>	
					</actualUseInfo>
				</xsl:otherwise>
			</xsl:choose>
	</xsl:template><!--#29 -->
	
	<xsl:template match="ms:Resource/ms:UsageInfo/ms:ActualUseInfo/ms:usageProject">
		<usageProject>
			<xsl:apply-templates select="ms:projectName"/>
			<xsl:apply-templates select="ms:projectShortName"/>
			<xsl:apply-templates select="ms:projectID"/>
			<xsl:apply-templates select="ms:url"/>
			<xsl:apply-templates select="ms:fundingType"/>
			<xsl:apply-templates select="ms:funder"/>
			<xsl:apply-templates select="ms:fundingCountry"/>
			<xsl:apply-templates select="ms:projectStartDate"/>
			<xsl:apply-templates select="ms:projectEndDate"/>
		</usageProject>
	</xsl:template>
	

	<xsl:template match="ms:Resource/ms:UsageInfo/ms:ActualUseInfo/ms:publication"><!--#31 -->
		<usageReport>
			<documentUnstructured>
				<xsl:apply-templates select="@*|node()"/>
			</documentUnstructured>	
		</usageReport>
	</xsl:template><!--#31 -->

	<xsl:template match="ms:Resource/ms:UsageInfo/ms:ActualUseInfo/ms:outcome"><!--#32 -->
		<derivedResource>
			<targetResourceNameURI>
				<xsl:apply-templates select="@*|node()"/>
			</targetResourceNameURI>	
		</derivedResource>
	</xsl:template><!--#32 -->

	<xsl:template match="ms:Resource/ms:ResourceDocumentationInfo"><!--#33 -->
		<resourceDocumentationInfo>
			<xsl:apply-templates select="ms:publication"/>	
			<xsl:apply-templates select="ms:samplesLocation"/>	
			<xsl:apply-templates select="ms:toolDocumentationType"/>	
		</resourceDocumentationInfo>
	</xsl:template><!--#33 -->

	<xsl:template match="ms:Resource/ms:ResourceDocumentationInfo/ms:publication"><!--#34 -->
		<documentation>
			<documentUnstructured>
				<xsl:apply-templates select="@*|node()"/>
			</documentUnstructured>	
		</documentation>
	</xsl:template><!--#34 -->

	<xsl:template match="ms:Resource/ms:ResourceCreationInfo"><!--#35 -->
		<resourceCreationInfo>
			<xsl:apply-templates select="ms:resourceCreator"/>	
			<xsl:apply-templates select="ms:FundingInfo/ms:ProjectInfo"/>	
			<xsl:apply-templates select="ms:creationStartDate"/>	
			<xsl:apply-templates select="ms:creationEndDate"/>	
		</resourceCreationInfo>
	</xsl:template><!--#35 -->

	<xsl:template match="ms:Resource/ms:LexicalConceptualResourceInfo"><!--#121 -->
			<lexicalConceptualResourceInfo>
				<resourceType>lexicalConceptualResource</resourceType>
				<xsl:apply-templates select="ms:lexicalConceptualResourceType"/>	
				<xsl:apply-templates select="ms:LexicalConceptualResourceEncodingInfo[1]"/>	
				<xsl:apply-templates select="ms:LexicalConceptualResourceCreationInfo[1]"/>		
				<lexicalConceptualResourceMediaType>
					<xsl:apply-templates select="../ms:TextInfo[1]"/>	
				</lexicalConceptualResourceMediaType>
			</lexicalConceptualResourceInfo>	
	</xsl:template><!--#121 -->

	<xsl:template match="ms:Resource/ms:LexicalConceptualResourceInfo/ms:LexicalConceptualResourceCreationInfo"><!--#122 -->
		<creationInfo>
			<xsl:apply-templates select="ms:originalSource"/>
			<xsl:apply-templates select="ms:creationMode"/>	
			<xsl:apply-templates select="ms:creationModeDetails"/>	
			<xsl:apply-templates select="ms:creationTool"/>		
		</creationInfo>
	</xsl:template><!--#122 -->

	<xsl:template match="ms:Resource/ms:LexicalConceptualResourceInfo/ms:LexicalConceptualResourceCreationInfo/ms:originalSource"><!--#123 -->
		<originalSource>
			<targetResourceNameURI>
				<xsl:apply-templates select="@*|node()"/>
			</targetResourceNameURI>	
		</originalSource>
	</xsl:template><!--#123 -->

	<xsl:template match="ms:Resource/ms:LexicalConceptualResourceInfo/ms:LexicalConceptualResourceCreationInfo/ms:creationTool"><!--#124 -->
		<creationTool>
			<targetResourceNameURI>
				<xsl:apply-templates select="@*|node()"/>
			</targetResourceNameURI>	
		</creationTool>
	</xsl:template><!--#124 -->
	
	<xsl:template match="ms:Resource/ms:LexicalConceptualResourceInfo/ms:LexicalConceptualResourceEncodingInfo"><!--#125 -->
		<lexicalConceptualResourceEncodingInfo>
			<xsl:apply-templates select="ms:encodingLevel"/>	
			<xsl:apply-templates select="ms:linguisticInformation"/>	
			<xsl:apply-templates select="ms:conformanceToStandardsBestPractice"/>	
			<xsl:apply-templates select="ms:theoreticModel"/>	
			<xsl:apply-templates select="ms:externalRef"/>	
			<xsl:apply-templates select="ms:extratextualInformation"/>	
			<xsl:apply-templates select="ms:extratextualInformationUnit"/>	
		</lexicalConceptualResourceEncodingInfo>
	</xsl:template><!--#125 -->

	<xsl:template match="ms:Resource/ms:LexicalConceptualResourceInfo/ms:LexicalConceptualResourceEncodingInfo/ms:conformanceToStandardsBestPractice"><!--#126 -->
		<conformanceToStandardsBestPractices>
			<xsl:apply-templates select="@*|node()"/>	
		</conformanceToStandardsBestPractices>
	</xsl:template><!--#126 -->

	<xsl:template match="ms:Resource/ms:ToolServiceInfo"><!--#144 went to the end-->  
		<toolServiceInfo>
			<resourceType>toolService</resourceType>
			<xsl:apply-templates select="@*|node()"/>	
		</toolServiceInfo>
	</xsl:template><!--#144 -->

	<xsl:template match="ms:Resource/ms:ToolServiceInfo/ms:InputInfo"><!--#146 -->
		<inputInfo>
			<xsl:apply-templates select="ms:mediaType[text()!='sensorimotor']"/>	
			<xsl:apply-templates select="ms:resourceType"/>	
			<xsl:apply-templates select="ms:modalityType"/>	
		</inputInfo>
	</xsl:template><!--#146 -->

	<xsl:template match="ms:Resource/ms:ToolServiceInfo/ms:OutputInfo"><!--#147 -->
		<outputInfo>
			<xsl:apply-templates select="ms:mediaType[text()!='sensorimotor']"/>	
			<xsl:apply-templates select="ms:resourceType"/>	
			<xsl:apply-templates select="ms:modalityType"/>	
		</outputInfo>
	</xsl:template><!--#147 -->

	<xsl:template match="ms:Resource/ms:ToolServiceInfo/ms:ToolServiceOperationInfo"><!--#148 -->
		<toolServiceOperationInfo>
			<xsl:apply-templates select="@*|node()"/>	
		</toolServiceOperationInfo>
	</xsl:template><!--#148 -->

	<xsl:template match="ms:Resource/ms:ToolServiceInfo/ms:ToolServiceOperationInfo/ms:RunningEnvironmentInfo"><!--#149 -->
		<runningEnvironmentInfo>
			<xsl:apply-templates select="@*|node()"/>	
		</runningEnvironmentInfo>
	</xsl:template><!--#149 -->

	<xsl:template match="ms:Resource/ms:ToolServiceInfo/ms:ToolServiceOperationInfo/ms:RunningEnvironmentInfo/ms:requiredLRs"><!--#150 -->
		<requiredLRs>
			<targetResourceNameURI>
				<xsl:apply-templates select="@*|node()"/>	
			</targetResourceNameURI>
		</requiredLRs>
	</xsl:template><!--#150 -->

	<xsl:template match="ms:Resource/ms:ToolServiceInfo/ms:ToolServiceEvaluationInfo"><!--#151 -->
		<toolServiceEvaluationInfo>
			<xsl:apply-templates select="@*|node()"/>	
		</toolServiceEvaluationInfo>
	</xsl:template><!--#151 -->

	<xsl:template match="ms:Resource/ms:ToolServiceInfo/ms:ToolServiceEvaluationInfo/ms:evaluationReport"><!--#153 -->
		<evaluationReport>
			<documentUnstructured>
				<xsl:apply-templates select="@*|node()"/>	
			</documentUnstructured>
		</evaluationReport>
	</xsl:template><!--#153 -->

	<xsl:template match="ms:Resource/ms:ToolServiceInfo/ms:ToolServiceEvaluationInfo/ms:evaluationTool"><!--#154 -->
		<evaluationTool>
			<targetResourceNameURI>
				<xsl:apply-templates select="@*|node()"/>	
			</targetResourceNameURI>
		</evaluationTool>
	</xsl:template><!--#154 -->

	<xsl:template match="ms:Resource/ms:ToolServiceInfo/ms:ToolServiceCreationInfo"><!--#155 -->
		<toolServiceCreationInfo>
			<xsl:apply-templates select="@*|node()"/>	
		</toolServiceCreationInfo>
	</xsl:template><!--#155 -->

	<xsl:template match="//ms:OrganizationInfo"><!--#158 -->
		<organizationInfo>
			<xsl:choose>
				<xsl:when test="not(ms:organizationName)">
				<organizationName>N/A</organizationName>					
				</xsl:when>
			</xsl:choose>
			<xsl:apply-templates select="node()"/>
			<xsl:choose>
				<xsl:when test="not(ms:CommunicationInfo)">
					<communicationInfo>
						<email>example@example.com</email>
					</communicationInfo>					
				</xsl:when>
			</xsl:choose>	
		</organizationInfo>
	</xsl:template><!--#158 -->

	<xsl:template match="//ms:CommunicationInfo"><!--#159 -->
		<communicationInfo>
			<xsl:choose>
				<xsl:when test="not(ms:email)">
					<email>example@example.com</email>
				</xsl:when>
			</xsl:choose>
			<xsl:apply-templates select="ms:email"/>
			<xsl:apply-templates select="ms:url"/>
			<xsl:apply-templates select="ms:address"/>
			<xsl:apply-templates select="ms:zipCode"/>
			<xsl:apply-templates select="ms:city"/>
			<xsl:apply-templates select="ms:region"/>
			<xsl:apply-templates select="ms:country"/>
			<xsl:apply-templates select="ms:telephoneNumber"/>
			<xsl:apply-templates select="ms:faxNumber"/>
		</communicationInfo>
	</xsl:template><!--#159 -->

	<xsl:template match="ms:Resource/ms:DistributionInfo/ms:LicenseInfo"><!--#8 ,#9,#7-->
		<licenceInfo>
        	<xsl:apply-templates select="ms:license"/>
        	<xsl:apply-templates select="ms:restrictionsOfUse"/>
        	<xsl:apply-templates select="ms:distributionAccessMedium"/>
        	<xsl:apply-templates select="ms:downloadLocation"/>
        	<xsl:apply-templates select="ms:executionLocation"/>
        	<xsl:apply-templates select="ms:price"/>
        	<xsl:apply-templates select="ms:attributionText"/>
        	<xsl:apply-templates select="ms:licenseSignatory"/>
        	<xsl:apply-templates select="ms:distributor"/>
    	</licenceInfo>
	</xsl:template><!--#8,#9,#7 -->
	
	<xsl:template match="ms:Resource/ms:DistributionInfo/ms:LicenseInfo/ms:restrictionsOfUse[.='informResourceOwner']"><!--#12 -->
		<restrictionsOfUse><!--
			-->informLicensor<!--
		--></restrictionsOfUse>
	</xsl:template>
	<xsl:template match="ms:Resource/ms:DistributionInfo/ms:LicenseInfo/ms:restrictionsOfUse[.='noModifications']">
		<restrictionsOfUse><!--
   			-->other<!--
		--></restrictionsOfUse>
	</xsl:template><!--#12 -->

	<xsl:template match="ms:Resource/ms:DistributionInfo/ms:availability[.='notAvailable']"><!--#6 -->
		<availability><!--
   			-->notAvailableThroughMetaShare<!--
		--></availability>
	</xsl:template><!--#6 -->


	<xsl:template match="ms:Resource/ms:DistributionInfo/ms:LicenseInfo/ms:license"><!--#11-->
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
	

	<xsl:template match="ms:Resource/ms:UsageInfo/ms:ForeseenUseInfo/ms:useNLPSpecific"><!--#28 -->
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
	
	<xsl:template match="ms:Resource/ms:UsageInfo/ms:ActualUseInfo/ms:useNLPSpecific"><!--#30 -->
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
	
	<xsl:template match="ms:Resource/ms:ResourceCreationInfo/ms:FundingInfo"><!--#36 -->
		<xsl:apply-templates select="ms:ProjectInfo"/>
	</xsl:template>
	<xsl:template match="ms:Resource/ms:ResourceCreationInfo/ms:FundingInfo/ms:ProjectInfo">
		<fundingProject>
			<xsl:apply-templates select="ms:projectName"/>
			<xsl:apply-templates select="ms:projectShortName"/>
			<xsl:apply-templates select="ms:projectID"/>
			<xsl:apply-templates select="ms:url"/>
			<xsl:apply-templates select="ms:fundingType"/>
			<xsl:apply-templates select="ms:funder"/>
			<xsl:apply-templates select="ms:fundingCountry"/>
			<xsl:apply-templates select="ms:projectStartDate"/>
			<xsl:apply-templates select="ms:projectEndDate"/>
		</fundingProject>
	</xsl:template><!--#36 -->
	
	<xsl:template match="ms:Resource/ms:UsageInfo/ms:ActualUseInfo/ms:usageProject/ms:fundingType">
		<xsl:choose>
			<xsl:when test="text()='otherFunds'">
				<xsl:copy copy-namespaces="no">other</xsl:copy>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no"><xsl:apply-templates select="@*|node()"/></xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>	
	
	
	<xsl:template match="ms:Resource/ms:ResourceCreationInfo/ms:FundingInfo/ms:ProjectInfo/ms:fundingType">
		<xsl:choose>
			<xsl:when test="text()='otherFunds'">
				<xsl:copy copy-namespaces="no">other</xsl:copy>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no"><xsl:apply-templates select="@*|node()"/></xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>	
	
	
	<xsl:template match="//ms:PersonInfo"><!--#157,#156 -->
		<personInfo>
			<xsl:choose>
				<xsl:when test="not(ms:surname)">
					<surname>N/A</surname>
				</xsl:when>
			</xsl:choose>
			
			<xsl:apply-templates select="ms:surname"/>
			<xsl:apply-templates select="ms:givenName"/>
			<xsl:apply-templates select="ms:CommunicationInfo"/>
			<xsl:apply-templates select="ms:position"/>
			<xsl:apply-templates select="ms:affiliation"/>
		</personInfo>
	</xsl:template><!--#157-->

	<xsl:template match="ms:Resource/ms:ToolServiceInfo/ms:ToolServiceEvaluationInfo[not(ms:evaluated)]"><!--#152-->
		<toolServiceEvaluationInfo>
			<evaluated>TRUE</evaluated>
			<xsl:apply-templates select="@*|node()"/>
		</toolServiceEvaluationInfo>
	</xsl:template><!--#152-->

	<xsl:template match="ms:Resource/ms:ToolServiceInfo[not(ms:languageDependent)]"><!--#145-->
		<resourceComponentType>
			<toolServiceInfo>
				<languageDependent>FALSE</languageDependent>
				<xsl:apply-templates select="@*|node()"/>
			</toolServiceInfo>
		</resourceComponentType>
	</xsl:template><!--#145-->

	<xsl:template match="ms:Resource/ms:TextInfo/ms:SizeInfo/ms:sizeUnit">
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
	<xsl:template match="ms:Resource/ms:TextInfo"><!--#40, #128, #38 -->
		<xsl:choose>
			<xsl:when test="../ms:ContentInfo/ms:resourceType='corpus'">
				<corpusTextInfo>
					<mediaType>text</mediaType>
					<xsl:apply-templates select="ms:LingualityInfo"/>
					<xsl:apply-templates select="ms:LanguageInfo"/>
					<xsl:apply-templates select="ms:LingualityInfo/ms:modalityType"/>
					<xsl:choose>
						<xsl:when test="not(ms:SizeInfo)">
							<sizeInfo>
								<size>0</size>
							</sizeInfo>
						</xsl:when>
					</xsl:choose>
					<xsl:apply-templates select="ms:SizeInfo"/>
					<xsl:apply-templates select="ms:TextFormatInfo"/>
					<xsl:apply-templates select="ms:CharacterEncodingInfo"/>
					<xsl:apply-templates select="ms:AnnotationInfo"/>
					<xsl:apply-templates select="ms:DomainInfo"/>
					<xsl:apply-templates select="ms:TextClassificationInfo"/>
					<xsl:apply-templates select="ms:TimeCoverageInfo"/>
					<xsl:apply-templates select="ms:GeographicCoverageInfo"/>
					<xsl:apply-templates select="ms:TextCreationInfo[1]"/>
				</corpusTextInfo>
			</xsl:when>
			<xsl:when test="../ms:ContentInfo/ms:resourceType='lexicalConceptualResource'">
				<lexicalConceptualResourceTextInfo>
					<xsl:apply-templates select="../ms:ContentInfo/ms:mediaType[text()!='audio' and text()!='video' and text()!='image']"/>
   					<xsl:apply-templates select="ms:LingualityInfo"/>
					<xsl:apply-templates select="ms:LanguageInfo"/>
					<xsl:apply-templates select="ms:LingualityInfo/ms:modalityType"/>
					<xsl:choose>
						<xsl:when test="not(ms:SizeInfo)">
							<sizeInfo>
								<size>0</size>
							</sizeInfo>
						</xsl:when>
					</xsl:choose>
					<xsl:apply-templates select="ms:SizeInfo"/>
					<xsl:apply-templates select="ms:TextFormatInfo"/>
					<xsl:apply-templates select="ms:CharacterEncodingInfo"/>
					<xsl:apply-templates select="ms:DomainInfo"/>
					<xsl:apply-templates select="ms:TimeCoverageInfo"/>
					<xsl:apply-templates select="ms:GeographicCoverageInfo"/>
				</lexicalConceptualResourceTextInfo>
			</xsl:when>
			<xsl:otherwise>	
   				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="../ms:ContentInfo/ms:mediaType"/>
   					<xsl:apply-templates select="ms:LingualityInfo"/>
					<xsl:apply-templates select="ms:LanguageInfo"/>
					<xsl:apply-templates select="ms:LingualityInfo/ms:modalityType"/>
					<xsl:choose>
						<xsl:when test="not(ms:SizeInfo)">
							<sizeInfo>
								<size>0</size>
							</sizeInfo>
						</xsl:when>
					</xsl:choose>
					<xsl:apply-templates select="ms:SizeInfo"/>
					<xsl:apply-templates select="ms:TextFormatInfo"/>
					<xsl:apply-templates select="ms:CharacterEncodingInfo"/>
					<xsl:apply-templates select="ms:DomainInfo"/>
					<xsl:apply-templates select="ms:TimeCoverageInfo"/>
					<xsl:apply-templates select="ms:GeographicCoverageInfo"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#40-->
		
	<xsl:template match="ms:Resource/ms:TextInfo/ms:LingualityInfo"><!--#41 #129-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
				<lingualityInfo>
							<xsl:apply-templates select="@*|node()[not(self::ms:modalityType)]"/>
				</lingualityInfo>
			</xsl:when>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='lexicalConceptualResource'">
				<lingualityInfo>
					<xsl:apply-templates select="@*|node()[not(self::ms:modalityType)]"/>
				</lingualityInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()[not(self::ms:modalityType)]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#41-->		
	
	

	<xsl:template match="ms:Resource/ms:TextInfo/ms:LingualityInfo/ms:modalityType"><!--#42-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='lexicalConceptualResource'">
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
	
	<xsl:template match="ms:Resource/ms:TextInfo/ms:LanguageInfo"><!--#43, #131-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
				<languageInfo>
					<xsl:choose>
						<xsl:when test="not(ms:languageId)">
							<languageId>N/A</languageId>
						</xsl:when>
					</xsl:choose>	
					<xsl:apply-templates select="ms:languageId"/>
					<xsl:apply-templates select="ms:languageName"/>
					<xsl:apply-templates select="ms:languageScript"/>
					<xsl:apply-templates select="ms:sizePerLanguage"/>
					<xsl:apply-templates select="ms:LanguageVarietyInfo"/>
				</languageInfo>
			</xsl:when>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='lexicalConceptualResource'">
				<languageInfo>
					<xsl:choose>
						<xsl:when test="not(ms:languageId)">
							<languageId>N/A</languageId>
						</xsl:when>
					</xsl:choose>	
					<xsl:apply-templates select="ms:languageId"/>
					<xsl:apply-templates select="ms:languageName"/>
					<xsl:apply-templates select="ms:languageScript"/>
					<xsl:apply-templates select="ms:sizePerLanguage"/>
					<xsl:apply-templates select="ms:LanguageVarietyInfo"/>
				</languageInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="ms:languageId"/>
					<xsl:apply-templates select="ms:languageName"/>
					<xsl:apply-templates select="ms:languageScript"/>
					<xsl:apply-templates select="ms:sizePerLanguage"/>
					<xsl:apply-templates select="ms:LanguageVarietyInfo"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#43-->	

	<xsl:template match="ms:Resource/ms:TextInfo/ms:LanguageInfo/ms:languageCoding"><!--#44,#132-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">		
			</xsl:when>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='lexicalConceptualResource'">
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#44-->	

	

	<xsl:template match="ms:Resource/ms:TextInfo/ms:TextCreationInfo"><!--#46-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
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

	<xsl:template match="ms:Resource/ms:TextInfo/ms:TextCreationInfo/ms:originalSource"><!--#47-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	<xsl:template match="ms:Resource/ms:TextInfo/ms:TextCreationInfo/ms:creationTool"><!--#48-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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

	<xsl:template match="ms:Resource/ms:TextInfo/ms:SizeInfo"><!--#49,#134-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
				<sizeInfo>
					<xsl:choose>
							<xsl:when test="not(ms:size)">
								<size>0</size>
							</xsl:when>
					</xsl:choose>
					<xsl:apply-templates select="@*|node()"/>
				</sizeInfo>
			</xsl:when>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='lexicalConceptualResource'">
				<sizeInfo>
					<xsl:choose>
							<xsl:when test="not(ms:size)">
								<size>0</size>
							</xsl:when>
					</xsl:choose>
					<xsl:apply-templates select="@*|node()"/>
				</sizeInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
					<xsl:choose>
							<xsl:when test="not(ms:size)">
								<size>0</size>
							</xsl:when>
						
					</xsl:choose>
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#49-->			

	<xsl:template match="//ms:size"><!--#50-->
		<xsl:choose>
			<xsl:when test="../ms:sizeUnitMultiplier='kilo'">
				<xsl:copy copy-namespaces="no">
					<xsl:value-of select="text()*1000"/>
				</xsl:copy>
			</xsl:when>
			<xsl:when test="../ms:sizeUnitMultiplier='hundred'">
				<xsl:copy copy-namespaces="no">
					<xsl:value-of select="text()*100"/>
				</xsl:copy>
			</xsl:when>
			<xsl:when test="../ms:sizeUnitMultiplier='mega'">
				<xsl:copy copy-namespaces="no">
					<xsl:value-of select="format-number(text()*1000000,'0')"/>
				</xsl:copy>
			</xsl:when>
			<xsl:when test="../ms:sizeUnitMultiplier='tera'">
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

	<xsl:template match="//ms:sizeUnitMultiplier"><!--#51-->
	</xsl:template><!--#51-->

	<xsl:template match="ms:Resource/ms:TextInfo/ms:TextFormatInfo"><!--#52--><!--#135-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
				<textFormatInfo>
					<xsl:apply-templates select= "ms:mime-type[1]"/>
					<xsl:apply-templates select= "ms:sizePerTextFormat[1]"/>
				</textFormatInfo>
			</xsl:when>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='lexicalConceptualResource'">
				<textFormatInfo>
					<xsl:apply-templates select= "ms:mime-type[1]"/>
					<xsl:apply-templates select= "ms:sizePerTextFormat[1]"/>
				</textFormatInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select= "ms:mime-type[1]"/>
					<xsl:apply-templates select= "ms:sizePerTextFormat[1]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#52-->	

	<xsl:template match="ms:Resource/ms:TextInfo/ms:TextFormatInfo/ms:mime-type"><!--#53 #136-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
				<mimeType>
					<xsl:apply-templates select="@*|node()"/>
				</mimeType>
			</xsl:when>
				<xsl:when test="../../../ms:ContentInfo/ms:resourceType='lexicalConceptualResource'">
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
	
	<xsl:template match="ms:Resource/ms:TextInfo/ms:CharacterEncodingInfo"><!--#54,#140-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
				<characterEncodingInfo>
					<xsl:apply-templates select="ms:characterEncoding[1]"/>
				
					<xsl:apply-templates select="ms:sizePerCharacterEncoding[1]"/>
				</characterEncodingInfo>
			</xsl:when>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='lexicalConceptualResource'">
				<characterEncodingInfo>
					<xsl:apply-templates select="ms:characterEncoding[1]"/>
					<xsl:apply-templates select="ms:sizePerCharacterEncoding[1]"/>
				</characterEncodingInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="ms:characterEncoding[1]"/>
   					<xsl:apply-templates select="ms:characterSet"/>
					<xsl:apply-templates select="ms:sizePerCharacterEncoding[1]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#54-->	


	<xsl:template match="ms:Resource/ms:TextInfo/ms:CharacterEncodingInfo/ms:characterSet"><!--#56,#131-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">	
			</xsl:when>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='lexicalConceptualResource'">
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#56-->
	
	<xsl:template match="ms:Resource/ms:TextInfo/ms:CharacterEncodingInfo/ms:characterEncoding"><!--#55-->
	<xsl:copy copy-namespaces="no">
		<xsl:choose>
		
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus' and text()!='US-ASCII' and text()!='windows-1250' and text()!='windows-1251' and text()!='windows-1252' and text()!='windows-1253' and text()!='windows-1254' and text()!='windows-1257' and text()!='ISO-8859-1' and text()!='ISO-8859-2' and text()!='ISO-8859-4' and text()!='ISO-8859-5' and text()!='ISO-8859-7' and text()!='ISO-8859-9' and text()!='ISO-8859-13' and text()!='ISO-8859-15' and text()!='UTF-8' "><!--	
				-->MacDingbat<!--
			--></xsl:when>
				<xsl:when test="../../../ms:ContentInfo/ms:resourceType='lexicalConceptualResource' and text()!='US-ASCII' and text()!='windows-1250' and text()!='windows-1251' and text()!='windows-1252' and text()!='windows-1253' and text()!='windows-1254' and text()!='windows-1257' and text()!='ISO-8859-1' and text()!='ISO-8859-2' and text()!='ISO-8859-4' and text()!='ISO-8859-5' and text()!='ISO-8859-7' and text()!='ISO-8859-9' and text()!='ISO-8859-13' and text()!='ISO-8859-15' and text()!='UTF-8' "><!--	
				-->MacDingbat<!--
			--></xsl:when>
			<xsl:otherwise>
   					<xsl:apply-templates select="@*|node()"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:copy>
	</xsl:template><!--#55 -->	

	<xsl:template match="ms:Resource/ms:TextInfo/ms:DomainInfo"><!--#57-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
				<domainInfo>
					<xsl:apply-templates select="ms:domain"/>
					<xsl:apply-templates select="ms:sizePerDomain[1]"/>
				</domainInfo>
			</xsl:when>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='lexicalConceptualResource'">
				<domainInfo>
					<xsl:apply-templates select="ms:domain"/>
					<xsl:apply-templates select="ms:sizePerDomain[1]"/>
				</domainInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="ms:domain"/>
					<xsl:apply-templates select="ms:sizePerDomain[1]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#57-->	

	<xsl:template match="ms:Resource/ms:TextInfo/ms:TimeCoverageInfo"><!--#58,#141-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
				<timeCoverageInfo>
					<xsl:apply-templates select="ms:timeCoverage"/>
					<xsl:apply-templates select="ms:sizePerTimeCoverage[1]"/>
				</timeCoverageInfo>
			</xsl:when>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='lexicalConceptualResource'">
				<timeCoverageInfo>
					<xsl:apply-templates select="ms:timeCoverage"/>
					<xsl:apply-templates select="ms:sizePerTimeCoverage[1]"/>
				</timeCoverageInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="ms:timeCoverage"/>
					<xsl:apply-templates select="ms:sizePerTimeCoverage[1]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#58-->	

	

	<xsl:template match="ms:Resource/ms:TextInfo/ms:TextClassificationInfo"><!--#60-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
				<textClassificationInfo>
					<xsl:apply-templates select="ms:textGenre"/>
					<xsl:apply-templates select="ms:textType"/>
					<xsl:apply-templates select="ms:register"/>
					<xsl:apply-templates select="ms:subject_Topic"/>
					<xsl:apply-templates select="ms:conformanceToClassificationScheme"/>
					<xsl:apply-templates select="ms:sizePerTextClassification[1]"/>
				</textClassificationInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="ms:textGenre"/>
					<xsl:apply-templates select="ms:textType"/>
					<xsl:apply-templates select="ms:register"/>
					<xsl:apply-templates select="ms:subject_Topic"/>
					<xsl:apply-templates select="ms:conformanceToClassificationScheme"/>
					<xsl:apply-templates select="ms:sizePerTextClassification[1]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#60-->	

	<xsl:template match="ms:Resource/ms:TextInfo/ms:TextClassificationInfo/ms:conformanceToClassificationScheme"><!--#61-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	
	
	<xsl:template match="ms:Resource/ms:TextInfo/ms:AnnotationInfo"><!--#62-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
				<annotationInfo>
					<xsl:apply-templates select="ms:annotationType"/>
					<xsl:apply-templates select="ms:annotatedElements"/>
					<xsl:apply-templates select="ms:annotationStandoff"/>
					<xsl:apply-templates select="ms:segmentationLevel"/>
					<xsl:apply-templates select="ms:annotationFormat"/>
					<xsl:apply-templates select="ms:tagset"/>
					<xsl:apply-templates select="ms:tagsetLanguageId"/>
					<xsl:apply-templates select="ms:conformanceToStandardsBestPractice"/>
					<xsl:apply-templates select="ms:theoreticModel"/>
					<xsl:apply-templates select="ms:annotationManual"/>
					<xsl:apply-templates select="ms:annotationMode"/>
					<xsl:apply-templates select="ms:annotationModeDetails"/>
					<xsl:apply-templates select="ms:annotationTool"/>
					<xsl:apply-templates select="ms:annotationStartDate"/>
					<xsl:apply-templates select="ms:annotationEndDate"/>
					<xsl:apply-templates select="ms:sizePerAnnotation"/>
					<xsl:apply-templates select="ms:interAnnotatorAggreement"/>
					<xsl:apply-templates select="ms:intraAnnotatorAggreement"/>
					<xsl:apply-templates select="ms:annotator"/>
					
				</annotationInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="ms:annotationType"/>
					<xsl:apply-templates select="ms:annotatedElements"/>
					<xsl:apply-templates select="ms:annotationStandoff"/>
					<xsl:apply-templates select="ms:segmentationLevel"/>
					<xsl:apply-templates select="ms:annotationFormat"/>
					<xsl:apply-templates select="ms:tagset"/>
					<xsl:apply-templates select="ms:tagsetLanguageId"/>
					<xsl:apply-templates select="ms:conformanceToStandardsBestPractice"/>
					<xsl:apply-templates select="ms:theoreticModel"/>
					<xsl:apply-templates select="ms:annotationManual"/>
					<xsl:apply-templates select="ms:annotationMode"/>
					<xsl:apply-templates select="ms:annotationModeDetails"/>
					<xsl:apply-templates select="ms:annotationTool"/>
					<xsl:apply-templates select="ms:annotationStartDate"/>
					<xsl:apply-templates select="ms:annotationEndDate"/>
					<xsl:apply-templates select="ms:sizePerAnnotation"/>
					<xsl:apply-templates select="ms:interAnnotatorAggreement"/>
					<xsl:apply-templates select="ms:intraAnnotatorAggreement"/>
					<xsl:apply-templates select="ms:annotator"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#62-->	
	
	<xsl:template match="ms:Resource/ms:TextInfo/ms:AnnotationInfo/ms:annotationType"><!--#63-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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

	<xsl:template match="ms:Resource/ms:TextInfo/ms:AnnotationInfo/ms:annotationManual"><!--#64-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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


	<xsl:template match="ms:Resource/ms:TextInfo/ms:AnnotationInfo/ms:conformanceToStandardsBestPractice"><!--#65-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	
	<xsl:template match="ms:Resource/ms:TextInfo/ms:AnnotationInfo/ms:annotationTool"><!--#66-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioAnnotationInfo/ms:annotationTool"><!--#106-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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

	<xsl:template match="ms:Resource/ms:TextInfo/ms:AnnotationInfo/ms:annotator"><!--#67-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
				<annotator>
					<personInfo>
						<xsl:choose>
							<xsl:when test="not(ms:surname)">
							<surname>N/A</surname>
							</xsl:when>
						</xsl:choose>
				
						<xsl:apply-templates select="ms:surname"/>
						<xsl:apply-templates select="ms:givenName"/>
						<xsl:apply-templates select="ms:CommunicationInfo"/>
						<xsl:apply-templates select="ms:position"/>
						<xsl:apply-templates select="ms:affiliation"/>
						
						
						
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
	
	<xsl:template match="ms:Resource/ms:AudioInfo"><!--#69 ,#39b-->
	 	<corpusAudioInfo>
	 		<mediaType>audio</mediaType>
	 		<xsl:apply-templates select="ms:LingualityInfo"/>
	 		<xsl:choose>
	 			<xsl:when test="not(ms:LanguageInfo)">
					<xsl:apply-templates select="../ms:TextInfo/ms:LanguageInfo"/>
	 			</xsl:when>
	 		</xsl:choose>
	 		<xsl:apply-templates select="ms:LanguageInfo"/>
	 		<xsl:apply-templates select="ms:modalityType"/>
	 		<xsl:choose>
	 			<xsl:when test="not(ms:AudioSizeInfo)">
					<audioSizeInfo><sizeInfo><size>0</size><sizeUnit>hours</sizeUnit></sizeInfo></audioSizeInfo>
	 			</xsl:when>
	 		</xsl:choose>
	 		<xsl:apply-templates select="ms:LingualityInfo/ms:modalityType"/>
	 		<xsl:apply-templates select="ms:AudioSizeInfo"/>
	 		<xsl:apply-templates select="ms:AudioContentInfo"/>
	 		<xsl:apply-templates select="ms:AudioSettingInfo"/>
	 		<xsl:apply-templates select="ms:AudioFormatInfo"/>
	 		<xsl:apply-templates select="ms:AudioAnnotationInfo"/>
	 		<xsl:apply-templates select="ms:DomainInfo"/>
	 		<xsl:apply-templates select="ms:TextClassificationInfo"/>
	 		<xsl:apply-templates select="ms:TimeCoverageInfo"/>
	 		<xsl:apply-templates select="ms:GeographicCoverageInfo"/>
	 		<xsl:apply-templates select="ms:AudioclassificationInfo"/>
	 		<xsl:apply-templates select="ms:AudioRecordingInfo"/>
	 		<xsl:apply-templates select="ms:AudioRecordingInfo/ms:AudioCaptureInfo[1]"/>
	 		<xsl:apply-templates select="ms:AudioRecordingInfo/ms:originalSource[1]"/>	
	 	</corpusAudioInfo>
	</xsl:template>

	<xsl:template match="ms:Resource/ms:AudioInfo/ms:LingualityInfo"><!--#70-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
				<lingualityInfo>
					<xsl:apply-templates select="@*|node()[not(self::ms:modalityType)]"/>
				</lingualityInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#70-->	
	
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:LingualityInfo/ms:modalityType"><!--#71-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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
			
			
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:LanguageInfo"><!--#72-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
				<languageInfo>
					<xsl:choose>
						<xsl:when test="not(ms:languageId)">
							<languageId>N/A</languageId>
						</xsl:when>
					</xsl:choose>	
					<xsl:apply-templates select="ms:languageId"/>
					<xsl:apply-templates select="ms:languageName"/>
					<xsl:apply-templates select="ms:languageScript"/>
					<xsl:apply-templates select="ms:sizePerLanguage"/>
					<xsl:apply-templates select="ms:LanguageVarietyInfo"/>
				</languageInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:choose>
						<xsl:when test="not(ms:languageId)">
							<languageId>N/A</languageId>
						</xsl:when>
					</xsl:choose>	
					<xsl:apply-templates select="ms:languageId"/>
					<xsl:apply-templates select="ms:languageName"/>
					<xsl:apply-templates select="ms:languageScript"/>
					<xsl:apply-templates select="ms:sizePerLanguage"/>
					<xsl:apply-templates select="ms:LanguageVarietyInfo"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#72-->	

	<xsl:template match="ms:Resource/ms:AudioInfo/ms:LanguageInfo/ms:languageCoding"><!--#73-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">		
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#73-->

	<xsl:template match="ms:Resource/ms:AudioInfo/ms:LanguageInfo/ms:LanguageVarietyInfo"><!--#74-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
				<languageVarietyInfo>
					<xsl:apply-templates select="ms:languageVarietyType"/>
					<xsl:apply-templates select="ms:languageVarietyName"/>
					<xsl:apply-templates select="ms:sizePerLanguageVariety[1]"/>
					<xsl:choose>
					
						<xsl:when test="not(ms:sizePerLanguageVariety)">
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
   					<xsl:apply-templates select="ms:languageVarietyType"/>
					<xsl:apply-templates select="ms:languageVarietyName"/>
					<xsl:apply-templates select="ms:sizePerLanguageVariety[1]"/>
					<xsl:choose>
						<xsl:when test="not(ms:sizePerLanguageVariety)">
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
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioContentInfo"><!--#75-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
				<audioContentInfo>
					<xsl:apply-templates select="ms:speechItems"/>
					<xsl:apply-templates select="ms:nonSpeechItems"/>
					<xsl:apply-templates select="ms:textualDescription"/>
					<xsl:apply-templates select="../ms:AudioSettingInfo/ms:noiseLevel"/>
					
				</audioContentInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#75-->	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioContentInfo/ms:nonSpeechItems"><!--#76-->
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
	
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioContentInfo/ms:speechItems"><!--#76-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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

	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioSizeInfo"><!--#77-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
				<audioSizeInfo>
					<sizeInfo>
						<xsl:choose>
							<xsl:when test="not(ms:size)">
								<size>0</size>
							</xsl:when>
						</xsl:choose>
						<xsl:apply-templates select="ms:size"/>
						<xsl:apply-templates select="ms:sizeUnit"/>
					</sizeInfo>
						<xsl:apply-templates select="ms:DurationOfEffectiveSpeechInfo"/>
						<xsl:apply-templates select="ms:DurationOfAudioInfo"/>
				</audioSizeInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#77-->	
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioSizeInfo/ms:DurationOfEffectiveSpeechInfo"><!--#78-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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

	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioSizeInfo/ms:DurationOfEffectiveSpeechInfo/ms:sizeUnit"><!--#79-->
		<xsl:choose>
			<xsl:when test="../../../../ms:ContentInfo/ms:resourceType='corpus'">
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

	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioSizeInfo/ms:DurationOfAudioInfo"><!--#80-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioSizeInfo/ms:DurationOfAudioInfo/ms:sizeUnit"><!--#81-->
		<xsl:choose>
			<xsl:when test="../../../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioFormatInfo"><!--#82-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
				<audioFormatInfo>
					<xsl:apply-templates select="ms:mime-type[1]"/>
					<xsl:apply-templates select="ms:signalEncoding"/>
					<xsl:apply-templates select="ms:samplingRate"/>
					<xsl:apply-templates select="ms:quantization"/>
					<xsl:apply-templates select="ms:byteOrder"/>
					<xsl:apply-templates select="ms:signConvention"/>
					<xsl:apply-templates select="ms:compression"/>
					<xsl:apply-templates select="ms:audioQualityMeasuresIncluded"/>
					<xsl:apply-templates select="ms:numberOfTracks"/>
					<xsl:apply-templates select="ms:recordingQuality"/>
					<xsl:apply-templates select="ms:sizePerAudioFormat[1]"/>
				</audioFormatInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="ms:mime-type[1]"/>
					<xsl:apply-templates select="ms:signalEncoding"/>
					<xsl:apply-templates select="ms:samplingRate"/>
					<xsl:apply-templates select="ms:quantization"/>
					<xsl:apply-templates select="ms:byteOrder"/>
					<xsl:apply-templates select="ms:signConvention"/>
					<xsl:apply-templates select="ms:compression"/>
					<xsl:apply-templates select="ms:audioQualityMeasuresIncluded"/>
					<xsl:apply-templates select="ms:numberOfTracks"/>
					<xsl:apply-templates select="ms:recordingQuality"/>
					<xsl:apply-templates select="ms:sizePerAudioFormat[1]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#82-->	
	
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioFormatInfo/ms:mime-type"><!--#83-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioFormatInfo/ms:byteOrder"><!--#84-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioFormatInfo/ms:signalEncoding"><!--#84-->
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
		
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioFormatInfo/ms:samplingRate"><!--#84-->
		<xsl:copy copy-namespaces="no">
			<xsl:choose>
				<xsl:when test="text()!='8000' and text()!='16000' and text()!='44100' and text()!='48000' and text()!='9600' ">44100</xsl:when>
				<xsl:otherwise>
					<xsl:apply-templates select="@*|node()"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:copy>
	</xsl:template><!--#84-->	
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioFormatInfo/ms:signConvention"><!--#85-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioFormatInfo/ms:compression"><!--#86-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
				<compressionInfo>
					<compression>
						<xsl:apply-templates select="@*|node()"/>
					</compression>
					<xsl:apply-templates select="../ms:compressionName"/>
					<xsl:apply-templates select="../ms:compressionLoss"/>
					
				</compressionInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#86-->	

	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioFormatInfo/ms:compressionName"><!--#87-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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


	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioFormatInfo/ms:compressionLoss"><!--#88-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioFormatInfo/ms:numberOfTracks"><!--#89-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioSettingInfo"><!--#91-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
				<settingInfo>
					<xsl:apply-templates select="ms:typeOfSituationOfCommunication"/>
					<xsl:apply-templates select="ms:speechSetting[1]"/>
					<xsl:apply-templates select="ms:speechTask[1]"/>
					<xsl:apply-templates select="ms:audience"/>
					<xsl:apply-templates select="ms:interactivity"/>
				</settingInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#91-->	
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioSettingInfo/ms:typeOfSituationOfCommunication"><!--#92-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioSettingInfo/ms:speechSetting"><!--#93-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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

	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioSettingInfo/ms:speechTask"><!--#94-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:DomainInfo"><!--#96-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
				<domainInfo>
					<xsl:apply-templates select="ms:domain"/>
					<xsl:apply-templates select="ms:sizePerDomain[1]"/>
				</domainInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
					<xsl:apply-templates select="ms:domain"/>
					<xsl:apply-templates select="ms:sizePerDomain[1]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#96-->	
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:TimeCoverageInfo"><!--#97-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
				<timeCoverageInfo>
					<xsl:apply-templates select="ms:timeCoverage"/>
					<xsl:apply-templates select="ms:sizePerTimeCoverage[1]"/>
				</timeCoverageInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="ms:timeCoverage"/>
					<xsl:apply-templates select="ms:sizePerTimeCoverage[1]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#97-->	
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:GeographicCoverageInfo"><!--#98-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
				<geographicCoverageInfo>
					<xsl:apply-templates select="ms:geographicCoverage"/>
					<xsl:apply-templates select="ms:sizePerGeographicCoverage[1]"/>
				</geographicCoverageInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="ms:geographicCoverage"/>
					<xsl:apply-templates select="ms:sizePerGeographicCoverage[1]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#98-->	
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioClassificationInfo"><!--#99-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioClassificationInfo/ms:speechGenre"><!--#100-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioClassificationInfo/ms:conformanceToClassificationScheme"><!--#101-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioAnnotationInfo"><!--#102-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
				<annotationInfo>
					<xsl:apply-templates select="ms:annotationType"/>
					<xsl:apply-templates select="ms:annotatedElements"/>
					<xsl:apply-templates select="ms:annotationStandoff"/>
					<xsl:apply-templates select="ms:segmentationLevel"/>
					<xsl:apply-templates select="ms:annotationFormat"/>
					<xsl:apply-templates select="ms:tagset"/>
					<xsl:apply-templates select="ms:tagsetLanguageId"/>
					<xsl:apply-templates select="ms:conformanceToStandardsBestPractice"/>
					<xsl:apply-templates select="ms:theoreticModel"/>
					<xsl:apply-templates select="ms:annotationManual"/>
					<xsl:apply-templates select="ms:annotationMode"/>
					<xsl:apply-templates select="ms:annotationModeDetails"/>
					<xsl:apply-templates select="ms:annotationTool"/>
					<xsl:apply-templates select="ms:annotationStartDate"/>
					<xsl:apply-templates select="ms:annotationEndDate"/>
					<xsl:apply-templates select="ms:sizePerAnnotation"/>
					<xsl:apply-templates select="ms:interAnnotatorAggreement"/>
					<xsl:apply-templates select="ms:intraAnnotatorAggreement"/>
					<xsl:apply-templates select="ms:annotator"/>
				</annotationInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="ms:annotationType"/>
					<xsl:apply-templates select="ms:annotatedElements"/>
					<xsl:apply-templates select="ms:annotationStandoff"/>
					<xsl:apply-templates select="ms:segmentationLevel"/>
					<xsl:apply-templates select="ms:annotationFormat"/>
					<xsl:apply-templates select="ms:tagset"/>
					<xsl:apply-templates select="ms:tagsetLanguageId"/>
					<xsl:apply-templates select="ms:conformanceToStandardsBestPractice"/>
					<xsl:apply-templates select="ms:theoreticModel"/>
					<xsl:apply-templates select="ms:annotationManual"/>
					<xsl:apply-templates select="ms:annotationMode"/>
					<xsl:apply-templates select="ms:annotationModeDetails"/>
					<xsl:apply-templates select="ms:annotationTool"/>
					<xsl:apply-templates select="ms:annotationStartDate"/>
					<xsl:apply-templates select="ms:annotationEndDate"/>
					<xsl:apply-templates select="ms:sizePerAnnotation"/>
					<xsl:apply-templates select="ms:interAnnotatorAggreement"/>
					<xsl:apply-templates select="ms:intraAnnotatorAggreement"/>
					<xsl:apply-templates select="ms:annotator"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#102-->	
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioAnnotationInfo/ms:annotationType"><!--#103-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioAnnotationInfo/ms:annotationManual"><!--#104-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioAnnotationInfo/ms:conformanceToStandardsBestPractice"><!--#105-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioAnnotationInfo/ms:annotator"><!--#107-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
				<annotator>
					<personInfo>
						<xsl:choose>
							<xsl:when test="not(ms:surname)">
							<surname>N/A</surname>
							</xsl:when>
						</xsl:choose>
				
						<xsl:apply-templates select="ms:surname"/>
						<xsl:apply-templates select="ms:givenName"/>
						<xsl:apply-templates select="ms:CommunicationInfo"/>
						<xsl:apply-templates select="ms:position"/>
						<xsl:apply-templates select="ms:affiliation"/>
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
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioRecordingInfo"><!--#108-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
				<recordingInfo>
					<xsl:apply-templates select="@*|node()[not(self::ms:originalSource or self::ms:recordingMode or self::ms:recordingModeDetails or self::ms:AudioCaptureInfo)]"/>
				</recordingInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#108-->	
	
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioRecordingInfo/ms:recordingDeviceType"><!--#109-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioRecordingInfo/ms:recordingEnvironment"><!--#110-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioRecordingInfo/ms:sourceChannel"><!--#111-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
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
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioRecordingInfo/ms:recorder"><!--#112-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
				<recorder>
					<personInfo>
						<xsl:choose>
							<xsl:when test="not(ms:surname)">
							<surname>N/A</surname>
							</xsl:when>
						</xsl:choose>
				
						<xsl:apply-templates select="ms:surname"/>
						<xsl:apply-templates select="ms:givenName"/>
						<xsl:apply-templates select="ms:CommunicationInfo"/>
						<xsl:apply-templates select="ms:position"/>
						<xsl:apply-templates select="ms:affiliation"/>
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

	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioRecordingInfo/ms:originalSource"><!--#113-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
				<creationInfo>
					<originalSource>
						<targetResourceNameURI>
							<xsl:apply-templates select="@*|node()"/>
						</targetResourceNameURI>
						
					</originalSource>
					<xsl:apply-templates select="../ms:AudioRecordingInfo/ms:recordingMode"/>
					<xsl:apply-templates select="../ms:AudioRecordingInfo/ms:recordingModeDetails"/>
				</creationInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="@*|node()"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#113-->
	
	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioRecordingInfo/ms:AudioCaptureInfo"><!--#117-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
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

	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioRecordingInfo/ms:AudioCaptureInfo/ms:PersonSourceSetInfo"><!--#118-->
		<xsl:choose>
			<xsl:when test="../../../../ms:ContentInfo/ms:resourceType='corpus'">
				<personSourceSetInfo>
					<xsl:apply-templates select="ms:numberOfPersons"/>
					<xsl:apply-templates select="ms:ageOfPersons"/>
					<xsl:apply-templates select="ms:ageRangeStart"/>
					<xsl:apply-templates select="ms:ageRangeEnd"/>
					<xsl:apply-templates select="ms:sexOfPersons"/>
					<xsl:apply-templates select="ms:originOfPersons"/>
					<xsl:apply-templates select="ms:dialectAccentOfPersons"/>
					<xsl:apply-templates select="ms:geographicDistributionOfPersons"/>
					<xsl:apply-templates select="ms:hearingImpairmentOfPersons"/>
					<xsl:apply-templates select="ms:speakingImpairmentOfPersons"/>
					<xsl:apply-templates select="ms:numberOfTrainedSpeakers"/>
					<xsl:apply-templates select="ms:speechInfluences"/>
					<xsl:apply-templates select="ms:ParticipantInfo"/>
				</personSourceSetInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
   					<xsl:apply-templates select="ms:numberOfPersons"/>
					<xsl:apply-templates select="ms:ageOfPersons"/>
					<xsl:apply-templates select="ms:ageRangeStart"/>
					<xsl:apply-templates select="ms:ageRangeEnd"/>
					<xsl:apply-templates select="ms:sexOfPersons"/>
					<xsl:apply-templates select="ms:originOfPersons"/>
					<xsl:apply-templates select="ms:dialectAccentOfPersons"/>
					<xsl:apply-templates select="ms:geographicDistributionOfPersons"/>
					<xsl:apply-templates select="ms:hearingImpairmentOfPersons"/>
					<xsl:apply-templates select="ms:speakingImpairmentOfPersons"/>
					<xsl:apply-templates select="ms:numberOfTrainedSpeakers"/>
					<xsl:apply-templates select="ms:speechInfluences"/>
					<xsl:apply-templates select="ms:ParticipantInfo"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#118-->

	<xsl:template match="ms:Resource/ms:AudioInfo/ms:AudioRecordingInfo/ms:AudioCaptureInfo/ms:PersonSourceSetInfo/ms:participant"><!--#119-->
		<xsl:choose>
			<xsl:when test="../../../../../ms:ContentInfo/ms:resourceType='corpus'">
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

	
	<xsl:template match="ms:Resource/ms:TextInfo/ms:LanguageInfo/ms:LanguageVarietyInfo"><!--#133-->
		<xsl:choose>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='lexicalConceptualResource'">
				<languageVarietyInfo>
					<xsl:apply-templates select="ms:languageVarietyType"/>
					<xsl:apply-templates select="ms:languageVarietyName"/>
					<xsl:apply-templates select="ms:sizePerLanguageVariety[1]"/>
					<xsl:choose>
						<xsl:when test="not(ms:sizePerLanguageVariety)">
							<sizePerLanguageVariety>
								<size>0</size>
								<sizeUnit>units</sizeUnit>
							</sizePerLanguageVariety>
						</xsl:when>
					</xsl:choose>
				</languageVarietyInfo>
			</xsl:when>
			<xsl:when test="../../../ms:ContentInfo/ms:resourceType='corpus'">
				<languageVarietyInfo>
					<xsl:apply-templates select="ms:languageVarietyType"/>
					<xsl:apply-templates select="ms:languageVarietyName"/>
					<xsl:apply-templates select="ms:sizePerLanguageVariety[1]"/>
					<xsl:choose>
						<xsl:when test="not(ms:sizePerLanguageVariety)">
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


	<xsl:template match="ms:Resource/ms:TextInfo/ms:GeographicCoverageInfo"><!--#142-->
		<xsl:choose>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='corpus'">
				<geographicCoverageInfo>
					<xsl:apply-templates select="ms:geographicCoverage"/>
					<xsl:apply-templates select="ms:sizePerGeographicCoverage[1]"/>
				</geographicCoverageInfo>
			</xsl:when>
			<xsl:when test="../../ms:ContentInfo/ms:resourceType='lexicalConceptualResource'">
				<geographicCoverageInfo>
					<xsl:apply-templates select="ms:geographicCoverage"/>
					<xsl:apply-templates select="ms:sizePerGeographicCoverage[1]"/>
				</geographicCoverageInfo>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy copy-namespaces="no">
					<xsl:apply-templates select="ms:geographicCoverage"/>
					<xsl:apply-templates select="ms:sizePerGeographicCoverage[1]"/>
				</xsl:copy>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template><!--#142-->

	<xsl:template match="ms:Resource/ms:VersionInfo"><!--#162 -->
		<versionInfo> <!--#19 -->
			<xsl:for-each select="@*|node()">
				<xsl:choose>
					<xsl:when test="name()='revision'">
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
						<xsl:apply-templates select="../ms:lastDateUpdated"/>
					</xsl:when>
					<xsl:when test="name()='version' and not(../ms:revision)">
						<xsl:copy copy-namespaces="no">
							<xsl:apply-templates select="@*|node()"/>
						</xsl:copy>
						<xsl:apply-templates select="../ms:lastDateUpdated"/>
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



	<xsl:template match="//ms:affiliation">
		<xsl:copy copy-namespaces="no">
			<xsl:apply-templates select="ms:OrganizationInfo/ms:organizationName"/>			
			<xsl:apply-templates select="ms:OrganizationInfo/ms:organizationShortName"/>			
			<xsl:apply-templates select="ms:OrganizationInfo/ms:departmentName"/>	
			<xsl:apply-templates select="ms:OrganizationInfo/ms:CommunicationInfo"/>
			<xsl:apply-templates select="@*|node()[not(self::ms:OrganizationInfo)]"/>
		</xsl:copy>
	</xsl:template>

	<xsl:template match="ms:Resource/ms:ToolServiceInfo/ms:ToolServiceOperationInfo/ms:RunningEnvironmentInfo/ms:requiredSoftware">
		<xsl:copy copy-namespaces="no">
			<targetResourceNameURI>	
				<xsl:apply-templates select="@*|node()"/>
			</targetResourceNameURI>	
		</xsl:copy>
	</xsl:template>

<!--  ##############################################################-->
	<xsl:template match="ms:Resource/ms:ContentInfo">
		<xsl:choose>
			<xsl:when test="../ms:ContentInfo/ms:resourceType='corpus'">
				<resourceComponentType>
					<corpusInfo>
						<resourceType>corpus</resourceType>
						<corpusMediaType>
							<xsl:apply-templates select="../ms:TextInfo"/>	
							<xsl:apply-templates select="../ms:AudioInfo[1]"/>		
						</corpusMediaType>
					</corpusInfo>
				</resourceComponentType>
			</xsl:when>
			<xsl:when test="../ms:ContentInfo/ms:resourceType='lexicalConceptualResource'">
				<resourceComponentType>
						<xsl:apply-templates select="../ms:LexicalConceptualResourceInfo"/>	
				</resourceComponentType>
			</xsl:when>
			<xsl:when test="../ms:ContentInfo/ms:resourceType='technologyToolService'">
				<resourceComponentType>
					<xsl:apply-templates select="../ms:ToolServiceInfo"/>	
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
