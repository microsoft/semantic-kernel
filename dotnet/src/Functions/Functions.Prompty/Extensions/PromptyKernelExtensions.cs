// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using Azure.AI.OpenAI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;
using Microsoft.SemanticKernel.PromptTemplates.Liquid;
using Microsoft.SemanticKernel.Prompty.Core;
using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Prompty.Extension;

/// <summary>
/// Extension methods for <see cref="Kernel"/> to create a <see cref="KernelFunction"/> from a prompty file.
/// </summary>
public static class PromptyKernelExtensions
{
    /// <summary>
    /// Create a <see cref="KernelFunction"/> from a prompty file.
    /// </summary>
    /// <param name="kernel">kernel</param>
    /// <param name="promptyPath">path to prompty file.</param>
    /// <param name="promptTemplateFactory">prompty template factory, if not provided, a <see cref="LiquidPromptTemplateFactory"/> will be used.</param>
    /// <param name="loggerFactory">logger factory</param>
    /// <returns><see cref="KernelFunction"/></returns>
    /// <exception cref="ArgumentNullException"></exception>
    /// <exception cref="NotSupportedException"></exception>
    public static KernelFunction CreateFunctionFromPrompty(
        this Kernel kernel,
        string promptyPath,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(kernel);

        var text = File.ReadAllText(promptyPath);

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

        var splits = text.Split(["---"], StringSplitOptions.RemoveEmptyEntries);
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

        PromptExecutionSettings defaultExecutionSetting = prompty.Model?.ModelConfiguration?.ModelType switch
        {
            ModelType.azure_openai or ModelType.openai => new OpenAIPromptExecutionSettings()
            {
                ResponseFormat = prompty.Model?.Parameters?.ResponseFormat == "json_object" ? ChatCompletionsResponseFormat.JsonObject : null,
                Temperature = prompty.Model?.Parameters?.Temperature ?? 1.0,
                TopP = prompty.Model?.Parameters?.TopP ?? 1.0,
                MaxTokens = prompty.Model?.Parameters?.MaxTokens,
                Seed = prompty.Model?.Parameters?.Seed,
                ModelId = prompty.Model?.ModelConfiguration?.AzureDeployment,
            },
            _ => throw new NotSupportedException($"Model type '{prompty.Model?.ModelConfiguration?.ModelType}' is not supported."),
        };

        promptTemplateConfig.AddExecutionSettings(defaultExecutionSetting);

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
