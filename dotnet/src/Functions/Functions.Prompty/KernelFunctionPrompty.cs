// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
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

        Dictionary<string, object> globalConfig = [];
        PromptyCore.Prompty prompty = PromptyCore.Prompty.Load(promptyTemplate, globalConfig, promptyFilePath);

        var promptTemplateConfig = new PromptTemplateConfig
        {
            Name = prompty.Name,
            Description = prompty.Description,
            Template = prompty.Content.ToString() ?? string.Empty,
        };

        PromptExecutionSettings? defaultExecutionSetting = null;
        if (prompty.Model?.Id is not null || prompty.Model?.Connection?.ServiceId is not null || prompty.Model?.Options?.Count > 0)
        {
            defaultExecutionSetting = new PromptExecutionSettings()
            {
                ModelId = prompty.Model.Id,
                ServiceId = prompty.Model.Connection?.ServiceId,
                ExtensionData = prompty.Model.Options,
            };
            promptTemplateConfig.AddExecutionSettings(defaultExecutionSetting);
        }

        // Add input and output variables.
        if (prompty.Inputs is not null)
        {
            foreach (var kvp in prompty.Inputs)
            {
                var input = kvp.Value;
                promptTemplateConfig.InputVariables.Add(new()
                {
                    Name = kvp.Key,
                    Default = input.Default,
                    IsRequired = input.Required,
                    Description = input.Description,
                    AllowDangerouslySetContent = !input.Strict,
                    JsonSchema = ToJsonSchema(input.JsonSchema),
                });
            }
        }
        if (prompty.Outputs is not null)
        {
            // PromptTemplateConfig supports only a single output variable. If the prompty template
            // contains one and only one, use it. Otherwise, ignore any outputs.
            if (prompty.Outputs.Count == 1)
            {
                var output = prompty.Outputs.Values.First();
                promptTemplateConfig.OutputVariable = new()
                {
                    Description = output.Description,
                    JsonSchema = ToJsonSchema(output.JsonSchema),
                };
            }
        }

        // Update template format. If not provided, use Liquid as default.
        promptTemplateConfig.TemplateFormat = prompty.Template?.Format ?? LiquidPromptTemplateFactory.LiquidTemplateFormat;

        return promptTemplateConfig;
    }

    #region private
    private static string? ToJsonSchema(object? input)
    {
        if (input is null)
        {
            return null;
        }

        if (input is string str)
        {
            return str;
        }

        return JsonSerializer.Serialize(input);
    }
    #endregion
}
