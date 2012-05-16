package metashare.upgrader;

import java.io.File;
import java.io.FilenameFilter;
import java.io.IOException;

import org.w3c.dom.Document;

import metashare.upgrader.XMLTool.MetashareSchemaVersion;

public class Upgrader {

	public static void main(String[] args) throws Exception {
		if (args.length != 2) {
			System.err.println("This tool will convert all META-SHARE XML files in a source folder to META-SHARE format 2.1 versions in a target folder.");
			System.err.println("Usage:");
			System.err.println("java [options] -jar metashare-resource-upgrader.jar source-folder/ target-folder/");
			System.err.println("options: -Dmetashare.targetVersion=... (one of v11, v20, v21; defaults to v21)");
			System.err.println("         -Dmetashare.sourceVersion=... (one of v10, v11, v20; if not set, will guess)");
			System.exit(0);
		}
		File sourceFolder = new File(args[0]);
		if (!sourceFolder.exists() || !sourceFolder.isDirectory()) {
			throw new IOException("source folder "+sourceFolder.getAbsolutePath()+" doesn't exist or is not a directory.");
		}
		File[] sourceFiles = sourceFolder.listFiles(new FilenameFilter() {
			public boolean accept(File file, String filename) {
				return filename.endsWith(".xml");
			}
		});
		if (sourceFiles.length == 0) {
			throw new IOException("No XML files in "+sourceFolder.getAbsolutePath());
		}
		File targetFolder = new File(args[1]);
		if (targetFolder.exists()) {
			if (!targetFolder.isDirectory()) {
				throw new IOException("Target folder "+targetFolder.getAbsolutePath()+" exists but is not a directory");
			} else if (targetFolder.list().length > 0) {
				throw new IOException("Target folder "+targetFolder.getAbsolutePath()+" is not empty.");
			}
		} else {
			targetFolder.mkdirs();
		}
		
		MetashareSchemaVersion targetVersion = MetashareSchemaVersion.valueOf(System.getProperty("metashare.targetVersion", "v21"));
		String sourceVersionString = System.getProperty("metashare.sourceVersion");
		MetashareSchemaVersion sourceVersion = sourceVersionString != null ? MetashareSchemaVersion.valueOf(sourceVersionString) : null;
		
		for (File sourceFile : sourceFiles) {
			String filename = sourceFile.getName();
			File targetFile = new File(targetFolder, filename);
			System.out.print(filename + "... ");
			Document sourceDoc = XMLTool.parse(sourceFile);
			MetashareSchemaVersion from = sourceVersion;
			if (from == null) {
				from = XMLTool.guessSchemaVersion(sourceDoc);
				System.out.print("version seems to be "+from+"... ");
			}
			
			Document targetDoc = XMLTool.transform(sourceDoc, from, targetVersion);
			XMLTool.write(targetDoc, targetFile);
			if (XMLTool.isValid(targetDoc, targetVersion)) {
				System.out.println(" converted ok!");
			} else {
				System.out.println(" converted but not schema-valid, please check manually: "+targetFile.getPath());
			}
		}
		
	}
	
}
