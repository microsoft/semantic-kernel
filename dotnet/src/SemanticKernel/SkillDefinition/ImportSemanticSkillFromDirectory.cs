// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Text;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the namespace of IKernel
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Class for extensions methods for importing semantic functions from a directory.
/// </summary>
public static class ImportSemanticSkillFromDirectoryExtension
{
    /// <summary>
    /// Loads semantic functions, defined by prompt templates stored in the filesystem.
    /// </summary>
    /// <remarks>
    /// <para>
    /// A skill directory contains a set of subdirectories, one for each semantic function.
    /// </para>
    /// <para>
    /// This method accepts the path of the parent directory (e.g. "d:\skills") and the name of the skill directory
    /// (e.g. "OfficeSkill"), which is used also as the "skill name" in the internal skill collection (note that
    /// skill and function names can contain only alphanumeric chars and underscore).
    /// </para>
    /// <code>
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
    /// </code>
    /// <para>
    /// See https://github.com/microsoft/semantic-kernel/tree/main/samples/skills for examples in the Semantic Kernel repository.
    /// </para>
    /// </remarks>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="parentDirectory">Directory containing the skill directory, e.g. "d:\myAppSkills"</param>
    /// <param name="skillDirectoryNames">Name of the directories containing the selected skills, e.g. "StrategySkill"</param>
    /// <returns>A list of all the semantic functions found in the directory, indexed by function name.</returns>
    public static IDictionary<string, ISKFunction> ImportSemanticSkillFromDirectory(
        this IKernel kernel, string parentDirectory, params string[] skillDirectoryNames)
    {
        const string ConfigFile = "config.json";
        const string PromptFile = "skprompt.txt";

        var skill = new Dictionary<string, ISKFunction>();

        ILogger? logger = null;
        foreach (string skillDirectoryName in skillDirectoryNames)
        {
            Verify.ValidSkillName(skillDirectoryName);
            var skillDir = Path.Combine(parentDirectory, skillDirectoryName);
            Verify.DirectoryExists(skillDir);

            string[] directories = Directory.GetDirectories(skillDir);
            foreach (string dir in directories)
            {
                var functionName = Path.GetFileName(dir);

                // Continue only if prompt template exists
                var promptPath = Path.Combine(dir, PromptFile);
                if (!File.Exists(promptPath)) { continue; }

                // Load prompt configuration. Note: the configuration is optional.
                var config = new PromptTemplateConfig();
                var configPath = Path.Combine(dir, ConfigFile);
                if (File.Exists(configPath))
                {
                    config = PromptTemplateConfig.FromJson(File.ReadAllText(configPath));
                }

                logger ??= kernel.LoggerFactory.CreateLogger(typeof(IKernel));
                if (logger.IsEnabled(LogLevel.Trace))
                {
                    logger.LogTrace("Config {0}: {1}", functionName, config.ToJson());
                }

                // Load prompt template
                var template = new PromptTemplate(File.ReadAllText(promptPath), config, kernel.PromptTemplateEngine);

                var functionConfig = new SemanticFunctionConfig(config, template);

                if (logger.IsEnabled(LogLevel.Trace))
                {
                    logger.LogTrace("Registering function {0}.{1} loaded from {2}", skillDirectoryName, functionName, dir);
                }

                skill[functionName] = kernel.RegisterSemanticFunction(skillDirectoryName, functionName, functionConfig);
            }
        }

        return skill;
    }
}
