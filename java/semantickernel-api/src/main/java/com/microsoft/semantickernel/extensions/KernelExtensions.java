// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.extensions;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

public class KernelExtensions {
    private static final Logger LOGGER = LoggerFactory.getLogger(KernelExtensions.class);

    private KernelExtensions() {}

    public static Map<String, SemanticFunctionConfig> importSemanticSkillFromDirectory(
            String parentDirectory, String skillDirectoryName) {

        String CONFIG_FILE = "config.json";
        String PROMPT_FILE = "skprompt.txt";

        // Verify.ValidSkillName(skillDirectoryName);
        File skillDir = new File(parentDirectory, skillDirectoryName);
        // Verify.DirectoryExists(skillDir);

        File[] files = skillDir.listFiles();
        if (files == null) {
            return Collections.unmodifiableMap(new HashMap<>());
        }

        HashMap<String, SemanticFunctionConfig> skills = new HashMap<>();

        for (File dir : files) {
            try {
                // Continue only if prompt template exists
                File promptPath = new File(dir, PROMPT_FILE);
                if (!promptPath.exists()) {
                    continue;
                }

                // Load prompt configuration. Note: the configuration is
                // optional.
                PromptTemplateConfig config = new PromptTemplateConfig("", "", null);

                File configPath = new File(dir, CONFIG_FILE);
                if (configPath.exists()) {
                    config = new ObjectMapper().readValue(configPath, PromptTemplateConfig.class);

                    // Verify.NotNull(config, $"Invalid prompt template
                    // configuration, unable to parse {configPath}");
                }

                // kernel.Log.LogTrace("Config {0}: {1}", functionName,
                // config.ToJson());

                // Load prompt template
                PromptTemplate template =
                        SKBuilders.promptTemplate()
                                .build(
                                        new String(
                                                Files.readAllBytes(promptPath.toPath()),
                                                Charset.defaultCharset()),
                                        config);

                skills.put(dir.getName(), new SemanticFunctionConfig(config, template));
            } catch (IOException e) {
                LOGGER.error("Failed to read file", e);
            }
        }

        return skills;
    }
}
