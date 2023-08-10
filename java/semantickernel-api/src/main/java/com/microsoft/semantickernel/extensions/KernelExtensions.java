// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.extensions;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.KernelException;
import com.microsoft.semantickernel.SKBuilders;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplate;
import com.microsoft.semantickernel.semanticfunctions.PromptTemplateConfig;
import com.microsoft.semantickernel.semanticfunctions.SemanticFunctionConfig;
import com.microsoft.semantickernel.templateengine.PromptTemplateEngine;
import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Collectors;
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
                    KernelException.ErrorCodes.FunctionNotAvailable,
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
                                .setPromptTemplate(template)
                                .setPromptTemplateConfig(config)
                                .setPromptTemplateEngine(promptTemplateEngine)
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
                        .setPromptTemplate(template)
                        .setPromptTemplateConfig(config)
                        .setPromptTemplateEngine(promptTemplateEngine)
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

        InputStream promptFileStream;
        if (clazz == null) {
            promptFileStream =
                    KernelExtensions.class.getClassLoader().getResourceAsStream(promptFileName);
        } else {
            promptFileStream = clazz.getResourceAsStream(promptFileName);
        }

        String template;

        try (BufferedReader promptFile =
                new BufferedReader(
                        new InputStreamReader(promptFileStream, Charset.defaultCharset()))) {
            template = promptFile.lines().collect(Collectors.joining("\n"));
        } catch (IOException e) {
            LOGGER.error("Failed to read file " + promptFileName, e);

            throw new KernelException(
                    KernelException.ErrorCodes.FunctionNotAvailable,
                    "No Skills found in directory " + promptFileName);
        }
        return template;
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

        InputStream configFileStream;
        if (clazz == null) {
            configFileStream =
                    KernelExtensions.class.getClassLoader().getResourceAsStream(configFileName);
        } else {
            configFileStream = clazz.getResourceAsStream(configFileName);
        }

        if (configFileStream == null) {
            return null;
        }

        try (InputStream is = configFileStream) {
            return new ObjectMapper().readValue(is, PromptTemplateConfig.class);
        } catch (IOException e) {
            LOGGER.debug("No config for " + functionName + " in " + pluginName);
            return null;
        }
    }
}
