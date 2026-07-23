// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using Microsoft.SemanticKernel.PromptTemplates.Liquid;
using PromptyCore = Prompty.Core;

namespace Microsoft.SemanticKernel.Prompty;

/// <summary>
/// Factory methods for creating <seealso cref="KernelFunction"/> instances.
/// </summary>
public static class KernelFunctionPrompty
{
    /// <summary>Default template factory to use when none is provided.</summary>
    internal static readonly AggregatorPromptTemplateFactory s_defaultTemplateFactory =
        new(new LiquidPromptTemplateFactory(), new HandlebarsPromptTemplateFactory(), new KernelPromptTemplateFactory());

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt function using the specified markdown text.
    /// </summary>
    /// <param name="text">YAML representation of the <see cref="PromptTemplateConfig"/> to use to create the prompt function.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the prompt template configuration into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="KernelFunction"/>.</returns>
    public static KernelFunction FromPrompty(
        string text,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        PromptTemplateConfig promptTemplateConfig = ToPromptTemplateConfig(text);

        return KernelFunctionFactory.CreateFromPrompt(
            promptTemplateConfig,
            promptTemplateFactory ?? s_defaultTemplateFactory,
            loggerFactory);
    }

    /// <summary>
    /// Create a <see cref="PromptTemplateConfig"/> from a prompty template.
    /// </summary>
    /// <param name="promptyTemplate">Prompty representation of a prompt-based <see cref="KernelFunction"/>.</param>
    /// <param name="promptyFilePath">Optional: File path to the prompty file.</param>
    /// <returns>The created <see cref="PromptTemplateConfig"/>.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="promptyTemplate"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="promptyTemplate"/> is empty or composed entirely of whitespace.</exception>
    public static PromptTemplateConfig ToPromptTemplateConfig(string promptyTemplate, string? promptyFilePath = null)
    {
        Verify.NotNullOrWhiteSpace(promptyTemplate);

        PromptyCore.Prompty prompty = LoadPrompty(promptyTemplate, promptyFilePath);

        var promptTemplateConfig = new PromptTemplateConfig
        {
            Name = prompty.Name,
            Description = prompty.Description,
            Template = prompty.Instructions ?? string.Empty,
        };

        PromptExecutionSettings? defaultExecutionSetting = null;
        var extensionData = ToExtensionData(prompty.Model?.Options);
        var modelId = prompty.Model?.Id;
        if (!string.IsNullOrWhiteSpace(modelId) || extensionData.Count > 0)
        {
            defaultExecutionSetting = new PromptExecutionSettings()
            {
                ModelId = string.IsNullOrWhiteSpace(modelId) ? null : modelId,
                ExtensionData = extensionData.Count > 0 ? extensionData : null,
            };
            promptTemplateConfig.AddExecutionSettings(defaultExecutionSetting);
        }

        // Add input and output variables.
        if (prompty.Inputs is not null)
        {
            foreach (var input in prompty.Inputs)
            {
                promptTemplateConfig.InputVariables.Add(new()
                {
                    Name = input.Name,
                    Default = input.Default,
                    IsRequired = input.Required ?? false,
                    Description = input.Description ?? string.Empty,
                });
            }
        }
        if (prompty.Outputs is not null)
        {
            // PromptTemplateConfig supports only a single output variable. If the prompty template
            // contains one and only one, use it. Otherwise, ignore any outputs.
            if (prompty.Outputs.Count == 1)
            {
                var output = prompty.Outputs[0];
                promptTemplateConfig.OutputVariable = new()
                {
                    Description = output.Description ?? string.Empty,
                };
            }
        }

        // Update template format. If not provided, use Liquid as default.
        promptTemplateConfig.TemplateFormat =
            string.IsNullOrEmpty(prompty.Template?.Format?.Kind)
                ? LiquidPromptTemplateFactory.LiquidTemplateFormat
                : prompty.Template!.Format!.Kind;

        return promptTemplateConfig;
    }

    #region private
    /// <summary>
    /// Loads a <see cref="PromptyCore.Prompty"/> from the provided template text, optionally using a file path
    /// so that <c>${file:...}</c> references resolve securely within the prompty file's directory.
    /// </summary>
    private static PromptyCore.Prompty LoadPrompty(string promptyTemplate, string? promptyFilePath)
    {
        try
        {
            // When a real file path is available, use the file loader so that file references
            // (${file:...}) are resolved securely, confined to the directory containing the file.
            if (!string.IsNullOrEmpty(promptyFilePath) && File.Exists(promptyFilePath))
            {
                var fullPath = Path.GetFullPath(promptyFilePath);
                var loadOptions = new PromptyCore.PromptyLoadOptions
                {
                    AllowedFileRoots = [Path.GetDirectoryName(fullPath)!],
                };

                return PromptyCore.PromptyLoader.Load(fullPath, loadOptions);
            }

            // Otherwise parse the frontmatter (and markdown body) directly from the provided text.
            var frontmatter = PromptyCore.FrontmatterParser.Parse(promptyTemplate);
            return PromptyCore.Prompty.Load(frontmatter, new PromptyCore.LoadContext());
        }
        catch (Exception ex) when (ex is not ArgumentException)
        {
            // Normalize parse/format failures (for example, invalid YAML in the frontmatter) to
            // ArgumentException to preserve the plugin's input-validation contract.
            throw new ArgumentException($"Invalid prompty template: {ex.Message}", nameof(promptyTemplate), ex);
        }
    }

    /// <summary>
    /// Converts the strongly typed <see cref="PromptyCore.ModelOptions"/> to the loosely typed extension data
    /// expected by <see cref="PromptExecutionSettings"/> consumers (for example, the OpenAI connector).
    /// Only the strongly typed options are mapped; arbitrary provider-specific options are not forwarded.
    /// </summary>
    private static Dictionary<string, object> ToExtensionData(PromptyCore.ModelOptions? options)
    {
        Dictionary<string, object> extensionData = [];
        if (options is null)
        {
            return extensionData;
        }

        if (options.Temperature is not null) { extensionData["temperature"] = options.Temperature; }
        if (options.TopP is not null) { extensionData["top_p"] = options.TopP; }
        if (options.PresencePenalty is not null) { extensionData["presence_penalty"] = options.PresencePenalty; }
        if (options.FrequencyPenalty is not null) { extensionData["frequency_penalty"] = options.FrequencyPenalty; }
        if (options.MaxOutputTokens is not null) { extensionData["max_tokens"] = options.MaxOutputTokens; }
        if (options.Seed is not null) { extensionData["seed"] = options.Seed; }
        if (options.StopSequences is { Count: > 0 }) { extensionData["stop_sequences"] = options.StopSequences; }

        return extensionData;
    }
    #endregion
}
