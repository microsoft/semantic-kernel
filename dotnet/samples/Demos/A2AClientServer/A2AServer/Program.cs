// Copyright (c) Microsoft. All rights reserved.
using System.Reflection;
using A2A;
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using SharpA2A.AspNetCore;
using SharpA2A.Core;

string agentId = string.Empty;
string agentType = string.Empty;

for (var i = 0; i < args.Length; i++)
{
    if (args[i].StartsWith("--agentId", StringComparison.InvariantCultureIgnoreCase) && i + 1 < args.Length)
    {
        agentId = args[++i];
    }
    else if (args[i].StartsWith("--agentType", StringComparison.InvariantCultureIgnoreCase) && i + 1 < args.Length)
    {
        agentType = args[++i];
    }
}

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddHttpClient().AddLogging();
var app = builder.Build();

var httpClient = app.Services.GetRequiredService<IHttpClientFactory>().CreateClient();
var logger = app.Logger;

IConfigurationRoot configuration = new ConfigurationBuilder()
    .AddEnvironmentVariables()
    .AddUserSecrets(Assembly.GetExecutingAssembly())
    .Build();

string? apiKey = configuration["A2AServer:ApiKey"];
string? endpoint = configuration["A2AServer:Endpoint"];
string modelId = configuration["A2AServer:ModelId"] ?? "gpt-4o-mini";

if (!string.IsNullOrEmpty(endpoint))
{
    AzureAIHostAgent hostAgent = agentType.ToUpperInvariant() switch
    {
        "INVOICE" => new AzureAIInvoiceAgent(logger),
        "POLICY" => new AzureAIPolicyAgent(logger),
        "LOGISTICS" => new AzureAILogisticsAgent(logger),
        _ => throw new ArgumentException($"Unsupported agent type: {agentType}"),
    };

    await hostAgent.InitializeAgentAsync(modelId, endpoint, agentId);
    var taskManager = new TaskManager();
    hostAgent.Attach(taskManager);
    app.MapA2A(taskManager, "");
}
else if (!string.IsNullOrEmpty(apiKey))
{
    ChatCompletionHostAgent hostAgent = agentType.ToUpperInvariant() switch
    {
        "INVOICE" => new InvoiceAgent(logger),
        "POLICY" => new PolicyAgent(logger),
        "LOGISTICS" => new LogisticsAgent(logger),
        _ => throw new ArgumentException($"Unsupported agent type: {agentType}"),
    };

    hostAgent.InitializeAgent(modelId, apiKey);
    var taskManager = new TaskManager();
    hostAgent.Attach(taskManager);
    app.MapA2A(taskManager, "");
}
else
{
    Console.Error.WriteLine("Either  A2AServer:ApiKey or A2AServer:ConnectionString must be provided");
}

await app.RunAsync();
