// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Skills.Core;
using Microsoft.SemanticKernel.TemplateEngine.Prompt;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example56_TemplateNativeFunctionsWithMultipleArguments
{
    /// <summary>
    /// Show how to invoke a Native Function written in C# with multiple arguments
    /// from a Semantic Function written in natural language
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine("======== TemplateNativeFunctionsWithMultipleArguments ========");

        string serviceId = TestConfiguration.AzureOpenAI.ServiceId;
        string apiKey = TestConfiguration.AzureOpenAI.ApiKey;
        string deploymentName = TestConfiguration.AzureOpenAI.DeploymentName;
        string endpoint = TestConfiguration.AzureOpenAI.Endpoint;

        if (serviceId == null || apiKey == null || deploymentName == null || endpoint == null)
        {
            Console.WriteLine("Azure serviceId, endpoint, apiKey, or deploymentName not found. Skipping example.");
            return;
        }

        IKernel kernel = Kernel.Builder
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureChatCompletionService(
                deploymentName: deploymentName,
                endpoint: endpoint,
                serviceId: serviceId,
                apiKey: apiKey)
            .Build();

        var variableName = "word2";
        var variableValue = " Potter";
        var context = kernel.CreateNewContext();
        context.Variables[variableName] = variableValue;

        // Load native skill into the kernel skill collection, sharing its functions with prompt templates
        // Functions loaded here are available as "text.*"
        kernel.ImportSkill(new TextSkill(), "text");

        // Semantic Function invoking text.Concat native function with named arguments input and input2 where input is a string and input2 is set to a variable from context called word2.
        const string FunctionDefinition = @"
 Write a haiku about the following: {{text.Concat input='Harry' input2=$word2}}
";

        // This allows to see the prompt before it's sent to OpenAI
        Console.WriteLine("--- Rendered Prompt");
        var promptRenderer = new PromptTemplateEngine();
        var renderedPrompt = await promptRenderer.RenderAsync(FunctionDefinition, context);
        Console.WriteLine(renderedPrompt);

        // Run the prompt / semantic function
        var haiku = kernel.CreateSemanticFunction(FunctionDefinition, requestSettings: new { MaxTokens = 100 });

        // Show the result
        Console.WriteLine("--- Semantic Function result");
        var result = await kernel.RunAsync(context.Variables, haiku);
        Console.WriteLine(result);

        /* OUTPUT:

--- Rendered Prompt

 Write a haiku about the following: Harry Potter

--- Semantic Function result
A boy with a scar,
Wizarding world he explores,
Harry Potter's tale.
         */
    }
}
