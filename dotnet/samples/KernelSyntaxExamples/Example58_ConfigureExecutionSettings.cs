// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;

// ReSharper disable once InconsistentNaming
public static class Example58_ConfigureExecutionSettings
{
    /// <summary>
    /// Show how to configure model execution settings
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Example58_ConfigureExecutionSettings ========");

        string serviceId = TestConfiguration.AzureOpenAI.ServiceId;
        string apiKey = TestConfiguration.AzureOpenAI.ApiKey;
        string chatDeploymentName = TestConfiguration.AzureOpenAI.ChatDeploymentName;
        string chatModelId = TestConfiguration.AzureOpenAI.ChatModelId;
        string endpoint = TestConfiguration.AzureOpenAI.Endpoint;

        if (apiKey == null || chatDeploymentName == null || chatModelId == null || endpoint == null)
        {
            Console.WriteLine("AzureOpenAI modelId, endpoint, apiKey, or deploymentName not found. Skipping example.");
            return;
        }

        Kernel kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                deploymentName: chatDeploymentName,
                endpoint: endpoint,
                serviceId: serviceId,
                apiKey: apiKey,
                modelId: chatModelId)
            .Build();

        var prompt = "Hello AI, what can you do for me?";

        // Option 1:
        // Invoke the prompt function and pass an OpenAI specific instance containing the execution settings
        var result = await kernel.InvokePromptAsync(
            prompt,
            new(new OpenAIPromptExecutionSettings()
            {
                MaxTokens = 60,
                Temperature = 0.7
            }));
        Console.WriteLine(result.GetValue<string>());

        // Option 2:
        // Load prompt template configuration including the execution settings from a JSON payload
        // Create the prompt functions using the prompt template and the configuration (loaded in the previous step)
        // Invoke the prompt function using the implicitly set execution settings
        string configPayload = @"{
          ""schema"": 1,
          ""name"": ""HelloAI"",
          ""description"": ""Say hello to an AI"",
          ""type"": ""completion"",
          ""completion"": {
            ""max_tokens"": 256,
            ""temperature"": 0.5,
            ""top_p"": 0.0,
            ""presence_penalty"": 0.0,
            ""frequency_penalty"": 0.0
          }
        }";
        var promptConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload)!;
        promptConfig.Template = prompt;
        var func = kernel.CreateFunctionFromPrompt(promptConfig);

        result = await kernel.InvokeAsync(func);
        Console.WriteLine(result.GetValue<string>());

        /* OUTPUT (using gpt4):
Hello! As an AI language model, I can help you with a variety of tasks, such as:

1. Answering general questions and providing information on a wide range of topics.
2. Assisting with problem-solving and brainstorming ideas.
3. Offering recommendations for books, movies, music, and more.
4. Providing definitions, explanations, and examples of various concepts.
5. Helping with language-related tasks, such as grammar, vocabulary, and writing tips.
6. Generating creative content, such as stories, poems, or jokes.
7. Assisting with basic math and science problems.
8. Offering advice on various topics, such as productivity, motivation, and personal development.

Please feel free to ask me anything, and I'll do my best to help you!
Hello! As an AI language model, I can help you with a variety of tasks, including:

1. Answering general questions and providing information on a wide range of topics.
2. Offering suggestions and recommendations.
3. Assisting with problem-solving and brainstorming ideas.
4. Providing explanations and
         */
    }
}
