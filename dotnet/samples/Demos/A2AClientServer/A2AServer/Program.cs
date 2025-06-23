// Copyright (c) Microsoft. All rights reserved.
using System.Reflection;
using A2A;
using A2AServer;
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.A2A;
using SharpA2A.AspNetCore;

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

IEnumerable<KernelPlugin> invoicePlugins = [KernelPluginFactory.CreateFromType<InvoiceQueryPlugin>()];

A2AHostAgent? hostAgent = null;
if (!string.IsNullOrEmpty(endpoint))
{
    hostAgent = agentType.ToUpperInvariant() switch
    {
        "INVOICE" => await HostAgentFactory.CreateHostAgentAsync(agentType, modelId, endpoint, agentId, invoicePlugins),
        "POLICY" => await HostAgentFactory.CreateHostAgentAsync(agentType, modelId, endpoint, agentId),
        "LOGISTICS" => await HostAgentFactory.CreateHostAgentAsync(agentType, modelId, endpoint, agentId),
        _ => throw new ArgumentException($"Unsupported agent type: {agentType}"),
    };
}
else if (!string.IsNullOrEmpty(apiKey))
{
    hostAgent = agentType.ToUpperInvariant() switch
    {
        "INVOICE" => await HostAgentFactory.CreateHostAgentAsync(
            agentType, modelId, apiKey, "InvoiceAgent",
            """
            You specialize in handling queries related to invoices.
            """, invoicePlugins),
        "POLICY" => await HostAgentFactory.CreateHostAgentAsync(
            agentType, modelId, apiKey, "PolicyAgent",
            """
            You specialize in handling queries related to policies and customer communications.
            
            Always reply with exactly this text:
            
            Policy: Short Shipment Dispute Handling Policy V2.1
            
            Summary: "For short shipments reported by customers, first verify internal shipment records
            (SAP) and physical logistics scan data (BigQuery). If discrepancy is confirmed and logistics data
            shows fewer items packed than invoiced, issue a credit for the missing items. Document the
            resolution in SAP CRM and notify the customer via email within 2 business days, referencing the
            original invoice and the credit memo number. Use the 'Formal Credit Notification' email
            template."
            """, invoicePlugins),
        "LOGISTICS" => await HostAgentFactory.CreateHostAgentAsync(
            agentType, modelId, apiKey, "LogisticsAgent",
            """
            You specialize in handling queries related to logistics.
            
            Always reply with exactly:
            
            Shipment number: SHPMT-SAP-001
            Item: TSHIRT-RED-L
            Quantity: 900
            """, invoicePlugins),
        _ => throw new ArgumentException($"Unsupported agent type: {agentType}"),
    };
}
else
{
    Console.Error.WriteLine("Either  A2AServer:ApiKey or A2AServer:ConnectionString must be provided");
}

app.MapA2A(hostAgent!.TaskManager!, "");

await app.RunAsync();
