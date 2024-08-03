package com.microsoft.semantickernel.samples.syntaxexamples;

import java.nio.file.Files;
import java.nio.file.Path;

public class SampleSkillsUtil {

    public static final String SAMPLES_SKILLS_DIR = "samples/skills";

    /**
     * Detects the location of the sample skill directory by searching up til the top of the repository.
     */
    public static String detectSkillDirLocation() {
        Path dir = Path.of(System.getProperty("user.dir"));

        do {
            if (Files.isDirectory(dir.resolve(SAMPLES_SKILLS_DIR))) {
                return dir.resolve(SAMPLES_SKILLS_DIR).toFile().getAbsolutePath();
            }

            if (Files.exists(dir.resolve(".gitignore"))) {
                // We've reached the root of the repo
                throw new RuntimeException("Could not find skill directory");
            }

        } while ((dir = dir.getParent()) != null);

        throw new RuntimeException("Could not find skill directory");
    }
}
