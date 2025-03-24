// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenTelemetry;
using OpenTelemetry.Exporter;
using OpenTelemetry.Logs;
using OpenTelemetry.Metrics;
using OpenTelemetry.Trace;
using ProcessFramework.Aspire.Shared;

var builder = WebApplication.CreateBuilder(args);

string otelExporterEndpoint = builder.GetConfiguration("OTEL_EXPORTER_OTLP_ENDPOINT");
string otelExporterHeaders = builder.GetConfiguration("OTEL_EXPORTER_OTLP_HEADERS");

AppContext.SetSwitch("Microsoft.SemanticKernel.Experimental.GenAI.EnableOTelDiagnosticsSensitive", true);

var loggerFactory = LoggerFactory.Create(builder =>
{
    // Add OpenTelemetry as a logging provider
    builder.AddOpenTelemetry(options =>
    {
        options.AddOtlpExporter(exporter => { exporter.Endpoint = new Uri(otelExporterEndpoint); exporter.Headers = otelExporterHeaders; exporter.Protocol = OtlpExportProtocol.Grpc; });
        // Format log messages. This defaults to false.
        options.IncludeFormattedMessage = true;
    });

    builder.AddTraceSource("Microsoft.SemanticKernel");
    builder.SetMinimumLevel(LogLevel.Information);
});

using var traceProvider = Sdk.CreateTracerProviderBuilder()
    .AddSource("Microsoft.SemanticKernel*")
    .AddOtlpExporter(exporter => { exporter.Endpoint = new Uri(otelExporterEndpoint); exporter.Headers = otelExporterHeaders; exporter.Protocol = OtlpExportProtocol.Grpc; })
    .Build();

using var meterProvider = Sdk.CreateMeterProviderBuilder()
    .AddMeter("Microsoft.SemanticKernel*")
    .AddOtlpExporter(exporter => { exporter.Endpoint = new Uri(otelExporterEndpoint); exporter.Headers = otelExporterHeaders; exporter.Protocol = OtlpExportProtocol.Grpc; })
    .Build();

builder.AddServiceDefaults();
builder.AddAzureOpenAIClient("openAiConnectionName");
builder.Services.AddSingleton(builder =>
{
    var kernelBuilder = Kernel.CreateBuilder();

    kernelBuilder.AddAzureOpenAIChatCompletion("gpt-4o", builder.GetService<AzureOpenAIClient>());

    return kernelBuilder.Build();
});

var app = builder.Build();

app.UseHttpsRedirection();

app.MapPost("/api/summary", async (Kernel kernel, SummarizeRequest summarizeRequest) =>
{
    ChatCompletionAgent summaryAgent =
    new()
    {
        Name = "SummarizationAgent",
        Instructions = "Summarize user input",
        Kernel = kernel
    };

    // Add a user message to the conversation
    var message = new ChatMessageContent(AuthorRole.User, summarizeRequest.TextToSummarize);

    // Generate the agent response(s)
    await foreach (ChatMessageContent response in summaryAgent.InvokeAsync(message).ConfigureAwait(false))
    {
        return response.Items.Last().ToString();
    }

    return null;
});

app.MapDefaultEndpoints();

app.Run();
