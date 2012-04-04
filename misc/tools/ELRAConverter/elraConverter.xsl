<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="1.0" xmlns:redirect="http://xml.apache.org/xalan/redirect" extension-element-prefixes="redirect" xmlns:xslt="http://xml.apache.org/xsltm" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xs="http://www.w3.org/2001/XMLSchema" exclude-result-prefixes="xs">
    <xsl:output method="xml" encoding="UTF-8" indent="yes" xslt:indent-amount="4"/>
    <xsl:param name="voiceControl" select="/.."/>
    <xsl:template match="/">
        <resourceInfo xmlns="http://www.ilsp.gr/META-XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.ilsp.gr/META-XMLSchema">

            <xsl:for-each select="*[local-name()='root' and namespace-uri()='']/*[local-name()='resource' and namespace-uri()='']">
                <xsl:variable name="var2_cur" select="."/>
                <identificationInfo>
                    <xsl:for-each select="*[local-name()='resource_fullname' and namespace-uri()='']">
                    	<xsl:sort select="./@language"/>
                        <resourceName>                           
                            <xsl:attribute name="lang" namespace="">
                                <xsl:value-of select="./@language"/>
                            </xsl:attribute>                           
                            <xsl:value-of select="string(.)"/>
                        </resourceName>
                    </xsl:for-each>                    
                    <xsl:for-each select="*[local-name()='resource_long_description' and namespace-uri()='']">
                   	<xsl:sort select="./@language"/>
                        <description>                    
                            <xsl:attribute name="lang" namespace="">
                                <xsl:value-of select="./@language"/>
                            </xsl:attribute>                        
                            <xsl:value-of select="string(.)"/>
                        </description>
                    </xsl:for-each>
                    <resourceShortName>                      
                        <xsl:value-of select="string(*[local-name()='resource_shortname' and namespace-uri()=''])"/>
                    </resourceShortName>
                    <metaShareId>NOT_DEFINED_FOR_V2</metaShareId>
                    <xsl:for-each select="*[local-name()='catalogue_item_id' and namespace-uri()='']">
                        <url>
                            <xsl:value-of select="concat('http://catalog.elra.info/product_info.php?products_id=', string(floor(number(string(.)))))"/>
                        </url>
                    </xsl:for-each>
                    <identifier>
                        <xsl:choose>
                            <xsl:when test="descendant::resource_subreference[1] != ''">
                                <xsl:value-of select="concat(descendant::resource_reference, '_', descendant::resource_subreference)"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="string(*[local-name()='resource_reference' and namespace-uri()=''])"/>
                            </xsl:otherwise>
                        </xsl:choose>
                    </identifier>

                    
                </identificationInfo>
               
                <metadataInfo>
                    <metadataCreationDate>2005-05-12</metadataCreationDate>
                    <metadataCreator>
                        <surname lang="en-us">Valérie</surname>
                        <givenName lang="en-us">Mapelli</givenName>
                        <communicationInfo>
                            <email>mapelli@elda.org</email>
                            <url>http://www.elda.org</url>
                            <address>55-57 rue Brillat-Savarin</address>
                            <zipcode>75013</zipcode>
                            <city>Paris</city>
                            <country>France</country>
                            <telephoneNumber>+1 43 13 33 33</telephoneNumber>
                            <faxNumber>+1 43 14 33 30</faxNumber>
                        </communicationInfo>
                    </metadataCreator>
                </metadataInfo>
                <versionInfo>
                    <version>1.0</version>
                    <xsl:variable name='rvh' select="*[local-name()='resource_versionhistory' and namespace-uri()='']"/>
                    <xsl:if test="$rvh!=''">
                        <revision>
                            <xsl:value-of select="$rvh"/>
                        </revision>
                    </xsl:if>
                    <xsl:variable name='rlm' select="*[local-name()='resource_last_modified' and namespace-uri()='']"/>
                    <xsl:if test="$rlm!=''">
                        <lastDateUpdated>
                            <xsl:value-of select="substring($rlm, '0', '11')"/>
                        </lastDateUpdated>
                    </xsl:if>
                </versionInfo>
                
                <distributionInfo>
                    <availability>
                        <xsl:text>available-restrictedUse</xsl:text> 
                    </availability>
		            <xsl:choose>
					<xsl:when test="*[local-name()='pricing_value' and namespace-uri()='']">
				    <!--for each pricing value, take all the direct neighbor info-->
				    <xsl:for-each select="*[local-name()='pricing_value' and namespace-uri()='']">
					    <licenceInfo>
					    <xsl:variable name='abr' select="following-sibling::pricing_abreviation[1]"/>
				
						<xsl:choose>
						<xsl:when test="$abr='A-R' or $abr='C-R' or $abr='Acad.-Reseach'">
							<licence>
							<xsl:text>ELRA_END_USER</xsl:text>
							</licence>
							<restrictionsOfUse>
							<xsl:text>academic-nonCommercialUse</xsl:text>
						   	</restrictionsOfUse>
						</xsl:when>
						<xsl:when test="$abr='A-E' or $abr='C-E' or $abr='Acad.-Reseach'">
							<licence>
						        <xsl:text>ELRA_EVALUATION</xsl:text>
						    	</licence>
						    	<restrictionsOfUse>
						        <xsl:text>evaluationUse</xsl:text>
						    	</restrictionsOfUse>
						</xsl:when>
						<xsl:when test="$abr='A-C' or $abr='C-C' or $abr='Acad.-Reseach'">
							<licence>
				                	<xsl:text>ELRA_VAR</xsl:text>
						   	</licence>
						    	<restrictionsOfUse>
						        <xsl:text>commercialUse</xsl:text>
						    	</restrictionsOfUse>
						</xsl:when>
						</xsl:choose>
				
				
						<xsl:variable name="medium" select="string(*[local-name()='tech_distribution_medium' and namespace-uri()=''])"/>
						    <xsl:choose>
						        <xsl:when test="contains($medium, 'CD-ROM')"> 
						            <distributionAccessMedium>
						                <xsl:text>CD-ROM</xsl:text>
						            </distributionAccessMedium>
						        </xsl:when>
						        <xsl:when test="contains($medium, 'DVD')"> 
						            <distributionAccessMedium>
						                <xsl:text>DVD-R</xsl:text>
						            </distributionAccessMedium>
						        </xsl:when>
						        <xsl:when test="contains($medium, 'floppy')"> 
						            <distributionAccessMedium>
						                <xsl:text>other</xsl:text>
						            </distributionAccessMedium>
						        </xsl:when>
						    </xsl:choose>

						<price><xsl:value-of select="string(.)"/></price>
						<xsl:variable name='customerType' select="following-sibling::pricing_category_customer_type[1]"/>
						<userNature><xsl:if test='$customerType="Commercial"'>commercial</xsl:if>
						<xsl:if test='$customerType="Academic"'>academic</xsl:if></userNature>

						<xsl:variable name='customerGroup' select="following-sibling::pricing_category_customer_group[1]"/>

						<membershipInfo>
						<member><xsl:if test='$customerGroup="Member"'>True</xsl:if>
						<xsl:if test='$customerGroup="Non Member"'>False</xsl:if></member>
						<membershipInstitution>ELRA</membershipInstitution>
						</membershipInfo>
					</licenceInfo>
				    </xsl:for-each>
		            </xsl:when>
				    <xsl:otherwise>
					<licenceInfo>
						<licence>ELRA_END_USER</licence>
						<restrictionsOfUse>academic-nonCommercialUse</restrictionsOfUse>
						<price>Please contact us for further information</price>
						<userNature>commercial</userNature>
						<membershipInfo>
							<member>False</member>
							<membershipInstitution>ELRA</membershipInstitution>
						</membershipInfo>
					</licenceInfo>
					<licenceInfo>
						<licence>ELRA_END_USER</licence>
						<restrictionsOfUse>academic-nonCommercialUse</restrictionsOfUse>
						<price>Please contact us for further information</price>
						<userNature>academic</userNature>
						<membershipInfo>
							<member>False</member>
							<membershipInstitution>ELRA</membershipInstitution>
						</membershipInfo>
					</licenceInfo>
					<licenceInfo>
						<licence>ELRA_END_USER</licence>
						<restrictionsOfUse>academic-nonCommercialUse</restrictionsOfUse>
						<price>Please contact us for further information</price>
						<userNature>commercial</userNature>
						<membershipInfo>
							<member>True</member>
							<membershipInstitution>ELRA</membershipInstitution>
						</membershipInfo>
					</licenceInfo>
					<licenceInfo>
						<licence>ELRA_END_USER</licence>
						<restrictionsOfUse>academic-nonCommercialUse</restrictionsOfUse>
						<price>Please contact us for further information</price>
						<userNature>academic</userNature>
						<membershipInfo>
							<member>True</member>
							<membershipInstitution>ELRA</membershipInstitution>
						</membershipInfo>
					</licenceInfo>
					<licenceInfo>
						<licence>ELRA_VAR</licence>
						<restrictionsOfUse>commercialUse</restrictionsOfUse>
						<price>Please contact us for further information</price>
						<userNature>commercial</userNature>
						<membershipInfo>
							<member>False</member>
							<membershipInstitution>ELRA</membershipInstitution>
						</membershipInfo>
					</licenceInfo>					
					<licenceInfo>
						<licence>ELRA_VAR</licence>
						<restrictionsOfUse>commercialUse</restrictionsOfUse>
						<price>Please contact us for further information</price>
						<userNature>academic</userNature>
						<membershipInfo>
							<member>False</member>
							<membershipInstitution>ELRA</membershipInstitution>
						</membershipInfo>
					</licenceInfo>
					<licenceInfo>
						<licence>ELRA_VAR</licence>
						<restrictionsOfUse>commercialUse</restrictionsOfUse>
						<price>Please contact us for further information</price>
						<userNature>commercial</userNature>
						<membershipInfo>
							<member>True</member>
							<membershipInstitution>ELRA</membershipInstitution>
						</membershipInfo>
					</licenceInfo>
					<licenceInfo>
						<licence>ELRA_VAR</licence>
						<restrictionsOfUse>commercialUse</restrictionsOfUse>
						<price>Please contact us for further information</price>
						<userNature>academic</userNature>
						<membershipInfo>
							<member>True</member>
							<membershipInstitution>ELRA</membershipInstitution>
						</membershipInfo>
					</licenceInfo>
				    </xsl:otherwise>
		            </xsl:choose>
		            
<!--
                    <xsl:if test="'A-R' = *[local-name()='pricing_abreviation' and namespace-uri()=''] or 'C-R' = *[local-name()='pricing_abreviation' and namespace-uri()=''] or 'Acad.-Reseach' = *[local-name()='pricing_abreviation' and namespace-uri()='']">
                        <licenceInfo>
                            <licence>
                                <xsl:text>ELRA_END_USER</xsl:text>
                            </licence>
                            <restrictionsOfUse>
                                <xsl:text>academic-nonCommercialUse</xsl:text>
                            </restrictionsOfUse>

                            <xsl:for-each select="*[local-name()='pricing_abreviation' and namespace-uri()='']">
                                <xsl:if test="(string(.)='A-R' or string(.)='C-R' or string(.)='Acad.-Reseach')">
                                    <price>
                                        <xsl:value-of select="preceding-sibling::pricing_category_customer_type[1]"/> org. ELRA <xsl:value-of select="preceding-sibling::pricing_category_customer_group[1]"/>: <xsl:value-of select="preceding-sibling::pricing_value[1]"/>€</price>
                                </xsl:if>
                            </xsl:for-each>
                            <xsl:variable name="medium" select="string(*[local-name()='tech_distribution_medium' and namespace-uri()=''])"/>
                            <xsl:choose>
                                <xsl:when test="contains($medium, 'CD-ROM')"> 
                                    <distributionAccessMedium>
                                        <xsl:text>CD-ROM</xsl:text>
                                    </distributionAccessMedium>
                                </xsl:when>
                                <xsl:when test="contains($medium, 'DVD')"> 
                                    <distributionAccessMedium>
                                        <xsl:text>DVD-R</xsl:text>
                                    </distributionAccessMedium>
                                </xsl:when>
                                <xsl:when test="contains($medium, 'floppy')"> 
                                    <distributionAccessMedium>
                                        <xsl:text>other</xsl:text>
                                    </distributionAccessMedium>
                                </xsl:when>
                            </xsl:choose>
                            <availabilityStartDate>
                                <xsl:value-of select="substring(string(*[local-name()='date_of_availability' and namespace-uri()='']), '0', '11')"/>
                            </availabilityStartDate>
                        </licenceInfo>
                    </xsl:if>
                    <xsl:if test="'A-E' = *[local-name()='pricing_abreviation' and namespace-uri()=''] or 'C-E' = *[local-name()='pricing_abreviation' and namespace-uri()='']">
                        <licenceInfo>
                            <licence>
                                <xsl:text>ELRA_EVALUATION</xsl:text>
                            </licence>
                            <restrictionsOfUse>
                                <xsl:text>evaluationUse</xsl:text>
                            </restrictionsOfUse>
                           
                            <xsl:for-each select="*[local-name()='pricing_abreviation' and namespace-uri()='']">
                                <xsl:if test="string(.)='A-E' or string(.)='C-E'">
                                    <price>
                                        <xsl:value-of select="preceding-sibling::pricing_category_customer_type[1]"/> org. ELRA <xsl:value-of select="preceding-sibling::pricing_category_customer_group[1]"/>: <xsl:value-of select="preceding-sibling::pricing_value[1]"/>€</price>
                                </xsl:if>
                            </xsl:for-each>
                            
                            <xsl:variable name="medium" select="string(*[local-name()='tech_distribution_medium' and namespace-uri()=''])"/>
                            <xsl:choose>
                                <xsl:when test="contains($medium, 'CD-ROM')"> 
                                    <distributionAccessMedium>
                                        <xsl:text>CD-ROM</xsl:text>
                                    </distributionAccessMedium>
                                </xsl:when>
                                <xsl:when test="contains($medium, 'DVD')"> 
                                    <distributionAccessMedium>
                                        <xsl:text>DVD-R</xsl:text>
                                    </distributionAccessMedium>
                                </xsl:when>
                                <xsl:when test="contains($medium, 'floppy')"> 
                                    <distributionAccessMedium>
                                        <xsl:text>other</xsl:text>
                                    </distributionAccessMedium>
                                </xsl:when>
                            </xsl:choose>
                            <availabilityStartDate>
                                <xsl:value-of select="substring(string(*[local-name()='date_of_availability' and namespace-uri()='']), '0', '11')"/>
                            </availabilityStartDate>
                        </licenceInfo>
                    </xsl:if>
                    <xsl:if test="'A-C' = *[local-name()='pricing_abreviation' and namespace-uri()=''] or 'C-C' = *[local-name()='pricing_abreviation' and namespace-uri()='']">
                        <licenceInfo>
                            <licence>
                                <xsl:text>ELRA_VAR</xsl:text>
                            </licence>
                            <restrictionsOfUse>
                                <xsl:text>commercialUse</xsl:text>
                            </restrictionsOfUse>
                            
                            <xsl:for-each select="*[local-name()='pricing_abreviation' and namespace-uri()='']">
                                <xsl:if test="string(.)='A-C' or string(.)='C-C'">
                                    <price>
                                        <xsl:value-of select="preceding-sibling::pricing_category_customer_type[1]"/> org. ELRA <xsl:value-of select="preceding-sibling::pricing_category_customer_group[1]"/>: <xsl:value-of select="preceding-sibling::pricing_value[1]"/>€</price>
                                </xsl:if>
                            </xsl:for-each>
                           
                            <xsl:variable name="medium" select="string(*[local-name()='tech_distribution_medium' and namespace-uri()=''])"/>
                            <xsl:choose>
                                <xsl:when test="contains($medium, 'CD-ROM')"> 
                                    <distributionAccessMedium>
                                        <xsl:text>CD-ROM</xsl:text>
                                    </distributionAccessMedium>
                                </xsl:when>
                                <xsl:when test="contains($medium, 'DVD')"> 
                                    <distributionAccessMedium>
                                        <xsl:text>DVD-R</xsl:text>
                                    </distributionAccessMedium>
                                </xsl:when>
                                <xsl:when test="contains($medium, 'floppy')"> 
                                    <distributionAccessMedium>
                                        <xsl:text>other</xsl:text>
                                    </distributionAccessMedium>
                                </xsl:when>
                            </xsl:choose>
                            <availabilityStartDate>
                                <xsl:value-of select="substring(string(*[local-name()='date_of_availability' and namespace-uri()='']), '0', '11')"/>
                            </availabilityStartDate>
                        </licenceInfo>
                    </xsl:if>
                    -->
                    <availabilityStartDate>
                                <xsl:value-of select="substring(string(*[local-name()='date_of_availability' and namespace-uri()='']), '0', '11')"/>
                    </availabilityStartDate>
                </distributionInfo>
                
                
                <xsl:variable name='vsg' select="*[local-name()='valid_specification_guidelines' and namespace-uri()='']"/>
                <xsl:variable name='vp' select="*[local-name()='validation_procedure' and namespace-uri()='']"/>
                <xsl:variable name='vr' select="*[local-name()='validation_report' and namespace-uri()='']"/>

            
            
                <xsl:if test='$vsg!="" or $vr!="" or $vp!=""'>            	
                    <validationInfo>
                        <xsl:if test='$vsg!="" or $vp!="" or $vr!=""'>
                            <validated>True</validated>
                        </xsl:if>
                        <xsl:if test='$vsg!="" or $vp!=""'>   
                            <validationModeDetails>
                                <xsl:value-of select="concat($vsg, ' ', $vp)"/>
                            </validationModeDetails>                        
                        </xsl:if>
                        <xsl:if test='$vr!=""'> 
                            <validationReport>
                                <xsl:value-of select="$vr"/>
                            </validationReport>
                        </xsl:if>   
                    </validationInfo>
                </xsl:if>
                                
                <xsl:variable name='apppos' select="*[local-name()='application_possible' and namespace-uri()='']"/>
                <xsl:variable name='appex' select="*[local-name()='application_existing' and namespace-uri()='']"/>
                <xsl:variable name='appar' select="*[local-name()='application_area' and namespace-uri()='']"/>
               
                <xsl:if test='$apppos!="" or $appex!="" or $appar!=""'>
                    <usageInfo>
                        <xsl:if test='$apppos!=""'>
                            <foreseenUseInfo>
                                <foreseenUse>nlpApplications</foreseenUse>
                                <useNLPSpecific>                           
                                    <xsl:choose>
                                        <xsl:when test="$apppos='Speech verification#Automatic speech recognition#Voice control'">voiceControl</xsl:when>
                                        <xsl:when test="$apppos='Speech verification#Automatic speech recognition#Voice control' or $apppos='Discourse analysis#Speaker verification#Speech recognition' or $apppos='Automatic speech recognition' or $apppos='Speech recognition#Voice control#Speech verification#Automatic speech recognition#Voice control'">speechRecognition</xsl:when>
                                        <xsl:when test="$apppos='Speech synthesis'">speechSynthesis</xsl:when>
                                    </xsl:choose>
                                </useNLPSpecific>
                            </foreseenUseInfo>
                        </xsl:if>
                    
                        <xsl:if test='$appex!="" or $appar!=""'> 
                            <actualUseInfo>
                                <actualUse>nlpApplications</actualUse>
                                <xsl:if test='$appex!=""'> 
                                    <useNLPSpecific>                            
                                        <xsl:choose>
                                            <xsl:when test="$appex='Spoken dialogue systems' or $appex='Speech synthesis#Automatic speech recognition' or $appex='Speech recognition#Voice control#Speech verification#Automatic speech recognition#Voice control' or $appex='Speech recognition#Lip tracking analysis' or $appex='Speech recognition#Speech synthesis' or $appex='Speech recognition' or $appex='Speaker verification#Speech recognition' or $appex='Speaker identification' or $appex='Language identification#Speaker identification#Speech recognition' or $appex='Automatic speech recognition' or $appex='Lip tracking analysis' or $appex='Speech recognition#Automatic speech recognition#Automatic person recognition'">speechRecognition</xsl:when>
                                            <xsl:when test="$appex='Speech synthesis#Information retrieval' or $appex='Speech synthesis#Automatic speech recognition' or $appex='Speech synthesis' or $appex='Speech recognition#Speech synthesis'">speechSynthesis</xsl:when>
                                            <xsl:when test="$appex='Speech recognition#Voice control'or $appex='Speech recognition#Voice control#Voice control' or $appex='Speech recognition#Voice control#Speech verification#Automatic speech recognition#Voice control'">voiceControl</xsl:when>
                                            <xsl:when test="$appex='Information retrieval'">textMining</xsl:when>
                                        </xsl:choose>
                                    </useNLPSpecific>
                                </xsl:if>
                                <xsl:if test='$appar!=""'> 
                       
                                    <actualUseDetails>
                                        <xsl:value-of select="$appar"/>
                                    </actualUseDetails>
                                </xsl:if>
                            </actualUseInfo>
                        </xsl:if>
                    </usageInfo>
                </xsl:if>
                
                
                <xsl:for-each select="*[local-name()='type' and namespace-uri()='']">                 	 
                    <xsl:if test="string(.)='S'">
                        <resourceDocumentationInfo>
                            <documentation>
                                <documentInfo>	
                                    <documentType>unpublished</documentType>						
                                    <title>
                                        <xsl:value-of select="following-sibling::file_name[1]"/>
                                    </title>				
                                </documentInfo>
                            </documentation>
                            <samplesLocation>
                                <xsl:value-of select="concat('http://catalog.elra.info/product_info.php?action=download&amp;filename=', following-sibling::file_name[1])"/>
                            </samplesLocation>
                        </resourceDocumentationInfo>
                    </xsl:if>
                </xsl:for-each>
                
                
                
                <xsl:variable name='pp' select="*[local-name()='production_project' and namespace-uri()='']"/>   
                <xsl:variable name='pcd' select="*[local-name()='production_creation_date' and namespace-uri()='']"/>    
                <xsl:if  test='$pp!="" or $pcd!=""'>           
                    <resourceCreationInfo>
                        <xsl:if  test='$pp!=""'>   
                            <fundingProject>
                       
                                <projectName>
                                    <xsl:value-of select="$pp"/>
                                </projectName>                            
                                <fundingType>
                                    <xsl:choose>
                            
                                        <xsl:when test="contains($pp, 'AURORA') or contains($pp, 'EMILLE') or contains($pp, 'NetDC')">ownFunds</xsl:when>
                                        <xsl:when test="contains($pp, 'Action de Recherche Concertée ARC A1, Amaryllis') or contains($pp, 'BITS') or contains($pp, 'CELEX') or contains($pp, 'Contribution à la réalisation de corpus') or contains($pp, 'ESTER') or contains($pp, 'EURADIC') or contains($pp, 'EVALDA') or contains($pp, 'ItalWordNet') or contains($pp, 'NEOLOGOS') or contains($pp, 'SmartWeb') or contains($pp, 'TUNA') or contains($pp, 'Vermobil')">nationalFunds</xsl:when>
                                        <xsl:when test="contains($pp, 'ANITA') or contains($pp, 'BABEL') or contains($pp, 'Balkanet') or contains($pp, 'C-ORAL') or contains($pp, 'CHIL') or contains($pp, 'CLEF') or contains($pp, 'COP-58') or contains($pp, 'COST') or contains($pp, 'ESPRIT') or contains($pp, 'EUROM1') or contains($pp, 'EuroWordNet') or contains($pp, 'HIWIRE') or contains($pp, 'STAR') or contains($pp, 'PAROLE') or contains($pp, 'LILA') or contains($pp, 'Language Resources Production') or contains($pp, 'MULTEXT') or contains($pp, 'NEMLAR') or contains($pp, 'ONOMASTICA') or contains($pp, 'Orientel') or contains($pp, 'SALA') or contains($pp, 'SpeechDat') or contains($pp, 'Speecon')">euFunds</xsl:when>
                           <!-- <xsl:when test="contains($pp, 'European Corpus Initiative') or contains($pp, 'International Corpus of English')">-->
                                        <xsl:otherwise>other</xsl:otherwise>
                            <!--</xsl:when>-->
                                    </xsl:choose>
                                </fundingType>
                        
                            </fundingProject>
                        </xsl:if>
                        <xsl:if  test='$pcd!=""'>   
                            <creationEndDate>
                                <xsl:value-of select="concat(substring($pcd, (string-length($pcd) - 3), string-length($pcd)), '-01-01')"/>
                            </creationEndDate>
                        </xsl:if>
                    </resourceCreationInfo>
                </xsl:if>
                
               
                
               
                    <xsl:if test="*[(local-name()='type_speech_corpus' and namespace-uri()='') or (local-name()='type_written_corpus' and namespace-uri()='') or (local-name()='type_video_corpus' and namespace-uri()='')]">
 			<resourceComponentType>
		                <corpusInfo>				
		                    <resourceType>corpus</resourceType>				
					
		                    <corpusMediaType>
		                        <xsl:for-each select="descendant::content_type">

		                            <xsl:if test=".='written'">
		                                <corpusTextInfo>					
		                                    <mediaType>text</mediaType>	
							
		                                    <xsl:variable name='nol' select="preceding-sibling::content_numberoflanguages[1]"/>	
		                                    <xsl:variable name='al' select="following-sibling::alignment[1]"/>
							
		                                    <lingualityInfo>
		                                        <lingualityType>
		                                            <xsl:choose>
		                                                <xsl:when test="$nol='Multilingual'">multilingual</xsl:when>							
		                                                <xsl:when test="$nol='Bilingual'">bilingual</xsl:when>
		                                                <xsl:otherwise>monolingual</xsl:otherwise>
		                                            </xsl:choose>
		                                        </lingualityType>
		                                        <xsl:if test="$al='Parallel'">
		                                            <multilingualityType>parallel</multilingualityType>	
		                                        </xsl:if>	
		                                    </lingualityInfo>
							
		                                    <xsl:variable name="bytesize" select="preceding-sibling::tech_bytesize"/>
		                                    
		                                        <xsl:for-each select="//*[((local-name()='source_language' or local-name()='target_language') and namespace-uri()='')]">
		                                            <xsl:variable name="lang" select="string(.)"/>
		                                            <xsl:if test='$lang!="" and $lang!="NULL"'>
		                                                <xsl:variable name="eng" select="//iso639_1[text()=$lang]/following-sibling::english[1]"/>
								
							<languageInfo>	
		                                                <languageId>
		                                                    <xsl:value-of select="//iso639_1[text()=$lang]/preceding-sibling::iso639_2[1]"/>
		                                                </languageId>	
		                                                <languageName>
								
		                                                    <xsl:value-of select="$eng"/>
		                                                </languageName>	
									
		                                                <xsl:if test="contains($bytesize, 'language')">
		                                                    <sizePerLanguage>
		                                                        <size>2</size>	
		                                                        <sizeUnit>gb</sizeUnit>	
		                                                    </sizePerLanguage>	
		                                                </xsl:if>
									
		                                                <xsl:variable name="a" select="$eng/following-sibling::*[1]"/>
								
		                                                <xsl:variable name="vn" select='following-sibling::language_variety_name'/>
		                                                <xsl:if test="$a=$vn">
		                                                    <languageVarietyInfo>
		                                                        <languageVarietyType>dialect</languageVarietyType>
		                                                        <languageVarietyName>
		                                                            <xsl:value-of select="$vn"/>
		                                                        </languageVarietyName>
		                                                        <sizePerLanguageVariety>
		                                                            <size>2</size>	
		                                                            <sizeUnit>gb</sizeUnit>	
		                                                        </sizePerLanguageVariety>
		                                                    </languageVarietyInfo>
		                                                    <xsl:variable name="oth" select='following-sibling::other'/>
											
										
		                                                    <xsl:if test="$oth!='' ">
		                                                        <languageVarietyInfo>								
		                                                            <languageVarietyName>
		                                                                <xsl:value-of select="$oth"/>
		                                                            </languageVarietyName>								
		                                                            <languageVarietyType>other</languageVarietyType>
		                                                            <sizePerLanguageVariety>
		                                                                <size>2</size>	
		                                                                <sizeUnit>gb</sizeUnit>	
		                                                            </sizePerLanguageVariety>
		                                                        </languageVarietyInfo>
		                                                    </xsl:if>									
		                                                </xsl:if>
		                                                </languageInfo>
		                                            </xsl:if>
		                                        </xsl:for-each>		
		                                    	
							
		                                    <xsl:variable name="size" select='preceding-sibling::tech_bytesize'/>	
		                                    <xsl:if test="$size!=''">							
		                                        <sizeInfo>
		                                            <xsl:choose>
		                                                <xsl:when test='contains($size, "words")'>
		                                                    <xsl:variable name="sz" select="substring-before($size, 'million')"/>
		                                                    <size>
		                                                        <xsl:value-of select="$sz*1000000"/>
		                                                    </size>	
		                                                    <sizeUnit>words</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test='contains($size, "hours")'>
		                                                    <xsl:variable name="sz" select="substring-before($size, ' hours')"/>
		                                                    <size>
		                                                        <xsl:value-of select="substring-after($sz, ' ')"/>
		                                                    </size>	
		                                                    <sizeUnit>hours</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test='contains($size, "minutes")'>
		                                                    <xsl:variable name="sz" select="substring-before($size, ' minutes')"/>
		                                                    <size>
		                                                        <xsl:value-of select="$sz"/>
		                                                    </size>	
		                                                    <sizeUnit>minutes</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test="contains($size, 'language')">
		                                                    <size>2</size>	
		                                                    <sizeUnit>gb</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test="contains($size, 'Mo') or contains($size, 'Mb')">
		                                                    <size>
		                                                        <xsl:value-of select="substring-before($size, ' ')"/>
		                                                    </size>	
		                                                    <sizeUnit>mb</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test="contains($size, 'kb') or contains($size, 'Kb')">
		                                                    <size>
		                                                        <xsl:value-of select="substring-before($size, ' ')"/>
		                                                    </size>	
		                                                    <sizeUnit>kb</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test="contains($size, 'Gb')">
		                                                    <size>
		                                                        <xsl:value-of select="substring-before($size, ' ')"/>
		                                                    </size>		
		                                                    <sizeUnit>gb</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test="contains($size, 'min')">
		                                                    <xsl:variable name="hours" select="substring-before($size, 'h')"/>
		                                                    <xsl:variable name="mins" select="substring-after($size, 'h')"/>
		                                                    <size>
		                                                        <xsl:value-of select="$hours*60+substring-before($mins, 'min')"/>
		                                                    </size>		
		                                                    <sizeUnit>minutes</sizeUnit>	
		                                                </xsl:when>
		                                            </xsl:choose>						
		                                        </sizeInfo>
		                                    </xsl:if>
							
		                                    <xsl:variable name="tff" select='preceding-sibling::tech_fileformat'/>	
		                                    <xsl:if test="$tff!=''">
		                                        <textFormatInfo>								
		                                            <mimeType>
		                                                <xsl:value-of select="$tff"/>
		                                            </mimeType>								
		                                        </textFormatInfo>
		                                    </xsl:if>	
									
		                                    <xsl:variable name="chars" select='preceding-sibling::character_set'/>							
		                                    <xsl:if test="$chars!='' and not(contains($chars, 'SAMPA')) and not(contains($chars, 'EAGLES'))">
		                                        <characterEncodingInfo>								
		                                            <characterEncoding>
		                                                <xsl:choose>
		                                                    <xsl:when test="contains($chars, '8859')">ISO-8859-1</xsl:when>
		                                                    <xsl:when test="contains($chars, 'ASCII')">US-ASCII</xsl:when>
		                                                    <xsl:when test="contains($chars, 'UTF-8') or contains($chars, 'Unicode') or contains($chars, 'UNICODE')">UTF-8</xsl:when>
		                                                </xsl:choose>
		                                            </characterEncoding>
		                                        </characterEncodingInfo>	
		                                    </xsl:if>						
							
						
		                                    <xsl:variable name="theory" select='following-sibling::theory[1]'/>	
		                                    <xsl:variable name="scheme" select='following-sibling::annotation_scheme[1]'/>	
		                                    <xsl:variable name="mode" select='following-sibling::annotation_mode[1]'/>	
		                                    <xsl:variable name="coverage" select='following-sibling::annotation_coverage[1]'/>	
						
						
		                                    <xsl:if test="$theory!='' or $scheme!='' or $mode!='' or ($coverage!='' and $coverage!='None') or contains($chars, 'SAMPA') or contains($chars, 'EAGLES')">
		                                        <annotationInfo>
		                                            <annotationType>other</annotationType>
		                                            <xsl:if test="contains($chars, 'SAMPA') or contains($chars, 'EAGLES')">						
		                                                <tagset>
		                                                    <xsl:value-of select="$chars"/>
		                                                </tagset>
		                                            </xsl:if>
		                                            <xsl:if test="$theory!=''">						
		                                                <theoreticModel>
		                                                    <xsl:value-of select="$theory"/>
		                                                </theoreticModel>
		                                            </xsl:if>
		                                            <xsl:if test="$scheme!=''">	
		                                                <conformanceToStandardsBestPractices>
		                                                    <xsl:value-of select="$scheme"/>
		                                                </conformanceToStandardsBestPractices>
		                                            </xsl:if>
		                                            <xsl:if test="$mode='Semi automatic' or $mode='Automatic'">	
		                                                <annotationMode>								
		                                                    <xsl:if test="$mode='Semi automatic'">mixed</xsl:if>
		                                                    <xsl:if test="$mode='Automatic'">automatic</xsl:if>
		                                                </annotationMode>
		                                            </xsl:if>
		                                            <xsl:if test="$coverage!='' and $coverage!='None'">	
		                                                <annotationModeDetails>
		                                                    <xsl:value-of select="$coverage"/>
		                                                </annotationModeDetails>
		                                            </xsl:if>
		                                        </annotationInfo>
		                                    </xsl:if>
							
		                                    <xsl:variable name='aa' select="preceding-sibling::application_area[1]"/>
							
		                                    <xsl:if test='$aa!=""'>
		                                        <domainInfo>							
		                                            <domain>
		                                                <xsl:if test="$aa='Tourism'">tourism</xsl:if>
		                                                <xsl:if test="$aa='Training#Research'">science</xsl:if>
		                                            </domain>
		                                        </domainInfo>
		                                    </xsl:if>
							
		                                    <xsl:variable name='time' select='preceding-sibling::resource_periodofcoverage'/>
		                                    <xsl:if test='$time!=""'>
		                                        <timeCoverageInfo>
		                                            <timeCoverage>
		                                                <xsl:value-of select='$time'/>
		                                            </timeCoverage>
		                                        </timeCoverageInfo>
		                                    </xsl:if>
							
		                                    <xsl:variable name='tdm' select="preceding-sibling::tech_development_mode"/>
		                                    <xsl:if test='$tdm!=""'>
		                                        <creationInfo>
							
		                                            <creationMode>
		                                                <xsl:if test="$tdm='Semi Automatic'">mixed</xsl:if>
		                                                <xsl:if test="$tdm='Manual'">manual</xsl:if>
		                                                <xsl:if test="$tdm='Automatic'">automatic</xsl:if>
		                                            </creationMode>
		                                        </creationInfo>
		                                    </xsl:if>
									
		                                </corpusTextInfo>
		                            </xsl:if>
									
					
		                            <xsl:if test=".='speech'">
		                                <corpusAudioInfo>					
		                                    <mediaType>audio</mediaType>	
							
									
		                                    <xsl:variable name='nol' select="preceding-sibling::content_numberoflanguages[1]"/>	
								
		                                    <lingualityInfo>
		                                        <lingualityType>
		                                            <xsl:choose>
		                                                <xsl:when test="$nol='Multilingual'">multilingual</xsl:when>							
		                                                <xsl:when test="$nol='Bilingual'">bilingual</xsl:when>
		                                                <xsl:otherwise>monolingual</xsl:otherwise>
		                                            </xsl:choose>
		                                        </lingualityType>
		                                    </lingualityInfo>
								
								
								
		                                    
		                                        <xsl:for-each select="//*[((local-name()='source_language' or local-name()='target_language') and namespace-uri()='')]">
		                                            <xsl:variable name="lang" select="string(.)"/>
		                                            <xsl:if test='$lang!="" and $lang!="NULL"'>
		                                                <xsl:variable name="eng" select="//iso639_1[text()=$lang]/following-sibling::english[1]"/>
								
							 <languageInfo>
		                                                <languageId>
		                                                    <xsl:value-of select="//iso639_1[text()=$lang]/preceding-sibling::iso639_2[1]"/>
		                                                </languageId>	
		                                                <languageName>
								
		                                                    <xsl:value-of select="$eng"/>
		                                                </languageName>	
								
		                                                <xsl:variable name="a" select="$eng/following-sibling::*[1]"/>
								
		                                                <xsl:variable name="vn" select='following-sibling::language_variety_name'/>
		                                                <xsl:if test="$a=$vn">
		                                                    <languageVarietyInfo>
		                                                        <languageVarietyType>dialect</languageVarietyType>
		                                                        <languageVarietyName>
		                                                            <xsl:value-of select="$vn"/>
		                                                        </languageVarietyName>
		                                                        <sizePerLanguageVariety>
		                                                            <size>2</size>	
		                                                            <sizeUnit>gb</sizeUnit>	
		                                                        </sizePerLanguageVariety>
		                                                    </languageVarietyInfo>
		                                                    <xsl:variable name="oth" select='following-sibling::other'/>
										
		                                                    <xsl:if test="$oth!='' ">
		                                                        <languageVarietyInfo>								
		                                                            <languageVarietyName>
		                                                                <xsl:value-of select="$oth"/>
		                                                            </languageVarietyName>								
		                                                            <languageVarietyType>other</languageVarietyType>
		                                                            <sizePerLanguageVariety>
		                                                                <size>2</size>	
		                                                                <sizeUnit>gb</sizeUnit>	
		                                                            </sizePerLanguageVariety>
		                                                        </languageVarietyInfo>
		                                                    </xsl:if>
		                                                </xsl:if>
		                                                </languageInfo>	
		                                            </xsl:if>
		                                        </xsl:for-each>		
		                                    
							
		                                    <xsl:variable name="size" select='preceding-sibling::tech_bytesize'/>
							
		                                    <xsl:if test="$size!=''">
		                                        <audioSizeInfo>
		                                            <sizeInfo>
		                                                <xsl:choose>
		                                                    <xsl:when test='contains($size, "words")'>
		                                                        <xsl:variable name="sz" select="substring-before($size, 'million')"/>
		                                                        <size>
		                                                            <xsl:value-of select="$sz*1000000"/>
		                                                        </size>	
		                                                        <sizeUnit>words</sizeUnit>	
		                                                    </xsl:when>
		                                                    <xsl:when test='contains($size, "hours")'>
		                                                        <xsl:variable name="sz" select="substring-before($size, ' hours')"/>
		                                                        <size>
		                                                            <xsl:value-of select="substring-after($sz, ' ')"/>
		                                                        </size>	
		                                                        <sizeUnit>hours</sizeUnit>	
		                                                    </xsl:when>
		                                                    <xsl:when test='contains($size, "minutes")'>
		                                                        <xsl:variable name="sz" select="substring-before($size, ' minutes')"/>
		                                                        <size>
		                                                            <xsl:value-of select="$sz"/>
		                                                        </size>	
		                                                        <sizeUnit>minutes</sizeUnit>	
		                                                    </xsl:when>
		                                                    <xsl:when test="contains($size, 'language')">
		                                                        <size>2</size>	
		                                                        <sizeUnit>gb</sizeUnit>	
		                                                    </xsl:when>
		                                                    <xsl:when test="contains($size, 'Mo') or contains($size, 'Mb')">
		                                                        <size>
		                                                            <xsl:value-of select="substring-before($size, ' ')"/>
		                                                        </size>	
		                                                        <sizeUnit>mb</sizeUnit>	
		                                                    </xsl:when>
		                                                    <xsl:when test="contains($size, 'kb') or contains($size, 'Kb')">
		                                                        <size>
		                                                            <xsl:value-of select="substring-before($size, ' ')"/>
		                                                        </size>	
		                                                        <sizeUnit>kb</sizeUnit>	
		                                                    </xsl:when>
		                                                    <xsl:when test="contains($size, 'Gb')">
		                                                        <size>
		                                                            <xsl:value-of select="substring-before($size, ' ')"/>
		                                                        </size>		
		                                                        <sizeUnit>gb</sizeUnit>	
		                                                    </xsl:when>
		                                                    <xsl:when test="contains($size, 'min')">
		                                                        <xsl:variable name="hours" select="substring-before($size, 'h')"/>
		                                                        <xsl:variable name="mins" select="substring-after($size, 'h')"/>
		                                                        <size>
		                                                            <xsl:value-of select="$hours*60+substring-before($mins, 'min')"/>
		                                                        </size>		
		                                                        <sizeUnit>minutes</sizeUnit>	
		                                                    </xsl:when>
		                                                </xsl:choose>						
		                                            </sizeInfo>
		                                        </audioSizeInfo>
		                                    </xsl:if>
														
		                                    <xsl:variable name="theory" select='following-sibling::theory[1]'/>	
		                                    <xsl:variable name="scheme" select='following-sibling::annotation_scheme[1]'/>	
		                                    <xsl:variable name="mode" select='following-sibling::annotation_mode[1]'/>	
		                                    <xsl:variable name="coverage" select='following-sibling::annotation_coverage[1]'/>	
						
						
		                                    <xsl:if test="$theory!='' or $scheme!='' or $mode!='' or ($coverage!='' and $coverage!='None')">
		                                        <annotationInfo>
		                                            <annotationType>other</annotationType>
		                                            <xsl:if test="$theory!=''">						
		                                                <theoreticModel>
		                                                    <xsl:value-of select="$theory"/>
		                                                </theoreticModel>
		                                            </xsl:if>
		                                            <xsl:if test="$scheme!=''">	
		                                                <conformanceToStandardsBestPractices>
		                                                    <xsl:value-of select="$scheme"/>
		                                                </conformanceToStandardsBestPractices>
		                                            </xsl:if>
		                                            <xsl:if test="$mode='Semi automatic' or $mode='Automatic'">	
		                                                <annotationMode>								
		                                                    <xsl:if test="$mode='Semi automatic'">mixed</xsl:if>
		                                                    <xsl:if test="$mode='Automatic'">automatic</xsl:if>
		                                                </annotationMode>
		                                            </xsl:if>
		                                            <xsl:if test="$coverage!='' and $coverage!='None'">	
		                                                <annotationModeDetails>
		                                                    <xsl:value-of select="$coverage"/>
		                                                </annotationModeDetails>
		                                            </xsl:if>
		                                        </annotationInfo>
		                                    </xsl:if>
									
								
		                                    <xsl:variable name='aa' select="preceding-sibling::application_area[1]"/>
										
		                                    <xsl:if test='$aa!=""'>
		                                        <domainInfo>							
		                                            <domain>
		                                                <xsl:if test="$aa='Tourism'">tourism</xsl:if>
		                                                <xsl:if test="$aa='Training#Research'">science</xsl:if>
		                                            </domain>
		                                        </domainInfo>
		                                    </xsl:if>
								
								
		                                    <xsl:variable name='time' select='preceding-sibling::resource_periodofcoverage'/>
								
		                                    <xsl:if test='$time!=""'>
		                                        <timeCoverageInfo>
		                                            <timeCoverage>
		                                                <xsl:value-of select='$time'/>
		                                            </timeCoverage>
		                                        </timeCoverageInfo>
		                                    </xsl:if>
								
		                                    <xsl:variable name='tdm' select="preceding-sibling::tech_development_mode"/>
		                                    <xsl:if test='$tdm!=""'>
		                                        <creationInfo>
		                                            <creationMode>
		                                                <xsl:if test="$tdm='Semi Automatic'">mixed</xsl:if>
		                                                <xsl:if test="$tdm='Manual'">manual</xsl:if>
		                                                <xsl:if test="$tdm='Automatic'">automatic</xsl:if>
		                                            </creationMode>
		                                        </creationInfo>
		                                    </xsl:if>
											
		                                </corpusAudioInfo>
		                            </xsl:if>
		                            <xsl:if test=".='video'">
		                                <corpusVideoInfo>					
		                                    <mediaType>video</mediaType>	
							
		                                    <xsl:variable name='nol' select="preceding-sibling::content_numberoflanguages[1]"/>	
															
		                                    <lingualityInfo>
		                                        <lingualityType>
		                                            <xsl:choose>
		                                                <xsl:when test="$nol='Multilingual'">multilingual</xsl:when>							
		                                                <xsl:when test="$nol='Bilingual'">bilingual</xsl:when>
		                                                <xsl:otherwise>monolingual</xsl:otherwise>
		                                            </xsl:choose>
		                                        </lingualityType>								
		                                    </lingualityInfo>
								
		                                   
		                                        <xsl:for-each select="//*[((local-name()='source_language' or local-name()='target_language') and namespace-uri()='')]">
		                                            <xsl:variable name="lang" select="string(.)"/>
		                                            <xsl:if test='$lang!="" and $lang!="NULL"'>
		                                                <xsl:variable name="eng" select="//iso639_1[text()=$lang]/following-sibling::english[1]"/>
								
							 <languageInfo>
		                                                <languageId>
		                                                    <xsl:value-of select="//iso639_1[text()=$lang]/preceding-sibling::iso639_2[1]"/>
		                                                </languageId>	
		                                                <languageName>
								
		                                                    <xsl:value-of select="$eng"/>
		                                                </languageName>	
								
		                                                <xsl:variable name="a" select="$eng/following-sibling::*[1]"/>
								
		                                                <xsl:variable name="vn" select='following-sibling::language_variety_name'/>
		                                                <xsl:if test="$a=$vn">
		                                                    <languageVarietyInfo>
		                                                        <languageVarietyType>dialect</languageVarietyType>
		                                                        <languageVarietyName>
		                                                            <xsl:value-of select="$vn"/>
		                                                        </languageVarietyName>
		                                                        <sizePerLanguageVariety>
		                                                            <size>2</size>	
		                                                            <sizeUnit>gb</sizeUnit>	
		                                                        </sizePerLanguageVariety>
		                                                    </languageVarietyInfo>
		                                                    <xsl:variable name="oth" select='following-sibling::other'/>
										
		                                                    <xsl:if test="$oth!='' ">
		                                                        <languageVarietyInfo>								
		                                                            <languageVarietyName>
		                                                                <xsl:value-of select="$oth"/>
		                                                            </languageVarietyName>								
		                                                            <languageVarietyType>other</languageVarietyType>
		                                                            <sizePerLanguageVariety>
		                                                                <size>2</size>	
		                                                                <sizeUnit>gb</sizeUnit>	
		                                                            </sizePerLanguageVariety>
		                                                        </languageVarietyInfo>
		                                                    </xsl:if>
		                                                </xsl:if>
		                                                 </languageInfo>	
		                                            </xsl:if>
		                                        </xsl:for-each>		
		                                   
							
		                                    <xsl:variable name="size" select='preceding-sibling::tech_bytesize'/>	
		                                    <xsl:if test="$size!=''">							
		                                        <sizeInfo>
		                                            <xsl:choose>
		                                                <xsl:when test='contains($size, "words")'>
		                                                    <xsl:variable name="sz" select="substring-before($size, 'million')"/>
		                                                    <size>
		                                                        <xsl:value-of select="$sz*1000000"/>
		                                                    </size>	
		                                                    <sizeUnit>words</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test='contains($size, "hours")'>
		                                                    <xsl:variable name="sz" select="substring-before($size, ' hours')"/>
		                                                    <size>
		                                                        <xsl:value-of select="substring-after($sz, ' ')"/>
		                                                    </size>	
		                                                    <sizeUnit>hours</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test='contains($size, "minutes")'>
		                                                    <xsl:variable name="sz" select="substring-before($size, ' minutes')"/>
		                                                    <size>
		                                                        <xsl:value-of select="$sz"/>
		                                                    </size>	
		                                                    <sizeUnit>minutes</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test="contains($size, 'language')">
		                                                    <size>2</size>	
		                                                    <sizeUnit>gb</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test="contains($size, 'Mo') or contains($size, 'Mb')">
		                                                    <size>
		                                                        <xsl:value-of select="substring-before($size, ' ')"/>
		                                                    </size>	
		                                                    <sizeUnit>mb</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test="contains($size, 'kb') or contains($size, 'Kb')">
		                                                    <size>
		                                                        <xsl:value-of select="substring-before($size, ' ')"/>
		                                                    </size>	
		                                                    <sizeUnit>kb</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test="contains($size, 'Gb')">
		                                                    <size>
		                                                        <xsl:value-of select="substring-before($size, ' ')"/>
		                                                    </size>		
		                                                    <sizeUnit>gb</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test="contains($size, 'min')">
		                                                    <xsl:variable name="hours" select="substring-before($size, 'h')"/>
		                                                    <xsl:variable name="mins" select="substring-after($size, 'h')"/>
		                                                    <size>
		                                                        <xsl:value-of select="$hours*60+substring-before($mins, 'min')"/>
		                                                    </size>		
		                                                    <sizeUnit>minutes</sizeUnit>	
		                                                </xsl:when>
		                                            </xsl:choose>						
		                                        </sizeInfo>
		                                    </xsl:if>
							

		                                    <xsl:variable name="theory" select='following-sibling::theory[1]'/>	
		                                    <xsl:variable name="scheme" select='following-sibling::annotation_scheme[1]'/>	
		                                    <xsl:variable name="mode" select='following-sibling::annotation_mode[1]'/>	
		                                    <xsl:variable name="coverage" select='following-sibling::annotation_coverage[1]'/>	
						
						
		                                   <xsl:if test="$theory!='' or $scheme!='' or $mode!='' or ($coverage!='' and $coverage!='None')">
		                                       <annotationInfo>
		                                            <annotationType>other</annotationType>	
		                                            <xsl:if test="$theory!=''">						
		                                                <theoreticModel>
		                                                    <xsl:value-of select="$theory"/>
		                                                </theoreticModel>
		                                            </xsl:if>
		                                            <xsl:if test="$scheme!=''">	
		                                                <conformanceToStandardsBestPractices>
		                                                    <xsl:value-of select="$scheme"/>
		                                                </conformanceToStandardsBestPractices>
		                                            </xsl:if>
		                                            <xsl:if test="$mode='Semi automatic' or $mode='Automatic'">	
		                                                <annotationMode>								
		                                                    <xsl:if test="$mode='Semi automatic'">mixed</xsl:if>
		                                                    <xsl:if test="$mode='Automatic'">automatic</xsl:if>
		                                                </annotationMode>
		                                            </xsl:if>
		                                            <xsl:if test="$coverage!='' and $coverage!='None'">	
		                                                <annotationModeDetails>
		                                                    <xsl:value-of select="$coverage"/>
		                                                </annotationModeDetails>
		                                            </xsl:if>
		                                        </annotationInfo>
		                                    </xsl:if>
								
								
		                                    <xsl:variable name='aa' select="preceding-sibling::application_area[1]"/>
								
		                                    <xsl:if test='$aa!=""'>
		                                        <domainInfo>							
		                                            <domain>
		                                                <xsl:if test="$aa='Tourism'">tourism</xsl:if>
		                                                <xsl:if test="$aa='Training#Research'">science</xsl:if>
		                                            </domain>
		                                        </domainInfo>
		                                    </xsl:if>
								
								
								
		                                    <xsl:variable name='time' select='preceding-sibling::resource_periodofcoverage'/>
		                                    <xsl:if test='$time!=""'>
		                                        <timeCoverageInfo>
		                                            <timeCoverage>
		                                                <xsl:value-of select='$time'/>
		                                            </timeCoverage>
		                                        </timeCoverageInfo>
		                                    </xsl:if>
								
								
		                                    <xsl:variable name='tdm' select="following-sibling::tech_development_mode"/>
		                                    <xsl:if test='$tdm!=""'>
		                                        <creationInfo>
								
		                                            <creationMode>
		                                                <xsl:if test="$tdm='Semi Automatic'">mixed</xsl:if>
		                                                <xsl:if test="$tdm='Manual'">manual</xsl:if>
		                                                <xsl:if test="$tdm='Automatic'">automatic</xsl:if>
		                                            </creationMode>
		                                        </creationInfo>
		                                    </xsl:if>
												
		                                </corpusVideoInfo>
		                            </xsl:if>
		                        </xsl:for-each>	
		                    </corpusMediaType>		
		                    
		                </corpusInfo>
                         </resourceComponentType>
                    </xsl:if>
		 
		 
		 
		 
		 
		 
		 
		 
                    <xsl:if test="*[(local-name()='type_speech_lexicon' and namespace-uri()='') or (local-name()='type_written_lexicon' and namespace-uri()='') or (local-name()='type_written_terminology' and namespace-uri()='')]">
		        
			<resourceComponentType>
			        <lexicalConceptualResourceInfo>
		                    <resourceType>lexicalConceptualResource</resourceType>	
						
		                    <lexicalConceptualResourceType>
		                
		                        <xsl:if test="*[(local-name()='type_speech_lexicon' and namespace-uri()='') or (local-name()='type_written_lexicon' and namespace-uri()='')]">lexicon</xsl:if>
		                        <xsl:if test="*[(local-name()='type_written_terminology' and namespace-uri()='')]">terminologicalResource</xsl:if>
		                    </lexicalConceptualResourceType>
		                    <xsl:variable name='sle' select="descendant::speech_lexicon_entries"/>
		                    <xsl:if test="$sle!=''">
		                        <lexicalConceptualResourceEncodingInfo>		
												
		                            <xsl:if test="$sle='Pronunciation#Orthographic' or $sle='Pronunciation'">
		                                <encodingLevel>phonetics</encodingLevel>
		                            </xsl:if>
		                            <xsl:if test="$sle='Pronunciation#Orthographic' or $sle='Orthographic'">
		                                <encodingLevel>morphology</encodingLevel>
		                            </xsl:if>
														
		                        </lexicalConceptualResourceEncodingInfo>
		                    </xsl:if>	
						
								
		                    <xsl:variable name='tdm' select="descendant::tech_development_mode"/>
		                    <xsl:if test='$tdm!=""'>
		                        <creationInfo>
								
		                            <creationMode>
		                                <xsl:if test="$tdm='Semi Automatic'">mixed</xsl:if>
		                                <xsl:if test="$tdm='Manual'">manual</xsl:if>
		                                <xsl:if test="$tdm='Automatic'">automatic</xsl:if>
		                            </creationMode>
		                        </creationInfo>
		                    </xsl:if>
						
						
					
		                    	
		                    <lexicalConceptualResourceMediaType>
		                        <xsl:for-each select="descendant::content_type">		                            				
		                                <lexicalConceptualResourceTextInfo>					
		                                    <mediaType>text</mediaType>	
						
		                                    <xsl:variable name='nol' select="preceding-sibling::content_numberoflanguages[1]"/>	
		                                    <xsl:variable name='al' select="*[local-name()='alignment' and namespace-uri()='']"/>
							
		                                    <lingualityInfo>
		                                        <lingualityType>
		                                            <xsl:choose>
		                                                <xsl:when test="$nol='Multilingual'">multilingual</xsl:when>							
		                                                <xsl:when test="$nol='Bilingual'">bilingual</xsl:when>
		                                                <xsl:otherwise>monolingual</xsl:otherwise>
		                                            </xsl:choose>
		                                        </lingualityType>
		                                        <xsl:if test="$al='Parallel'">
		                                            <multilingualityType>parallel</multilingualityType>	
		                                        </xsl:if>	
		                                    </lingualityInfo>
						
		                                    
		                                        <xsl:for-each select="//*[((local-name()='source_language' or local-name()='target_language') and namespace-uri()='')]">
		                                            <xsl:variable name="lang" select="string(.)"/>
		                                            <xsl:if test='$lang!="" and $lang!="NULL"'>
		                                                <xsl:variable name="eng" select="//iso639_1[text()=$lang]/following-sibling::english[1]"/>
								
							<languageInfo>
		                                                <languageId>
		                                                    <xsl:value-of select="//iso639_1[text()=$lang]/preceding-sibling::iso639_2[1]"/>
		                                                </languageId>	
		                                                <languageName>
								
		                                                    <xsl:value-of select="$eng"/>
		                                                </languageName>	
								
		                                                <xsl:variable name="a" select="$eng/following-sibling::*[1]"/>
								
		                                                <xsl:variable name="vn" select='following-sibling::language_variety_name'/>
		                                                <xsl:if test="$a=$vn">
		                                                    <languageVarietyInfo>
		                                                        <languageVarietyType>dialect</languageVarietyType>
		                                                        <languageVarietyName>
		                                                            <xsl:value-of select="$vn"/>
		                                                        </languageVarietyName>
		                                                        <sizePerLanguageVariety>
		                                                            <size>2</size>	
		                                                            <sizeUnit>gb</sizeUnit>	
		                                                        </sizePerLanguageVariety>
		                                                    </languageVarietyInfo>
		                                                    <xsl:variable name="oth" select='following-sibling::other'/>
										
		                                                    <xsl:if test="$oth!='' ">
		                                                        <languageVarietyInfo>								
		                                                            <languageVarietyName>
		                                                                <xsl:value-of select="$oth"/>
		                                                            </languageVarietyName>								
		                                                            <languageVarietyType>other</languageVarietyType>
		                                                            <sizePerLanguageVariety>
		                                                                <size>2</size>	
		                                                                <sizeUnit>gb</sizeUnit>	
		                                                            </sizePerLanguageVariety>
		                                                        </languageVarietyInfo>
		                                                    </xsl:if>
		                                                </xsl:if>
		                                                </languageInfo>	
		                                            </xsl:if>
		                                        </xsl:for-each>		
		                                    	
							
		                                    <xsl:variable name="size" select='preceding-sibling::tech_bytesize'/>	
		                                    <xsl:if test="$size!=''">							
		                                        <sizeInfo>
		                                            <xsl:choose>
		                                                <xsl:when test='contains($size, "words")'>
		                                                    <xsl:variable name="sz" select="substring-before($size, 'million')"/>
		                                                    <size>
		                                                        <xsl:value-of select="$sz*1000000"/>
		                                                    </size>	
		                                                    <sizeUnit>words</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test='contains($size, "hours")'>
		                                                    <xsl:variable name="sz" select="substring-before($size, ' hours')"/>
		                                                    <size>
		                                                        <xsl:value-of select="substring-after($sz, ' ')"/>
		                                                    </size>	
		                                                    <sizeUnit>hours</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test='contains($size, "minutes")'>
		                                                    <xsl:variable name="sz" select="substring-before($size, ' minutes')"/>
		                                                    <size>
		                                                        <xsl:value-of select="$sz"/>
		                                                    </size>	
		                                                    <sizeUnit>minutes</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test="contains($size, 'language')">
		                                                    <size>2</size>	
		                                                    <sizeUnit>gb</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test="contains($size, 'Mo') or contains($size, 'Mb')">
		                                                    <size>
		                                                        <xsl:value-of select="substring-before($size, ' ')"/>
		                                                    </size>	
		                                                    <sizeUnit>mb</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test="contains($size, 'kb') or contains($size, 'Kb')">
		                                                    <size>
		                                                        <xsl:value-of select="substring-before($size, ' ')"/>
		                                                    </size>	
		                                                    <sizeUnit>kb</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test="contains($size, 'Gb')">
		                                                    <size>
		                                                        <xsl:value-of select="substring-before($size, ' ')"/>
		                                                    </size>		
		                                                    <sizeUnit>gb</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test="contains($size, 'min')">
		                                                    <xsl:variable name="hours" select="substring-before($size, 'h')"/>
		                                                    <xsl:variable name="mins" select="substring-after($size, 'h')"/>
		                                                    <size>
		                                                        <xsl:value-of select="$hours*60+substring-before($mins, 'min')"/>
		                                                    </size>		
		                                                    <sizeUnit>minutes</sizeUnit>	
		                                                </xsl:when>
		                                            </xsl:choose>						
		                                        </sizeInfo>
		                                    </xsl:if>
						
						
		                                    <xsl:variable name="tff" select='preceding-sibling::tech_fileformat'/>	
		                                    <xsl:if test="$tff!=''">
		                                        <textFormatInfo>								
		                                            <mimeType>
		                                                <xsl:value-of select="$tff"/>
		                                            </mimeType>								
		                                        </textFormatInfo>
		                                    </xsl:if>
		                                    <xsl:variable name="chars" select='preceding-sibling::character_set'/>							
		                                    <xsl:if test="$chars!='' and not(contains($chars, 'SAMPA')) and not(contains($chars, 'EAGLES'))">
		                                        <characterEncodingInfo>								
		                                            <characterEncoding>
		                                                <xsl:choose>
		                                                    <xsl:when test="contains($chars, '8859')">ISO-8859-1</xsl:when>
		                                                    <xsl:when test="contains($chars, 'ASCII')">US-ASCII</xsl:when>
		                                                    <xsl:when test="contains($chars, 'UTF-8') or contains($chars, 'Unicode') or contains($chars, 'UNICODE')">UTF-8</xsl:when>
		                                                </xsl:choose>
		                                            </characterEncoding>
		                                        </characterEncodingInfo>	
		                                    </xsl:if>		
							
		                                    <xsl:variable name='aa' select="preceding-sibling::application_area[1]"/>
							
		                                    <xsl:if test='$aa!=""'>
		                                        <domainInfo>							
		                                            <domain>
		                                                <xsl:if test="$aa='Tourism'">tourism</xsl:if>
		                                                <xsl:if test="$aa='Training#Research'">science</xsl:if>
		                                            </domain>
		                                        </domainInfo>
		                                    </xsl:if>
							
		                                    <xsl:variable name='time' select='preceding-sibling::resource_periodofcoverage'/>
		                                    <xsl:if test='$time!=""'>
		                                        <timeCoverageInfo>
		                                            <timeCoverage>
		                                                <xsl:value-of select='$time'/>
		                                            </timeCoverage>
		                                        </timeCoverageInfo>
		                                    </xsl:if>
			
		                                </lexicalConceptualResourceTextInfo>
		                            
		                            <xsl:if test=".='speech'">
		                                <lexicalConceptualResourceAudioInfo>					
		                                    <mediaType>audio</mediaType>	
						
						
						
		                                    <xsl:variable name='nol' select="preceding-sibling::content_numberoflanguages[1]"/>	
							
		                                    <lingualityInfo>
		                                        <lingualityType>
		                                            <xsl:choose>
		                                                <xsl:when test="$nol='Multilingual'">multilingual</xsl:when>							
		                                                <xsl:when test="$nol='Bilingual'">bilingual</xsl:when>
		                                                <xsl:otherwise>monolingual</xsl:otherwise>
		                                            </xsl:choose>
		                                        </lingualityType>
		                                    </lingualityInfo>
								
		                                   
		                                        <xsl:for-each select="//*[((local-name()='source_language' or local-name()='target_language') and namespace-uri()='')]">
		                                            <xsl:variable name="lang" select="string(.)"/>
		                                            <xsl:if test='$lang!="" and $lang!="NULL"'>
		                                                <xsl:variable name="eng" select="//iso639_1[text()=$lang]/following-sibling::english[1]"/>
								
							 <languageInfo>	
		                                                <languageId>
		                                                    <xsl:value-of select="//iso639_1[text()=$lang]/preceding-sibling::iso639_2[1]"/>
		                                                </languageId>	
		                                                <languageName>
								
		                                                    <xsl:value-of select="$eng"/>
		                                                </languageName>	
								
		                                                <xsl:variable name="a" select="$eng/following-sibling::*[1]"/>
								
		                                                <xsl:variable name="vn" select='following-sibling::language_variety_name'/>
		                                                <xsl:if test="$a=$vn">
		                                                    <languageVarietyInfo>
		                                                        <languageVarietyType>dialect</languageVarietyType>
		                                                        <languageVarietyName>
		                                                            <xsl:value-of select="$vn"/>
		                                                        </languageVarietyName>
		                                                        <sizePerLanguageVariety>
		                                                            <size>2</size>	
		                                                            <sizeUnit>gb</sizeUnit>	
		                                                        </sizePerLanguageVariety>
		                                                    </languageVarietyInfo>
		                                                    <xsl:variable name="oth" select='following-sibling::other'/>
										
		                                                    <xsl:if test="$oth!='' ">
		                                                        <languageVarietyInfo>								
		                                                            <languageVarietyName>
		                                                                <xsl:value-of select="$oth"/>
		                                                            </languageVarietyName>								
		                                                            <languageVarietyType>other</languageVarietyType>
		                                                            <sizePerLanguageVariety>
		                                                                <size>2</size>	
		                                                                <sizeUnit>gb</sizeUnit>	
		                                                            </sizePerLanguageVariety>
		                                                        </languageVarietyInfo>
		                                                    </xsl:if>
		                                                </xsl:if>
		                                                </languageInfo>	
		                                            </xsl:if>
		                                        </xsl:for-each>		
		                                    
							
							
		                                    <xsl:variable name="size" select='preceding-sibling::tech_bytesize'/>	
		                                    <xsl:if test="$size!=''">							
		                                        <sizeInfo>
		                                            <xsl:choose>
		                                                <xsl:when test='contains($size, "words")'>
		                                                    <xsl:variable name="sz" select="substring-before($size, 'million')"/>
		                                                    <size>
		                                                        <xsl:value-of select="$sz*1000000"/>
		                                                    </size>	
		                                                    <sizeUnit>words</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test='contains($size, "hours")'>
		                                                    <xsl:variable name="sz" select="substring-before($size, ' hours')"/>
		                                                    <size>
		                                                        <xsl:value-of select="substring-after($sz, ' ')"/>
		                                                    </size>	
		                                                    <sizeUnit>hours</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test='contains($size, "minutes")'>
		                                                    <xsl:variable name="sz" select="substring-before($size, ' minutes')"/>
		                                                    <size>
		                                                        <xsl:value-of select="$sz"/>
		                                                    </size>	
		                                                    <sizeUnit>minutes</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test="contains($size, 'language')">
		                                                    <size>2</size>	
		                                                    <sizeUnit>gb</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test="contains($size, 'Mo') or contains($size, 'Mb')">
		                                                    <size>
		                                                        <xsl:value-of select="substring-before($size, ' ')"/>
		                                                    </size>	
		                                                    <sizeUnit>mb</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test="contains($size, 'kb') or contains($size, 'Kb')">
		                                                    <size>
		                                                        <xsl:value-of select="substring-before($size, ' ')"/>
		                                                    </size>	
		                                                    <sizeUnit>kb</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test="contains($size, 'Gb')">
		                                                    <size>
		                                                        <xsl:value-of select="substring-before($size, ' ')"/>
		                                                    </size>		
		                                                    <sizeUnit>gb</sizeUnit>	
		                                                </xsl:when>
		                                                <xsl:when test="contains($size, 'min')">
		                                                    <xsl:variable name="hours" select="substring-before($size, 'h')"/>
		                                                    <xsl:variable name="mins" select="substring-after($size, 'h')"/>
		                                                    <size>
		                                                        <xsl:value-of select="$hours*60+substring-before($mins, 'min')"/>
		                                                    </size>		
		                                                    <sizeUnit>minutes</sizeUnit>	
		                                                </xsl:when>
		                                            </xsl:choose>						
		                                        </sizeInfo>
		                                    </xsl:if>						
							
							
		                                    <xsl:variable name='aa' select="preceding-sibling::application_area[1]"/>
		                                    <xsl:if test='$aa!=""'>
		                                        <domainInfo>							
		                                            <domain>
		                                                <xsl:if test="$aa='Tourism'">tourism</xsl:if>
		                                                <xsl:if test="$aa='Training#Research'">science</xsl:if>
		                                            </domain>
		                                        </domainInfo>
		                                    </xsl:if>
							
						
						
		                                    <xsl:variable name='time' select='preceding-sibling::resource_periodofcoverage'/>
							
		                                    <xsl:if test='$time!=""'>
		                                        <timeCoverageInfo>
		                                            <timeCoverage>
		                                                <xsl:value-of select='$time'/>
		                                            </timeCoverage>
		                                        </timeCoverageInfo>
		                                    </xsl:if>
									
		                                </lexicalConceptualResourceAudioInfo>
					
		                            </xsl:if>
		                        </xsl:for-each>
		                    </lexicalConceptualResourceMediaType>			
						
						
		                </lexicalConceptualResourceInfo>
		 	</resourceComponentType>
		        
                    </xsl:if>                
                
            </xsl:for-each>
        </resourceInfo>
    </xsl:template>
</xsl:stylesheet>

