// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.extensions;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.KernelException;
import com.microsoft.semantickernel.KernelException.ErrorCodes;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import com.microsoft.semantickernel.util.EmbeddedResourceLoader;
import com.microsoft.semantickernel.util.EmbeddedResourceLoader.ResourceLocation;
import java.io.File;
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.util.HashMap;
import java.util.Map;
import javax.annotation.Nullable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class KernelExtensions {

    private static final Logger LOGGER = LoggerFactory.getLogger(KernelExtensions.class);
    private static final String CONFIG_FILE = "config.json";
    private static final String PROMPT_FILE = "skprompt.txt";

    private KernelExtensions() {}

    public static Map<String, SemanticFunctionConfig> importSemanticSkillFromDirectory(
            String parentDirectory,
            String skillDirectoryName,
            PromptTemplateEngine promptTemplateEngine) {

        // Verify.ValidSkillName(skillDirectoryName);
        File skillDir = new File(parentDirectory, skillDirectoryName);
        // Verify.DirectoryExists(skillDir);

        File[] files = skillDir.listFiles();
        if (files == null) {
            throw new KernelException(
                    ErrorCodes.FUNCTION_NOT_AVAILABLE,
                    "No Skills found in directory " + skillDir.getAbsolutePath());
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
                String template =
                        new String(
                                Files.readAllBytes(promptPath.toPath()), Charset.defaultCharset());

                PromptTemplate promptTemplate =
                        SKBuilders.promptTemplate()
                                .withPromptTemplate(template)
                                .withPromptTemplateConfig(config)
                                .withPromptTemplateEngine(promptTemplateEngine)
                                .build();

                skills.put(dir.getName(), new SemanticFunctionConfig(config, promptTemplate));
            } catch (IOException e) {
                LOGGER.error("Failed to read file", e);
            }
        }

        return skills;
    }

    public static Map<String, SemanticFunctionConfig> importSemanticSkillFromResourcesDirectory(
            String pluginDirectory,
            String pluginName,
            String functionName,
            @Nullable Class clazz,
            PromptTemplateEngine promptTemplateEngine) {

        PromptTemplateConfig config =
                getPromptTemplateConfig(pluginDirectory, pluginName, functionName, clazz);

        if (config == null) {
            config = new PromptTemplateConfig("", "", null);
        }

        String template = getTemplatePrompt(pluginDirectory, pluginName, functionName, clazz);

        HashMap<String, SemanticFunctionConfig> skills = new HashMap<>();

        PromptTemplate promptTemplate =
                SKBuilders.promptTemplate()
                        .withPromptTemplate(template)
                        .withPromptTemplateConfig(config)
                        .withPromptTemplateEngine(promptTemplateEngine)
                        .build();

        skills.put(functionName, new SemanticFunctionConfig(config, promptTemplate));

        return skills;
    }

    private static String getTemplatePrompt(
            String pluginDirectory, String pluginName, String functionName, @Nullable Class clazz) {
        String promptFileName =
                pluginDirectory
                        + File.separator
                        + pluginName
                        + File.separator
                        + functionName
                        + File.separator
                        + PROMPT_FILE;

        try {
            return EmbeddedResourceLoader.readFile(
                    promptFileName,
                    clazz,
                    ResourceLocation.CLASSPATH_ROOT,
                    ResourceLocation.CLASSPATH,
                    ResourceLocation.FILESYSTEM);
        } catch (IOException e) {
            LOGGER.error("Failed to read file " + promptFileName, e);

            throw new KernelException(
                    ErrorCodes.FUNCTION_NOT_AVAILABLE,
                    "No Skills found in directory " + promptFileName);
        }
    }

    private static PromptTemplateConfig getPromptTemplateConfig(
            String pluginDirectory, String pluginName, String functionName, @Nullable Class clazz) {
        String configFileName =
                pluginDirectory
                        + File.separator
                        + pluginName
                        + File.separator
                        + functionName
                        + File.separator
                        + CONFIG_FILE;

        try {
            String config =
                    EmbeddedResourceLoader.readFile(
                            configFileName,
                            clazz,
                            ResourceLocation.CLASSPATH_ROOT,
                            ResourceLocation.CLASSPATH,
                            ResourceLocation.FILESYSTEM);

            return new ObjectMapper().readValue(config, PromptTemplateConfig.class);
        } catch (IOException e) {
            LOGGER.debug("No config for " + functionName + " in " + pluginName);
            return null;
        }
    }
}
