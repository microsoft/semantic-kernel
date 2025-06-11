// Copyright (c) Microsoft. All rights reserved.
using System.Reflection;
using A2A;
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using SharpA2A.AspNetCore;
using SharpA2A.Core;

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
    var invoiceAgent = new AzureAIInvoiceAgent(logger);
    var invoiceAgentId = configuration["A2AServer:InvoiceAgentId"] ?? throw new ArgumentException("A2AServer:InvoiceAgentId must be provided");
    await invoiceAgent.InitializeAgentAsync(modelId, endpoint, invoiceAgentId);
    var invoiceTaskManager = new TaskManager();
    invoiceAgent.Attach(invoiceTaskManager);
    app.MapA2A(invoiceTaskManager, "/invoice");

    var policyAgent = new AzureAIPolicyAgent(logger);
    var policyAgentId = configuration["A2AServer:PolicyAgentId"] ?? throw new ArgumentException("A2AServer:PolicyAgentId must be provided");
    await policyAgent.InitializeAgentAsync(modelId, endpoint, policyAgentId);
    var policyTaskManager = new TaskManager();
    policyAgent.Attach(policyTaskManager);
    app.MapA2A(policyTaskManager, "/policy");

    var logisticsAgent = new AzureAILogisticsAgent(logger);
    var logisticsAgentId = configuration["A2AServer:LogisticsAgentId"] ?? throw new ArgumentException("A2AServer:LogisticsAgentId must be provided");
    await logisticsAgent.InitializeAgentAsync(modelId, endpoint, logisticsAgentId);
    var logisticsTaskManager = new TaskManager();
    logisticsAgent.Attach(logisticsTaskManager);
    app.MapA2A(logisticsTaskManager, "/logistics");
}
else if (!string.IsNullOrEmpty(apiKey))
{
    var invoiceAgent = new InvoiceAgent(logger);
    invoiceAgent.InitializeAgent(modelId, apiKey);
    var invoiceTaskManager = new TaskManager();
    invoiceAgent.Attach(invoiceTaskManager);
    app.MapA2A(invoiceTaskManager, "/invoice");

    var policyAgent = new PolicyAgent(logger);
    policyAgent.InitializeAgent(modelId, apiKey);
    var policyTaskManager = new TaskManager();
    policyAgent.Attach(policyTaskManager);
    app.MapA2A(policyTaskManager, "/policy");

    var logisticsAgent = new LogisticsAgent(logger);
    logisticsAgent.InitializeAgent(modelId, apiKey);
    var logisticsTaskManager = new TaskManager();
    logisticsAgent.Attach(logisticsTaskManager);
    app.MapA2A(logisticsTaskManager, "/logistics");
}
else
{
    Console.Error.WriteLine("Either  A2AServer:ApiKey or A2AServer:ConnectionString must be provided");
}

await app.RunAsync();
