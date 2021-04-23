package myplcc.defnLang;

import myplcc.GeneratedClass;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintStream;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;

public final class Generate {
	private Generate() {
	}

	public static void main(String[] args) throws IOException {
		String cwd = System.getProperty("user.dir");
		Path outDir = Paths.get(cwd, "../gen/src/main/java").normalize();
		outDir.toFile().mkdirs();
		Files.walkFileTree(outDir, new SimpleFileVisitor<Path>() {
			@Override
			public FileVisitResult postVisitDirectory(Path dir, IOException exc) throws IOException {
				if(!dir.equals(outDir)) Files.delete(dir);
				return FileVisitResult.CONTINUE;
			}

			@Override
			public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
				Files.delete(file);
				return FileVisitResult.CONTINUE;
			}
		});
		DefinitionLanguage.itemRule.checkLL1();
		for(GeneratedClass generatedClass : DefinitionLanguage.generatedClasses.values()) {
			StringBuilder sb = new StringBuilder();
			generatedClass.classRef.generate("/", sb);
			assert generatedClass.classRef.classParts.size() == 1;
			Path p = outDir.resolve(sb.toString() + ".java");
			p.getParent().toFile().mkdirs();
			try(FileWriter w = new FileWriter(p.toFile())) {
				generatedClass.generate("", w);
			}
		}
	}
}
