// Copyright (c) Microsoft. All rights reserved.
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using System;
using System.Linq;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Class for extensions methods to define agent using prompt YAML format.
/// </summary>
public static class KernelExtensions
{
    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt function using the specified YAML.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="text">YAML representation of the <see cref="PromptTemplateConfig"/> to use to create the prompt function</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the prompt template configuration into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <param name="defaultArguments">// %%%</param>
    /// <param name="id">// %%%</param>
    /// <returns>The created <see cref="ChatCompletionAgent"/>.</returns>
    public static ChatCompletionAgent CreateChatCompletionAgentFromPromptYaml(
        this Kernel kernel,
        string text,
        IPromptTemplateFactory? promptTemplateFactory = null,
        KernelArguments? defaultArguments = null,
        string? id = null)
    {
        return FromPromptYaml(text, kernel, promptTemplateFactory, kernel.LoggerFactory, defaultArguments, id);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt function using the specified markdown text.
    /// </summary>
    /// <param name="yamlText">YAML representation of the <see cref="PromptTemplateConfig"/> to use to create the prompt function.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the prompt template configuration into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="defaultArguments">// %%%</param>
    /// <param name="id">// %%%</param>
    /// <returns>The created <see cref="ChatCompletionAgent"/>.</returns>
    private static ChatCompletionAgent FromPromptYaml(
        string yamlText,
        Kernel kernel,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null,
        KernelArguments? defaultArguments = null,
        string? id = null)
    {
        PromptTemplateConfig promptTemplateConfig = yamlText.ToPromptTemplateConfig();

        // %%% WHAT ARE CONFIG EXECUTION SETTINGS FROM YAML?
        //promptTemplateConfig.ExecutionSettings = defaultArguments?.ExecutionSettings?.ToDictionary(kvp => kvp.Key, kvp => kvp.Value) ?? []; // %%%

        // Prevent the default value from being any type other than a string.
        // It's a temporary limitation that helps shape the public API surface
        // (changing the type of the Default property to object) now, before the release.
        // This helps avoid a breaking change while a proper solution for
        // dealing with the different deserialization outputs of JSON/YAML prompt configurations is being evaluated.
        foreach (var inputVariable in promptTemplateConfig.InputVariables)
        {
            if (inputVariable.Default is not null and not string)
            {
                throw new NotSupportedException($"Default value for input variable '{inputVariable.Name}' must be a string. " +
                        $"This is a temporary limitation; future updates are expected to remove this constraint. Prompt function - '{promptTemplateConfig.Name ?? promptTemplateConfig.Description}'.");
            }
        }

        IPromptTemplateFactory factory = promptTemplateFactory ?? new KernelPromptTemplateFactory(loggerFactory);
        IPromptTemplate template = factory.Create(promptTemplateConfig);
        KernelFunction function = KernelFunctionFactory.CreateFromPrompt(template, promptTemplateConfig, loggerFactory);
        ChatCompletionAgent agent =
            new()
            {
                Id = id ?? Guid.NewGuid().ToString(),
                Name = promptTemplateConfig.Name,
                Description = promptTemplateConfig.Description,
                LoggerFactory = loggerFactory ?? NullLoggerFactory.Instance,
                Arguments = defaultArguments,
                Instructions = promptTemplateConfig.Template,
                Kernel = kernel,
                Template = template,
                //Prompt = function, // %%% << THIS ONE
            };

        return agent;
    }

    /// <summary>
    /// Convert the given YAML text to a <see cref="PromptTemplateConfig"/> model.
    /// </summary>
    /// <param name="text">YAML representation of the <see cref="PromptTemplateConfig"/> to use to create the prompt function.</param>
    private static PromptTemplateConfig ToPromptTemplateConfig(this string text)
    {
        IDeserializer deserializer = new DeserializerBuilder()
            .WithNamingConvention(UnderscoredNamingConvention.Instance)
            .WithNodeDeserializer(new PromptExecutionSettingsNodeDeserializer()) // %%%
            .Build();

        return deserializer.Deserialize<PromptTemplateConfig>(text);
    }
}
