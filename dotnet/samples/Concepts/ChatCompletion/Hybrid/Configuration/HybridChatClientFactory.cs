// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ChatCompletion.Hybrid;

internal sealed class HybridChatClientFactory
{
    private readonly HybridChatClientConfiguration _configuration;
    private readonly IServiceProvider _serviceProvider;

    public HybridChatClientFactory(IServiceProvider serviceProvider, JsonElement configuration)
    {
        this._serviceProvider = serviceProvider;
        this._configuration = configuration.Deserialize<HybridChatClientConfiguration>()!;
    }

    public Microsoft.Extensions.AI.IChatClient Create()
    {
        // The evaluator and handler should be created based on the configuration
        CustomFallbackEvaluator fallbackEvaluator = new((context) => context.Exception is ClientResultException clientResultException && clientResultException.Status >= 500);

        FallbackChatCompletionHandler handler = new() { FallbackEvaluator = fallbackEvaluator };

        var chatClients = this._configuration.Clients.Select(this._serviceProvider.GetRequiredKeyedService<IChatClient>);

        var kernel = this._serviceProvider.GetService<Kernel>();

        return new HybridChatClient(chatClients, handler, kernel);
    }
}

internal sealed class HybridChatClientConfiguration
{
    [JsonPropertyName("clients")]
    public IEnumerable<string> Clients { get; set; }
}
