// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.Text;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the namespace of IKernel
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Class for extensions methods to define semantic functions.
/// </summary>
public static class InlineFunctionsDefinitionExtension
{
    /// <summary>
    /// Define a string-to-string semantic function, with no direct support for input context.
    /// The function can be referenced in templates and will receive the context, but when invoked programmatically you
    /// can only pass in a string in input and receive a string in output.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="promptTemplate">Plain language definition of the semantic function, using SK template language</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <param name="pluginName">Optional plugin name, for namespacing and avoid collisions</param>
    /// <param name="description">Optional description, useful for the planner</param>
    /// <param name="maxTokens">Max number of tokens to generate</param>
    /// <param name="temperature">Temperature parameter passed to LLM</param>
    /// <param name="topP">Top P parameter passed to LLM</param>
    /// <param name="presencePenalty">Presence Penalty parameter passed to LLM</param>
    /// <param name="frequencyPenalty">Frequency Penalty parameter passed to LLM</param>
    /// <param name="stopSequences">Strings the LLM will detect to stop generating (before reaching max tokens)</param>
    /// <param name="chatSystemPrompt">When provided will be used to set the system prompt while using Chat Completions</param>
    /// <param name="serviceId">When provided will be used to select the AI service used</param>
    /// <returns>A function ready to use</returns>
    public static ISKFunction CreateSemanticFunction(
        this IKernel kernel,
        string promptTemplate,
        string? functionName = null,
        string? pluginName = null,
        string? description = null,
        int? maxTokens = null,
        double temperature = 0,
        double topP = 0,
        double presencePenalty = 0,
        double frequencyPenalty = 0,
        IEnumerable<string>? stopSequences = null,
        string? chatSystemPrompt = null,
        string? serviceId = null)
    {
        functionName ??= RandomFunctionName();

        var config = new PromptTemplateConfig
        {
            Description = description ?? "Generic function, unknown purpose",
            Type = "completion",
            Completion = new PromptTemplateConfig.CompletionConfig
            {
                Temperature = temperature,
                TopP = topP,
                PresencePenalty = presencePenalty,
                FrequencyPenalty = frequencyPenalty,
                MaxTokens = maxTokens,
                StopSequences = stopSequences?.ToList() ?? new List<string>(),
                ChatSystemPrompt = chatSystemPrompt,
                ServiceId = serviceId
            }
        };

        return kernel.CreateSemanticFunction(
            promptTemplate: promptTemplate,
            config: config,
            functionName: functionName,
            pluginName: pluginName);
    }

    /// <summary>
    /// Allow to define a semantic function passing in the definition in natural language, i.e. the prompt template.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="promptTemplate">Plain language definition of the semantic function, using SK template language</param>
    /// <param name="config">Optional function settings</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <param name="pluginName">An optional plugin name, e.g. to namespace functions with the same name. When empty,
    /// the function is added to the global namespace, overwriting functions with the same name</param>
    /// <returns>A function ready to use</returns>
    public static ISKFunction CreateSemanticFunction(
        this IKernel kernel,
        string promptTemplate,
        PromptTemplateConfig config,
        string? functionName = null,
        string? pluginName = null)
    {
        functionName ??= RandomFunctionName();
        Verify.ValidFunctionName(functionName);
        if (!string.IsNullOrEmpty(pluginName)) { Verify.ValidPluginName(pluginName); }

        var template = new PromptTemplate(promptTemplate, config, kernel.PromptTemplateEngine);

        // Prepare lambda wrapping AI logic
        var functionConfig = new SemanticFunctionConfig(config, template);

        // TODO: manage overwrites, potentially error out
        return string.IsNullOrEmpty(pluginName)
            ? kernel.RegisterSemanticFunction(functionName, functionConfig)
            : kernel.RegisterSemanticFunction(pluginName!, functionName, functionConfig);
    }

    /// <summary>
    /// Invoke a semantic function using the provided prompt template.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="promptTemplate">Plain language definition of the semantic function, using SK template language</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <param name="pluginName">Optional plugin name, for namespacing and avoid collisions</param>
    /// <param name="description">Optional description, useful for the planner</param>
    /// <param name="maxTokens">Max number of tokens to generate</param>
    /// <param name="temperature">Temperature parameter passed to LLM</param>
    /// <param name="topP">Top P parameter passed to LLM</param>
    /// <param name="presencePenalty">Presence Penalty parameter passed to LLM</param>
    /// <param name="frequencyPenalty">Frequency Penalty parameter passed to LLM</param>
    /// <param name="stopSequences">Strings the LLM will detect to stop generating (before reaching max tokens)</param>
    /// <param name="chatSystemPrompt">When provided will be used to set the system prompt while using Chat Completions</param>
    /// <param name="serviceId">When provided will be used to select the AI service used</param>
    /// <returns>A function ready to use</returns>
    public static Task<SKContext> InvokeSemanticFunctionAsync(
        this IKernel kernel,
        string promptTemplate,
        string? functionName = null,
        string? pluginName = null,
        string? description = null,
        int? maxTokens = null,
        double temperature = 0,
        double topP = 0,
        double presencePenalty = 0,
        double frequencyPenalty = 0,
        IEnumerable<string>? stopSequences = null,
        string? chatSystemPrompt = null,
        string? serviceId = null)
    {
        var skfunction = kernel.CreateSemanticFunction(
            promptTemplate,
            functionName,
            pluginName,
            description,
            maxTokens,
            temperature,
            topP,
            presencePenalty,
            frequencyPenalty,
            stopSequences,
            chatSystemPrompt,
            serviceId);

        return kernel.RunAsync(skfunction);
    }

    /// <summary>
    /// Loads semantic functions, defined by prompt templates stored in the filesystem.
    /// </summary>
    /// <remarks>
    /// <para>
    /// A plugin directory contains a set of subdirectories, one for each semantic function.
    /// </para>
    /// <para>
    /// This method accepts the path of the parent directory (e.g. "d:\plugins") and the name of the plugin directory
    /// (e.g. "OfficePlugin"), which is used also as the "plugin name" in the internal function collection (note that
    /// pligin and function names can contain only alphanumeric chars and underscore).
    /// </para>
    /// <code>
    /// Example:
    /// D:\plugins\                            # parentDirectory = "D:\plugins"
    ///
    ///     |__ OfficePlugin\                  # pluginDirectoryName = "SummarizeEmailThread"
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
    ///     |__ XboxPlugin\                    # another plugin, etc.
    ///
    ///         |__ MessageFriend
    ///             |__ skprompt.txt
    ///             |__ config.json
    ///         |__ LaunchGame
    ///             |__ skprompt.txt
    ///             |__ config.json
    /// </code>
    /// <para>
    /// See https://github.com/microsoft/semantic-kernel/tree/main/samples/plugins for examples in the Semantic Kernel repository.
    /// </para>
    /// </remarks>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="parentDirectory">Directory containing the plugin directory, e.g. "d:\myAppPlugins"</param>
    /// <param name="pluginDirectoryNames">Name of the directories containing the selected plugins, e.g. "StrategyPlugin"</param>
    /// <returns>A list of all the semantic functions found in the directory, indexed by function name.</returns>
    public static IDictionary<string, ISKFunction> ImportSemanticFunctionsFromDirectory(
        this IKernel kernel, string parentDirectory, params string[] pluginDirectoryNames)
    {
        const string ConfigFile = "config.json";
        const string PromptFile = "skprompt.txt";

        var functions = new Dictionary<string, ISKFunction>();

        ILogger? logger = null;
        foreach (string pluginDirectoryName in pluginDirectoryNames)
        {
            Verify.ValidPluginName(pluginDirectoryName);
            var pluginDirectory = Path.Combine(parentDirectory, pluginDirectoryName);
            Verify.DirectoryExists(pluginDirectory);

            string[] directories = Directory.GetDirectories(pluginDirectory);
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
                    logger.LogTrace("Registering function {0}.{1} loaded from {2}", pluginDirectoryName, functionName, dir);
                }

                functions[functionName] = kernel.RegisterSemanticFunction(pluginDirectoryName, functionName, functionConfig);
            }
        }

        return functions;
    }

    private static string RandomFunctionName() => "func" + Guid.NewGuid().ToString("N");
}
