// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.kernelextensions;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.microsoft.semantickernel.semanticfunctions.DefaultPromptTemplate;
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

/// <summary>
/// Class for extensions methods for importing semantic functions from a directory.
/// </summary>
public class ImportSemanticSkillFromDirectoryExtension {

    private static final Logger LOGGER =
            LoggerFactory.getLogger(ImportSemanticSkillFromDirectoryExtension.class);

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
                DefaultPromptTemplate template =
                        new DefaultPromptTemplate(
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

    /*
    /// <summary>
    /// A kernel extension that allows to load Semantic Functions, defined by prompt templates stored in the filesystem.
    /// A skill directory contains a set of subdirectories, one for each semantic function.
    /// This extension requires the path of the parent directory (e.g. "d:\skills") and the name of the skill directory
    /// (e.g. "OfficeSkill"), which is used also as the "skill name" in the internal skill collection.
    ///
    /// Note: skill and function names can contain only alphanumeric chars and underscore.
    ///
    /// Example:
    /// D:\skills\                            # parentDirectory = "D:\skills"
    ///
    ///     |__ OfficeSkill\                  # skillDirectoryName = "SummarizeEmailThread"
    ///
    ///         |__ ScheduleMeeting           # semantic function
    ///             |__ skprompt.txt          # prompt template
    ///             |__ config.json           # settings (optional file)
    ///
    ///         |__ SummarizeEmailThread      # semantic function
    ///             |__ skprompt.txt          # prompt template
    ///             |__ config.json           # settings (optional file)
    ///
    ///         |__ MergeWordAndExcelDocs     # semantic function
    ///             |__ skprompt.txt          # prompt template
    ///             |__ config.json           # settings (optional file)
    ///
    ///     |__ XboxSkill\                    # another skill, etc.
    ///
    ///         |__ MessageFriend
    ///             |__ skprompt.txt
    ///             |__ config.json
    ///         |__ LaunchGame
    ///             |__ skprompt.txt
    ///             |__ config.json
    ///
    /// See https://github.com/microsoft/semantic-kernel/tree/main/samples/skills for some skills in our repo.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="parentDirectory">Directory containing the skill directory, e.g. "d:\myAppSkills"</param>
    /// <param name="skillDirectoryName">Name of the directory containing the selected skill, e.g. "StrategySkill"</param>
    /// <returns>A list of all the semantic functions found in the directory, indexed by function name.</returns>
    public static IDictionary<string, ISKFunction> ImportSemanticSkillFromDirectory(
        this IKernel kernel, string parentDirectory, string skillDirectoryName) {
        const string CONFIG_FILE = "config.json";
        const string PROMPT_FILE = "skprompt.txt";

        Verify.ValidSkillName(skillDirectoryName);
        var skillDir = Path.Combine(parentDirectory, skillDirectoryName);
        Verify.DirectoryExists(skillDir);

        var skill = new Dictionary<string, ISKFunction>();

        string[] directories = Directory.GetDirectories(skillDir);
        foreach(string dir in directories)
        {
            var functionName = Path.GetFileName(dir);

            // Continue only if prompt template exists
            var promptPath = Path.Combine(dir, PROMPT_FILE);
            if (!File.Exists(promptPath)) {
                continue;
            }

            // Load prompt configuration. Note: the configuration is optional.
            var config = new PromptTemplateConfig();
            var configPath = Path.Combine(dir, CONFIG_FILE);
            if (File.Exists(configPath)) {
                config = PromptTemplateConfig.FromJson(File.ReadAllText(configPath));
                Verify.NotNull(config, $"Invalid prompt template configuration, unable to parse {configPath}");
            }

            kernel.Log.LogTrace("Config {0}: {1}", functionName, config.ToJson());

            // Load prompt template
            var template = new PromptTemplate(File.ReadAllText(promptPath), config, kernel.PromptTemplateEngine);

            // Prepare lambda wrapping AI logic
            var functionConfig = new SemanticFunctionConfig(config, template);

            kernel.Log.LogTrace("Registering function {0}.{1} loaded from {2}", skillDirectoryName, functionName, dir);
            skill[functionName] = kernel.RegisterSemanticFunction(skillDirectoryName, functionName, functionConfig);
        }

        return skill;
    }

     */
}
