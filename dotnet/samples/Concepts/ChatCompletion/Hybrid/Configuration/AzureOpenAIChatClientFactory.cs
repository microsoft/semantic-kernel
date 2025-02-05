// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Serialization;
using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Extensions.AI;

namespace ChatCompletion.Hybrid;

internal sealed class AzureOpenAIChatClientFactory
{
    private readonly AzureOpenAIChatClientConfiguration _config;

    public AzureOpenAIChatClientFactory(IServiceProvider serviceProvider, JsonElement config)
    {
        this._config = config.Deserialize<AzureOpenAIChatClientConfiguration>()!;
    }

    public Microsoft.Extensions.AI.IChatClient Create()
    {
        IChatClient azureOpenAiClient = new AzureOpenAIClient(new Uri(TestConfiguration.AzureOpenAI.Endpoint), new AzureCliCredential()).AsChatClient(TestConfiguration.AzureOpenAI.ChatDeploymentName);

        var builder = new ChatClientBuilder(azureOpenAiClient);

        if (this._config.UseFunctionInvocation)
        {
            builder.UseFunctionInvocation();
        }

        return builder.Build();
    }
}

internal sealed class AzureOpenAIChatClientConfiguration
{
    [JsonPropertyName("useFunctionInvocation")]
    public bool UseFunctionInvocation { get; set; }
}
