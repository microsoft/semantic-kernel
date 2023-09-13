// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;
using Microsoft.SemanticKernel.SemanticFunctions;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example57_ConfigureRequestSettings
{
    /// <summary>
    /// Show how to configure model request settings
    /// </summary>
    public static async Task RunAsync()
    {
        Console.WriteLine("======== Example57_ConfigureRequestSettings ========");

        string serviceId = TestConfiguration.AzureOpenAI.ServiceId;
        string apiKey = TestConfiguration.AzureOpenAI.ApiKey;
        string chatDeploymentName = TestConfiguration.AzureOpenAI.ChatDeploymentName;
        string endpoint = TestConfiguration.AzureOpenAI.Endpoint;

        if (serviceId == null || apiKey == null || chatDeploymentName == null || endpoint == null)
        {
            Console.WriteLine("Azure serviceId, endpoint, apiKey, or deploymentName not found. Skipping example.");
            return;
        }

        IKernel kernel = Kernel.Builder
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithAzureChatCompletionService(
                deploymentName: chatDeploymentName,
                endpoint: endpoint,
                serviceId: serviceId,
                apiKey: apiKey)
            .Build();

        var prompt = "Hello AI, what can you do for me?";

        // Option 1:
        // Invoke the semantic function and pass an AnonymousType containing the request settings
        var result = await kernel.InvokeSemanticFunctionAsync("Hello AI, what can you do for me?", requestSettings: new { max_tokens = 16, temperature = 0.7 });
        Console.WriteLine(result.LastException is not null ? result.LastException.Message : result.Result);

        // Option 2:
        // Invoke the semantic function and pass an OpenAI specific instance containing the request settings
        result = await kernel.InvokeSemanticFunctionAsync(prompt, requestSettings: new OpenAITextRequestSettings() { MaxTokens = 256, Temperature = 0.7 });
        Console.WriteLine(result.LastException is not null ? result.LastException.Message : result.Result);

        // Option 3:
        // Load prompt template configuration including the request settings from a JSON payload
        // Create the semantic functions using the prompt template and the configuration (loaded in the previous step)
        // Invoke the semantic function using the implicitly set request settings
        string configPayload = @"{
          ""schema"": 1,
          ""description"": ""Say hello to an AI"",
          ""type"": ""completion"",
          ""completion"": {
            ""max_tokens"": 60,
            ""temperature"": 0.5,
            ""top_p"": 0.0,
            ""presence_penalty"": 0.0,
            ""frequency_penalty"": 0.0
          }
        }";
        var templateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);
        var func = kernel.CreateSemanticFunction(prompt, config: templateConfig!, "HelloAI");

        result = await kernel.RunAsync(func);
        Console.WriteLine(result.LastException is not null ? result.LastException.Message : result.Result);

        /* OUTPUT (using gpt4):
Hello! As an AI language model, I can help you with a variety of
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
