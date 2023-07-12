// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Services.Configuration;
using Microsoft.SemanticKernel.Services.Diagnostics;
using Microsoft.SemanticKernel.Services.SemanticMemory.WebService;
using Microsoft.SemanticKernel.Services.Storage.Pipeline;

// ********************************************************
// ************** SETUP ***********************************
// ********************************************************

WebApplicationBuilder builder = WebApplication.CreateBuilder(args);

SKMemoryConfig config = builder.Services.UseConfiguration(builder.Configuration);

builder.Logging.ConfigureLogger();
builder.Services.UseContentStorage(config);
builder.Services.UseOrchestrator(config);

if (config.OpenApiEnabled)
{
    builder.Services.AddEndpointsApiExplorer();
    builder.Services.AddSwaggerGen();
}

WebApplication app = builder.Build();

if (config.OpenApiEnabled)
{
    // URL: http://localhost:9001/swagger/index.html
    app.UseSwagger();
    app.UseSwaggerUI();
}

DateTimeOffset start = DateTimeOffset.UtcNow;

// ********************************************************
// ************** ENDPOINTS *******************************
// ********************************************************

// Simple ping endpoint
app.MapGet("/", () => Results.Ok("Ingestion service is running. " +
                                 "Uptime: " + (DateTimeOffset.UtcNow.ToUnixTimeSeconds() - start.ToUnixTimeSeconds()) + " secs"));

// File upload endpoint
app.MapPost("/upload", async Task<IResult> (
    HttpRequest request,
    IPipelineOrchestrator orchestrator,
    ILogger<Program> log) =>
{
    log.LogTrace("New upload request");

    // Note: .NET doesn't yet support binding multipart forms including data and files
    (UploadRequest input, bool isValid, string errMsg) = await UploadRequest.BindHttpRequestAsync(request);

    if (!isValid)
    {
        log.LogError(errMsg);
        return Results.BadRequest(errMsg);
    }

    log.LogInformation("Queueing upload of {0} files for further processing [request {1}]", input.Files.Count(), input.RequestId);
    var containerId = $"usr.{input.UserId}.op.{input.RequestId}";

    // Define all the steps in the pipeline
    var pipeline = orchestrator
        .PrepareNewFileUploadPipeline(containerId, input.UserId, input.VaultIds, input.Files)
        .Then("extract")
        .Then("partition")
        .Then("index")
        .Build();

    try
    {
        await orchestrator.RunPipelineAsync(pipeline);
    }
#pragma warning disable CA1031 // Must catch all to log and keep the process alive
    catch (Exception e)
    {
        app.Logger.LogError(e, "Pipeline start failed");
        return Results.Problem(
            title: "Upload failed",
            detail: e.Message,
            statusCode: 503);
    }
#pragma warning restore CA1031

    return Results.Accepted($"/upload-status?id={pipeline.Id}", new
    {
        Id = pipeline.Id,
        Message = "Upload completed, pipeline started",
        Count = input.Files.Count()
    });
});

app.Logger.LogInformation(
    "Starting web service, Log Level: {0}, .NET Env: {1}, Orchestration: {2}",
    app.Logger.GetLogLevelName(),
    Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT"),
    config.Orchestration.Type);

app.Run();
