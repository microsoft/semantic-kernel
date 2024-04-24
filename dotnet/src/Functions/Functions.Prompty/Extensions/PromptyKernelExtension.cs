// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.Metrics;
using System;
using System.IO;
using System.Reflection;
using Microsoft.SemanticKernel.Experimental.Prompty.Core;
using Microsoft.SemanticKernel.PromptTemplates.Liquid;
using static System.Net.Mime.MediaTypeNames;
using YamlDotNet.Serialization;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Azure.AI.OpenAI;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Prompty.Extension;

public static class PromptyKernelExtension
{
    public static KernelFunction CreateFunctionFromPrompty(
        this Kernel _,
        string promptyPath,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        var text = File.ReadAllText(promptyPath);

        promptTemplateFactory ??= new LiquidPromptTemplateFactory(); // use liquid template factory by default

        // create PromptTemplateConfig from text
        // step 1
        // retrieve the header, which is in yaml format and put between ---
        //
        // e.g
        // file: chat.prompty
        // ---
        // name: Contoso Chat Prompt
        // description: A retail assistent for Contoso Outdoors products retailer.
        // authors:
        //   -Cassie Breviu
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
        var prompty = deserializer.Deserialize<Experimental.Prompty.Core.Prompty>(yaml);

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
                ResponseFormat = prompty.Model?.Response == "json_object" ? ChatCompletionsResponseFormat.JsonObject : null,
                Temperature = prompty.Model?.Parameters?.Temperature ?? 1.0,
                TopP = prompty.Model?.Parameters?.TopP ?? 1.0,
                MaxTokens = prompty.Model?.Parameters?.MaxTokens,
                Seed = prompty.Model?.Parameters?.Seed,
                ModelId = prompty.Model?.ModelConfiguration?.AzureDeployment ?? throw new ArgumentNullException($"{nameof(prompty.Model.ModelConfiguration.AzureDeployment)} is null"),
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

        // step 4. update template format
        // Note: liquid template format is the only supported format for now
        // Once other template formats are supported, this should be updated to be dynamically retrieved from prompty object
        var templateFormat = LiquidPromptTemplateFactory.LiquidTemplateFormat;
        promptTemplateConfig.TemplateFormat = templateFormat;

        return KernelFunctionFactory.CreateFromPrompt(promptTemplateConfig, promptTemplateFactory, loggerFactory);
    }
}
