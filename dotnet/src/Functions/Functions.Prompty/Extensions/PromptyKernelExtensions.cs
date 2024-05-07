// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using Microsoft.SemanticKernel.PromptTemplates.Liquid;
using Microsoft.SemanticKernel.Prompty.Core;
using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for creating <see cref="KernelFunction"/>s from the Prompty template format.
/// </summary>
public static class PromptyKernelExtensions
{
    /// <summary>Default template factory to use when none is provided.</summary>
    private static readonly AggregatorPromptTemplateFactory s_defaultTemplateFactory =
        new(new LiquidPromptTemplateFactory(), new HandlebarsPromptTemplateFactory());

    /// <summary>Regex for parsing the YAML frontmatter and content from the prompty template.</summary>
    private static readonly Regex s_promptyRegex = new("""
        ^---\s*$\n      # Start of YAML front matter, a line beginning with "---" followed by optional whitespace
        (?<header>.*?)  # Capture the YAML front matter, everything up to the next "---" line
        ^---\s*$\n      # End of YAML front matter, a line beginning with "---" followed by optional whitespace
        (?<content>.*)  # Capture the content after the YAML front matter
        """,
        RegexOptions.Multiline | RegexOptions.Singleline | RegexOptions.IgnorePatternWhitespace | RegexOptions.Compiled);

    /// <summary>
    /// Create a <see cref="KernelFunction"/> from a prompty template file.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptyFilePath">Path to the file containing the Prompty representation of a prompt based <see cref="KernelFunction"/>.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the prompt template configuration into a <see cref="IPromptTemplate"/>.
    /// If null, a <see cref="AggregatorPromptTemplateFactory"/> will be used with support for Liquid and Handlebars prompt templates.
    /// </param>
    /// <returns>The created <see cref="KernelFunction"/>.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="kernel"/> is null.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="promptyFilePath"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="promptyFilePath"/> is empty or composed entirely of whitespace.</exception>
    public static KernelFunction CreateFunctionFromPromptyFile(
        this Kernel kernel,
        string promptyFilePath,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNullOrWhiteSpace(promptyFilePath);

        var promptyTemplate = File.ReadAllText(promptyFilePath);
        return kernel.CreateFunctionFromPrompty(promptyTemplate, promptTemplateFactory);
    }

    /// <summary>
    /// Create a <see cref="KernelFunction"/> from a prompty template.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptyTemplate">Prompty representation of a prompt-based <see cref="KernelFunction"/>.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the prompt template configuration into a <see cref="IPromptTemplate"/>.
    /// If null, a <see cref="AggregatorPromptTemplateFactory"/> will be used with support for Liquid and Handlebars prompt templates.
    /// </param>
    /// <returns>The created <see cref="KernelFunction"/>.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="kernel"/> is null.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="promptyTemplate"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="promptyTemplate"/> is empty or composed entirely of whitespace.</exception>
    public static KernelFunction CreateFunctionFromPrompty(
        this Kernel kernel,
        string promptyTemplate,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNullOrWhiteSpace(promptyTemplate);

        // Step 1:
        // Create PromptTemplateConfig from text.
        // Retrieve the header, which is in yaml format and put between ---
        // e.g
        // file: chat.prompty
        // ---
        // name: Contoso Chat Prompt
        // description: A retail assistant for Contoso Outdoors products retailer.
        // authors:
        //   - XXXX
        // model:
        //   api: chat
        //   configuration:
        //     type: azure_openai
        //     azure_deployment: gpt-35-turbo
        //     api_version: 2023-07-01-preview
        //   parameters:
        //     tools_choice: auto
        //     tools:
        //     -type: function
        //       function:
        //         name: test
        //         description: test function
        //         parameters:
        //           properties:
        //             location:
        //               description: The city and state or city and country, e.g.San Francisco, CA
        //                 or Tokyo, Japan
        // ---
        // ... (rest of the prompty content)

        // Parse the YAML frontmatter and content from the prompty template
        Match m = s_promptyRegex.Match(promptyTemplate);
        if (!m.Success)
        {
            throw new ArgumentException("Invalid prompty template. Header and content could not be parsed.");
        }

        var header = m.Groups["header"].Value;
        var content = m.Groups["content"].Value;

        var prompty = new DeserializerBuilder().Build().Deserialize<PromptyYaml>(header);
        if (prompty is null)
        {
            throw new ArgumentException("Invalid prompty template. Header could not be parsed.");
        }

        // Step 2:
        // Create a prompt template config from the prompty data.
        var promptTemplateConfig = new PromptTemplateConfig
        {
            Name = prompty.Name, // TODO: sanitize name
            Description = prompty.Description,
            Template = content,
        };

        PromptExecutionSettings? defaultExecutionSetting = null;
        if (prompty.Model?.ModelConfiguration?.ModelType is ModelType.azure_openai or ModelType.openai)
        {
            defaultExecutionSetting = new PromptExecutionSettings
            {
                ModelId = prompty.Model.ModelConfiguration.ModelType is ModelType.azure_openai ?
                    prompty.Model.ModelConfiguration.AzureDeployment :
                    prompty.Model.ModelConfiguration.Name
            };

            var extensionData = new Dictionary<string, object>();

            if (prompty.Model?.Parameters?.Temperature is double temperature)
            {
                extensionData.Add("temperature", temperature);
            }

            if (prompty.Model?.Parameters?.TopP is double topP)
            {
                extensionData.Add("top_p", topP);
            }

            if (prompty.Model?.Parameters?.MaxTokens is int maxTokens)
            {
                extensionData.Add("max_tokens", maxTokens);
            }

            if (prompty.Model?.Parameters?.Seed is int seed)
            {
                extensionData.Add("seed", seed);
            }

            if (prompty.Model?.Parameters?.FrequencyPenalty is double frequencyPenalty)
            {
                extensionData.Add("frequency_penalty", frequencyPenalty);
            }

            if (prompty.Model?.Parameters?.PresencePenalty is double presencePenalty)
            {
                extensionData.Add("presence_penalty", presencePenalty);
            }

            if (prompty.Model?.Parameters?.Stop is List<string> stop)
            {
                extensionData.Add("stop_sequences", stop);
            }

            if (prompty.Model?.Parameters?.ResponseFormat == "json_object")
            {
                extensionData.Add("response_format", "json_object");
            }

            defaultExecutionSetting.ExtensionData = extensionData;
            promptTemplateConfig.AddExecutionSettings(defaultExecutionSetting);
        }

        // Step 3:
        // Add input and output variables.
        if (prompty.Inputs is not null)
        {
            foreach (var input in prompty.Inputs)
            {
                if (input.Value is string description)
                {
                    promptTemplateConfig.InputVariables.Add(new()
                    {
                        Name = input.Key,
                        Description = description,
                    });
                }
            }
        }

        if (prompty.Outputs is not null)
        {
            // PromptTemplateConfig supports only a single output variable. If the prompty template
            // contains one and only one, use it. Otherwise, ignore any outputs.
            if (prompty.Outputs.Count == 1 &&
                prompty.Outputs.First().Value is string description)
            {
                promptTemplateConfig.OutputVariable = new() { Description = description };
            }
        }

        // Step 4:
        // Update template format. If not provided, use Liquid as default.
        promptTemplateConfig.TemplateFormat = prompty.Template ?? LiquidPromptTemplateFactory.LiquidTemplateFormat;

        return KernelFunctionFactory.CreateFromPrompt(
            promptTemplateConfig,
            promptTemplateFactory ?? s_defaultTemplateFactory,
            kernel.LoggerFactory);
    }
}
