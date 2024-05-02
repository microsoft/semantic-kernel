// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using Microsoft.SemanticKernel.PromptTemplates.Liquid;
using Microsoft.SemanticKernel.Prompty.Core;
using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for <see cref="Kernel"/> to create a <see cref="KernelFunction"/> from a prompty file.
/// </summary>
public static class PromptyKernelExtensions
{
    /// <summary>
    /// Create a <see cref="KernelFunction"/> from a prompty file.
    /// </summary>
    /// <param name="kernel">kernel</param>
    /// <param name="promptyFilePath">Prompty template.</param>
    /// <param name="promptTemplateFactory">prompty template factory, if not provided, a <see cref="LiquidPromptTemplateFactory"/> will be used.</param>
    /// <param name="loggerFactory">logger factory</param>
    /// <returns><see cref="KernelFunction"/></returns>
    /// <exception cref="ArgumentNullException"></exception>
    /// <exception cref="NotSupportedException"></exception>
    public static KernelFunction CreateFunctionFromPromptyFile(
        this Kernel kernel,
        string promptyFilePath,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        var promptyTemplate = File.ReadAllText(promptyFilePath);
        return kernel.CreateFunctionFromPrompty(promptyTemplate, promptTemplateFactory, loggerFactory);
    }

    /// <summary>
    /// Create a <see cref="KernelFunction"/> from a prompty file.
    /// </summary>
    /// <param name="kernel">kernel</param>
    /// <param name="promptyTemplate">Prompty template.</param>
    /// <param name="promptTemplateFactory">prompty template factory, if not provided, a <see cref="LiquidPromptTemplateFactory"/> will be used.</param>
    /// <param name="loggerFactory">logger factory</param>
    /// <returns><see cref="KernelFunction"/></returns>
    /// <exception cref="ArgumentNullException"></exception>
    /// <exception cref="NotSupportedException"></exception>
    public static KernelFunction CreateFunctionFromPrompty(
    this Kernel kernel,
    string promptyTemplate,
    IPromptTemplateFactory? promptTemplateFactory = null,
    ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(kernel);

        promptTemplateFactory ??= new AggregatorPromptTemplateFactory(new HandlebarsPromptTemplateFactory(), new LiquidPromptTemplateFactory());

        // create PromptTemplateConfig from text
        // step 1
        // retrieve the header, which is in yaml format and put between ---
        //
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
        //     azure_deployment: gpt - 35 - turbo
        //     api_version: 2023 - 07 - 01 - preview
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

        var splits = promptyTemplate.Split(["---"], StringSplitOptions.RemoveEmptyEntries);
        var yaml = splits[0];
        var content = splits[1];

        var deserializer = new DeserializerBuilder().Build();
        var prompty = deserializer.Deserialize<PromptyYaml>(yaml);

        // step 2
        // create a prompt template config from the prompty object
        var promptTemplateConfig = new PromptTemplateConfig
        {
            Name = prompty.Name, // TODO: sanitize name
            Description = prompty.Description,
            Template = content,
        };

        PromptExecutionSettings? defaultExecutionSetting = null;
        if (prompty.Model?.ModelConfiguration?.ModelType is ModelType.azure_openai || prompty.Model?.ModelConfiguration?.ModelType is ModelType.openai)
        {
            defaultExecutionSetting = new PromptExecutionSettings
            {
                ModelId = prompty.Model?.ModelConfiguration?.AzureDeployment,
            };

            var extensionData = new Dictionary<string, object>();
            extensionData.Add("temperature", prompty.Model?.Parameters?.Temperature ?? 1.0);
            extensionData.Add("top_p", prompty.Model?.Parameters?.TopP ?? 1.0);
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

        // step 3. add input variables
        if (prompty.Inputs != null)
        {
            foreach (var input in prompty.Inputs)
            {
                if (input.Value is string description)
                {
                    var inputVariable = new InputVariable()
                    {
                        Name = input.Key,
                        Description = description,
                    };

                    promptTemplateConfig.InputVariables.Add(inputVariable);
                }
            }
        }

        // step 4. update template format, if not provided, use Liquid as default
        var templateFormat = prompty.Template ?? LiquidPromptTemplateFactory.LiquidTemplateFormat;
        promptTemplateConfig.TemplateFormat = templateFormat;

        return KernelFunctionFactory.CreateFromPrompt(promptTemplateConfig, promptTemplateFactory, loggerFactory);
    }
}
