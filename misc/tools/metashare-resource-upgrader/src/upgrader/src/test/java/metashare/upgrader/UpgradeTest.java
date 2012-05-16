package metashare.upgrader;

import javax.xml.XMLConstants;
import javax.xml.validation.Schema;
import javax.xml.validation.SchemaFactory;

import metashare.upgrader.XMLTool.MetashareSchemaVersion;

import org.junit.Test;
import org.w3c.dom.Document;
import org.xml.sax.SAXException;

import static org.junit.Assert.*;

public class UpgradeTest {

	@Test
	public void canInstantiate21Schema() throws Exception {
		Schema metashareSchema = SchemaFactory.newInstance(XMLConstants.W3C_XML_SCHEMA_NS_URI).newSchema(UpgradeTest.class.getResource("schema21/META-SHARE-Resource.xsd"));
		assertNotNull(metashareSchema);
		
	}
	
	@Test
	public void canValidate21Resource() throws Exception {
		Document sample21 = XMLTool.parse(UpgradeTest.class.getResourceAsStream("sample-2.1.xml"));
		XMLTool.validate(sample21, XMLTool.METASHARE_SCHEMA_21);
	}

	@Test(expected=SAXException.class)
	public void wontValidate11Resource() throws Exception {
		Document sample11 = XMLTool.parse(UpgradeTest.class.getResourceAsStream("sample-1.1.xml"));
		XMLTool.validate(sample11, XMLTool.METASHARE_SCHEMA_21);
	}
	
	@Test
	public void canTransform_20to21() throws Exception {
		Document sample20 = XMLTool.parse(UpgradeTest.class.getResourceAsStream("sample-2.0.xml"));
		Document conv21 = XMLTool.transform(sample20, XMLTool.METASHARE_20to21);
		XMLTool.validate(conv21, XMLTool.METASHARE_SCHEMA_21);
	}
	
	@Test
	public void canTransform_11to20() throws Exception {
		Document sample11 = XMLTool.parse(UpgradeTest.class.getResourceAsStream("sample-1.1.xml"));
		Document conv20 = XMLTool.transform(sample11, XMLTool.METASHARE_11to20);
		assertNotNull(conv20);
	}
	
	@Test
	public void canTransform_11to21() throws Exception {
		Document sample11 = XMLTool.parse(UpgradeTest.class.getResourceAsStream("sample-1.1.xml"));
		Document conv20 = XMLTool.transform(sample11, XMLTool.METASHARE_11to20);
		Document conv21 = XMLTool.transform(conv20, XMLTool.METASHARE_20to21);
		XMLTool.validate(conv21, XMLTool.METASHARE_SCHEMA_21);
	}

	@Test
	public void canTransform_10to21() throws Exception {
		Document sample10 = XMLTool.parse(UpgradeTest.class.getResourceAsStream("sample-1.0.xml"));
		Document conv11 = XMLTool.transform(sample10, XMLTool.METASHARE_10to11);
		Document conv20 = XMLTool.transform(conv11, XMLTool.METASHARE_11to20);
		Document conv21 = XMLTool.transform(conv20, XMLTool.METASHARE_20to21);
		XMLTool.validate(conv21, XMLTool.METASHARE_SCHEMA_21);
	}
	
	@Test
	public void guessVersion10() throws Exception {
		Document sample = XMLTool.parse(UpgradeTest.class.getResourceAsStream("sample-1.0.xml"));
		assertEquals(MetashareSchemaVersion.v10, XMLTool.guessSchemaVersion(sample));
	}

	@Test
	public void guessVersion11() throws Exception {
		Document sample = XMLTool.parse(UpgradeTest.class.getResourceAsStream("sample-1.1.xml"));
		assertEquals(MetashareSchemaVersion.v11, XMLTool.guessSchemaVersion(sample));
	}

	@Test
	public void guessVersion20() throws Exception {
		Document sample = XMLTool.parse(UpgradeTest.class.getResourceAsStream("sample-2.0.xml"));
		assertEquals(MetashareSchemaVersion.v20, XMLTool.guessSchemaVersion(sample));
	}

	@Test
	public void guessVersion21() throws Exception {
		Document sample = XMLTool.parse(UpgradeTest.class.getResourceAsStream("sample-2.1.xml"));
		assertEquals(MetashareSchemaVersion.v21, XMLTool.guessSchemaVersion(sample));
	}
	
	@Test
	public void canTransformWithGuessing() throws Exception {
		Document sample10 = XMLTool.parse(UpgradeTest.class.getResourceAsStream("sample-1.0.xml"));
		Document conv21 = XMLTool.transform(sample10, XMLTool.guessSchemaVersion(sample10), MetashareSchemaVersion.v21);
		XMLTool.validate(conv21, XMLTool.METASHARE_SCHEMA_21);
	}

}
