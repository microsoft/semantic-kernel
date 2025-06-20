// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using Microsoft.SemanticKernel;
using SemanticKernel.Process.IntegrationTests;
using SemanticKernel.Process.TestsShared.CloudEvents;

Debugger.Break();

var builder = WebApplication.CreateBuilder(args);

// Configure logging
builder.Services.AddLogging((logging) =>
{
    logging.AddConsole();
    logging.AddDebug();
});

// Configure the Kernel with DI. This is required for dependency injection to work with processes.
builder.Services.AddKernel();

// Configure IExternalKernelProcessMessageChannel used for testing purposes
builder.Services.AddSingleton<IExternalKernelProcessMessageChannel>(MockCloudEventClient.Instance);
builder.Services.AddSingleton(MockCloudEventClient.Instance);

// Configure the Process Framework and Dapr
builder.Services.AddDaprKernelProcesses();
builder.Services.AddActors(static options =>
{
    // Register the actors required to run Processes
    options.AddProcessActors();
    options.Actors.RegisterActor<HealthActor>();
});

var process = ProcessResources.GetCStepProcess();
builder.Services.AddKeyedSingleton<KernelProcess>(process.State.StepId, (sp, key) =>
{
    return process;
});

// Register our processes
builder.Services.AddSingleton<DaprKernelProcessFactory>();

builder.Services.AddControllers().AddJsonOptions(options =>
{
    options.JsonSerializerOptions.TypeInfoResolver = new ProcessStateTypeResolver<KickoffStep>();
});

var app = builder.Build();

app.MapControllers();
app.MapActorsHandlers();

try
{
    app.Run();
}
catch (Exception)
{
    throw;
}
