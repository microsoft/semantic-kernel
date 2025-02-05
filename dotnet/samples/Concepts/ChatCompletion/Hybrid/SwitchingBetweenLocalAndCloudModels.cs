// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using System.ClientModel.Primitives;
using System.ComponentModel;
using Azure.AI.OpenAI;
using Azure.Identity;
using ChatCompletion.Hybrid;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI;

namespace ChatCompletion;

public sealed class SwitchingBetweenLocalAndCloudModels(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task FallbackToAvailableModelAsync()
    {
        // Create an unavailable chat client
        IChatClient unavailableChatClient = CreateUnavailableOpenAIChatClient();

        // Create a cloud available chat client
        IChatClient cloudChatClient = CreateAzureOpenAIChatClient();

        CustomFallbackEvaluator fallbackEvaluator = new((context) => context.Exception is ClientResultException clientResultException && clientResultException.Status >= 500);

        FallbackChatCompletionHandler handler = new() { FallbackEvaluator = fallbackEvaluator };

        IChatClient hybridChatClient = new HybridChatClient([unavailableChatClient, cloudChatClient], handler);

        ChatOptions chatOptions = new() { Tools = [AIFunctionFactory.Create(GetWeather, new AIFunctionFactoryCreateOptions { Name = "GetWeather" })] };

        var result = await hybridChatClient.CompleteAsync("Do I need an umbrella?", chatOptions);

        Output.WriteLine(result);

        [Description("Gets the weather")]
        string GetWeather() => "It's sunny";
    }

    [Fact]
    public async Task FallbackToAvailableModelStreamingAsync()
    {
        // Create an unavailable chat client
        IChatClient unavailableChatClient = CreateUnavailableOpenAIChatClient();

        // Create a cloud available chat client
        IChatClient cloudChatClient = CreateAzureOpenAIChatClient();

        CustomFallbackEvaluator fallbackEvaluator = new((context) => context.Exception is ClientResultException clientResultException && clientResultException.Status >= 500);

        FallbackChatCompletionHandler handler = new() { FallbackEvaluator = fallbackEvaluator };

        IChatClient hybridChatClient = new HybridChatClient([unavailableChatClient, cloudChatClient], handler);

        ChatOptions chatOptions = new() { Tools = [AIFunctionFactory.Create(GetWeather, new AIFunctionFactoryCreateOptions { Name = "GetWeather" })] };

        var result = hybridChatClient.CompleteStreamingAsync("Do I need an umbrella?", chatOptions);

        await foreach (var update in result)
        {
            Output.WriteLine(update);
        }

        [Description("Gets the weather")]
        string GetWeather() => "It's sunny";
    }

    [Fact]
    public async Task BuildHybridChatClientFromDeclarationAsync()
    {
        using var configSource = new MemoryStream(System.Text.Encoding.UTF8.GetBytes("""
        {
            "services": [ 
                {
                    "serviceKey": "openAIClient",
                    "type": "Microsoft.Extensions.AI.IChatClient, Microsoft.Extensions.AI.Abstractions",  
                    "lifetime": "Singleton",
                    "factory": {
                        "type": "ChatCompletion.Hybrid.OpenAIChatClientFactory, Concepts",
                        "configuration": {
                            "useFunctionInvocation": true
                        }
                    }
                },
                {
                    "serviceKey": "azureOpenAIClient",
                    "type": "Microsoft.Extensions.AI.IChatClient, Microsoft.Extensions.AI.Abstractions",  
                    "lifetime": "Singleton",
                    "factory": {
                        "type": "ChatCompletion.Hybrid.AzureOpenAIChatClientFactory, Concepts",
                        "configuration": {
                            "useFunctionInvocation": true
                        }
                    }
                },
                {
                    "serviceKey": "hybridChatClient",
                    "type": "Microsoft.Extensions.AI.IChatClient, Microsoft.Extensions.AI.Abstractions",  
                    "lifetime": "Singleton",
                    "factory": {
                        "type": "ChatCompletion.Hybrid.HybridChatClientFactory, Concepts",
                        "configuration": {
                            "clients": ["openAIClient", "azureOpenAIClient"]
                        }
                    }
                }
            ]  
        }  
        """));

        var services = new ServiceCollection();

        ServiceRegistry.RegisterServices(services, configSource);

        var serviceProvider = services.BuildServiceProvider();

        var hybridChatClient = serviceProvider.GetRequiredKeyedService<IChatClient>("hybridChatClient");

        ChatOptions chatOptions = new() { Tools = [AIFunctionFactory.Create(GetWeather, new AIFunctionFactoryCreateOptions { Name = "GetWeather" })] };

        var result = await hybridChatClient.CompleteAsync("Do I need an umbrella?", chatOptions);

        Output.WriteLine(result);

        [Description("Gets the weather")]
        string GetWeather() => "It's sunny";
    }

    private static IChatClient CreateUnavailableOpenAIChatClient()
    {
        OpenAIClientOptions options = new()
        {
            Transport = new HttpClientPipelineTransport(
                new HttpClient
                (
                    new StubHandler(new HttpClientHandler(), async (response) => { response.StatusCode = System.Net.HttpStatusCode.ServiceUnavailable; })
                )
            )
        };

        IChatClient openAiClient = new OpenAIClient(new ApiKeyCredential(TestConfiguration.OpenAI.ApiKey), options).AsChatClient(TestConfiguration.OpenAI.ChatModelId);

        openAiClient = new ChatClientBuilder(openAiClient)
            .UseFunctionInvocation()
            .Build();
        return openAiClient;
    }

    private static IChatClient CreateOpenAIChatClient()
    {
        IChatClient openAiClient = new OpenAIClient(TestConfiguration.OpenAI.ApiKey).AsChatClient(TestConfiguration.OpenAI.ChatModelId);
        openAiClient = new ChatClientBuilder(openAiClient)
            .UseFunctionInvocation()
            .Build();
        return openAiClient;
    }

    private static IChatClient CreateAzureOpenAIChatClient()
    {
        IChatClient azureOpenAiClient = new AzureOpenAIClient(new Uri(TestConfiguration.AzureOpenAI.Endpoint), new AzureCliCredential()).AsChatClient(TestConfiguration.AzureOpenAI.ChatDeploymentName);
        azureOpenAiClient = new ChatClientBuilder(azureOpenAiClient)
            .UseFunctionInvocation()
            .Build();
        return azureOpenAiClient;
    }

    protected sealed class StubHandler(HttpMessageHandler innerHandler, Func<HttpResponseMessage, Task> handler) : DelegatingHandler(innerHandler)
    {
        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            var result = await base.SendAsync(request, cancellationToken);

            await handler(result);

            return result;
        }
    }
}
