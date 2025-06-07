// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.SignalR;
using Microsoft.SemanticKernel;
using ProcessFramework.Aspire.SignalR.ProcessOrchestrator.Models;
using ProcessFramework.SignalR;

var builder = WebApplication.CreateBuilder(args);

AppContext.SetSwitch("Microsoft.SemanticKernel.Experimental.GenAI.EnableOTelDiagnosticsSensitive", true);

builder.AddServiceDefaults();
builder.AddAzureOpenAIClient("openAiConnectionName");
builder.Services.AddSingleton<IExternalKernelProcessMessageChannel, LocalEventProxyChannel>();
builder.Services.AddKernel().AddAzureOpenAIChatCompletion("gpt-4o");
builder.Services.AddSignalR(options =>
{
    options.EnableDetailedErrors = true;
    options.MaximumReceiveMessageSize = 1024 * 1024 * 10; // 10 MB
});
// Configure Dapr
builder.Services.AddActors(static options =>
{
    // Register the actors required to run Processes
    options.AddProcessActors();
});
builder.Services.AddCors(options =>
{
    options.AddPolicy(name: "AllowAll",
    policy =>
    {
        policy.WithOrigins("http://localhost:5173") // Replace with your frontend's URL
            .AllowAnyMethod()
            .AllowAnyHeader()
            .AllowCredentials();
    });
});

var app = builder.Build();

app.UseCors("AllowAll");

// app.UseHttpsRedirection();

app.MapPost("/api/generate-doc", async (Kernel kernel, IExternalKernelProcessMessageChannel? externalMessageChannel, [FromBody] DocumentGenerationRequest request) =>
{
    var processId = string.IsNullOrEmpty(request.ProcessId) ? Guid.NewGuid().ToString() : request.ProcessId;
    var process = DocumentGenerationProcess.CreateProcessBuilder().Build();

    var processEvent = new KernelProcessEvent()
    {
        Id = DocumentGenerationProcess.DocGenerationEvents.StartDocumentGeneration,
        // The object ProductInfo is sent because this is the type the GatherProductInfoStep is expecting
        Data = new ProductInfo() { Title = request.Title, Content = request.Content, UserInput = request.UserDescription },
    };

    var processContext = await process.StartAsync(
        processEvent,
        processId);

    return new ProcessData { ProcessId = processId };
})
.WithName("GenerateDocument");

app.MapPost("/api/reviewed-doc", async (Kernel kernel, IExternalKernelProcessMessageChannel? externalMessageChannel, [FromBody] DocumentGenerationRequest request) =>
{
    var process = DocumentGenerationProcess.CreateProcessBuilder().Build();

    KernelProcessEvent processEvent;
    if (request.DocumentationApproved)
    {
        processEvent = new()
        {
            Id = DocumentGenerationProcess.DocGenerationEvents.UserApprovedDocument,
            Data = true,
        };
    }
    else
    {
        processEvent = new()
        {
            Id = DocumentGenerationProcess.DocGenerationEvents.UserRejectedDocument,
            Data = request.Reason,
        };
    }

    var processContext = await process.StartAsync(processEvent, request.ProcessId);

    return Results.Ok("Process completed successfully");
})
.WithName("ReviewDocument");

app.MapDefaultEndpoints();

app.MapHub<MyHub>("/pfevents", options =>
{
    options.Transports = Microsoft.AspNetCore.Http.Connections.HttpTransportType.WebSockets;
});

app.MapActorsHandlers();
app.Run();

public class MyHub : Hub
{
    public override async Task OnConnectedAsync()
    {
        await base.OnConnectedAsync();
    }

    public override async Task OnDisconnectedAsync(Exception? exception)
    {
        await base.OnDisconnectedAsync(exception);
    }

#pragma warning disable IDE1006
    public async Task RequestUserReview(KernelProcessProxyMessage eventData)
    {
        var requestDocument = eventData.EventData!.ToObject() as DocumentInfo;
        await Clients.All.SendAsync("RequestUserReview", new
        {
            Title = requestDocument!.Title,
            AssistantMessage = "Document ready for user revision. Approve or reject document",
            Content = requestDocument.Content,
            ProcessData = new { ProcessId = eventData.ProcessId }
        });
    }

    public async Task PublishDocumentation(KernelProcessProxyMessage eventData)
    {
        var publishedDocument = eventData.EventData!.ToObject() as DocumentInfo;
        await Clients.All.SendAsync("PublishDocumentation", new
        {
            Title = publishedDocument!.Title,
            AssistantMessage = "Published Document Ready",
            Content = publishedDocument.Content,
            ProcessData = new { ProcessId = eventData.ProcessId }
        });
    }
}

public static class ExternalEventTopics
{
    public const string RequestMoreInfo = nameof(RequestMoreInfo);
    public const string ReturnResult = nameof(ReturnResult);
}
