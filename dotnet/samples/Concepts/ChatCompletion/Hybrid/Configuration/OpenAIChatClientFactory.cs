// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.AI;
using OpenAI;

namespace ChatCompletion.Hybrid;

internal sealed class OpenAIChatClientFactory
{
    private readonly OpenAIChatClientConfiguration _config;

    public OpenAIChatClientFactory(IServiceProvider serviceProvider, JsonElement config)
    {
        this._config = config.Deserialize<OpenAIChatClientConfiguration>()!;
    }

    public Microsoft.Extensions.AI.IChatClient Create()
    {
        IChatClient openAiClient = new OpenAIClient(new ApiKeyCredential(TestConfiguration.OpenAI.ApiKey)).AsChatClient(TestConfiguration.OpenAI.ChatModelId);

        var builder = new ChatClientBuilder(openAiClient);

        if (this._config.UseFunctionInvocation)
        {
            builder.UseFunctionInvocation();
        }

        return builder.Build();
    }
}

internal sealed class OpenAIChatClientConfiguration
{
    [JsonPropertyName("useFunctionInvocation")]
    public bool UseFunctionInvocation { get; set; }
}
