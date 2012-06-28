package metashare.upgrader;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerException;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.TransformerFactoryConfigurationError;
import javax.xml.transform.dom.DOMResult;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import javax.xml.transform.stream.StreamSource;
import javax.xml.validation.Schema;
import javax.xml.validation.SchemaFactory;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.xml.sax.SAXException;

public class XMLTool {
	public enum MetashareSchemaVersion { v10, v11, v20, v21 };

	public static String metashareNamespaceURI = "http://www.ilsp.gr/META-XMLSchema";
	
	public static Schema METASHARE_SCHEMA_21 = initSchema("schema21/META-SHARE-Resource.xsd");
	
	public static Transformer METASHARE_20to21 = initTransformer("conversion/2.0_to_2.1.xsl");
	public static Transformer METASHARE_11to20 = initTransformer("conversion/1.1_to_2.0.xsl");
	public static Transformer METASHARE_10to11 = initTransformer("conversion/1.0_to_1.1.xsl");
	
	private static Map<MetashareSchemaVersion, Transformer> version2transformer = initVersion2Transformer(); 
	private static Map<MetashareSchemaVersion, Schema> version2schema = initVersion2Schema(); 
	
	private static DocumentBuilder builder = initBuilder();
	
	private static Schema initSchema(String resourceName) {
		try {
			return SchemaFactory.newInstance(XMLConstants.W3C_XML_SCHEMA_NS_URI).newSchema(XMLTool.class.getResource(resourceName));
		} catch (Exception e) {
			throw new Error("Cannot initiate Schema from resource "+resourceName, e);
		}
	}
	
	private static Map<MetashareSchemaVersion, Transformer> initVersion2Transformer() {
		Map<MetashareSchemaVersion, Transformer> m = new HashMap<XMLTool.MetashareSchemaVersion, Transformer>();
		m.put(MetashareSchemaVersion.v10, METASHARE_10to11);
		m.put(MetashareSchemaVersion.v11, METASHARE_11to20);
		m.put(MetashareSchemaVersion.v20, METASHARE_20to21);
		return Collections.unmodifiableMap(m);
	}

	private static Map<MetashareSchemaVersion, Schema> initVersion2Schema() {
		Map<MetashareSchemaVersion, Schema> m = new HashMap<XMLTool.MetashareSchemaVersion, Schema>();
		m.put(MetashareSchemaVersion.v21, METASHARE_SCHEMA_21);
		return Collections.unmodifiableMap(m);
	}

	private static Transformer initTransformer(String stylesheetResource) {
		try {
			return TransformerFactory.newInstance().newTransformer(new StreamSource(XMLTool.class.getResourceAsStream(stylesheetResource)));
		} catch (Exception e) {
			throw new Error("Cannot initiate XSLT Transformer from resource "+stylesheetResource, e);
		}
	}

	private static DocumentBuilder initBuilder() {
		DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
		factory.setNamespaceAware(true);
		try {
			return factory.newDocumentBuilder();
		} catch (Exception e) {
			throw new Error("Cannot instantiate parser", e);
		}
	}
	
	public static Document parse(InputStream in) throws IOException, SAXException {
		return builder.parse(in);
	}

	public static Document parse(File in) throws IOException, SAXException {
		return builder.parse(in);
	}
	
	public static void validate(Document doc, Schema schema) throws IOException, SAXException {
		schema.newValidator().validate(new DOMSource(doc));
	}
	
	public static Document transform(Document in, Transformer transformer) throws TransformerException {
		DOMResult result = new DOMResult();
		transformer.transform(new DOMSource(in), result);
		return (Document) result.getNode();
	}

	public static MetashareSchemaVersion guessSchemaVersion(Document doc) {
		if (doc == null || doc.getDocumentElement() == null) {
			return null;
		}
		Element root = doc.getDocumentElement();
		if (!metashareNamespaceURI.equals(root.getNamespaceURI())) {
			return null;
		}
		if ("Resource".equals(root.getLocalName())) { // 1.x
			// If it contains a <contactPerson> tag, its 1.1:
			if (root.getElementsByTagNameNS(metashareNamespaceURI, "contactPerson").getLength() > 0) {
				return MetashareSchemaVersion.v11;
			}
			return MetashareSchemaVersion.v10;
		} else if ("resourceInfo".equals(root.getLocalName())) { // 2.x
			// if it contains a <fee> element, it's 2.1
			if (root.getElementsByTagNameNS(metashareNamespaceURI, "fee").getLength() > 0
					|| root.getAttributeNS(XMLConstants.W3C_XML_SCHEMA_INSTANCE_NS_URI, "schemaLocation").contains("2.1")){
				return MetashareSchemaVersion.v21;
			}
			return MetashareSchemaVersion.v20;
		}
		return null;
	}

	public static Document transform(Document doc, MetashareSchemaVersion source, MetashareSchemaVersion target) throws TransformerException {
		if (source.compareTo(target) >= 0) {
			throw new IllegalArgumentException("Source version must be older than target version");
		}
		Document oneStep = transform(doc, version2transformer.get(source));
		MetashareSchemaVersion next = MetashareSchemaVersion.values()[source.ordinal()+1];
		if (next == target) {
			return oneStep;
		} else {
			return transform(oneStep, next, target);
		}
	}
	
	public static boolean isValid(Document doc, MetashareSchemaVersion version) {
		Schema schema = version2schema.get(version);
		if (schema == null) {
			return true;
		}
		try {
			validate(doc, schema);
		} catch (Exception e) {
			return false;
		}
		return true;
	}

	public static void write(Document doc, File file) throws IOException, TransformerFactoryConfigurationError, TransformerException {
		Transformer transformer = TransformerFactory.newInstance().newTransformer();
		transformer.setOutputProperty(OutputKeys.INDENT, "yes");
		//initialize StreamResult with File object to save to file
		StreamResult result = new StreamResult(new FileOutputStream(file));
		DOMSource source = new DOMSource(doc);
		transformer.transform(source, result);
	}
}
