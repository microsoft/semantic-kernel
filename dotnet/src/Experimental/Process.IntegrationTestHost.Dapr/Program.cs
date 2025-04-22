// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process;
using SemanticKernel.Process.IntegrationTests;
using SemanticKernel.Process.TestsShared.CloudEvents;

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

builder.Services.AddKeyedSingleton<KernelProcess>("cStep", (sp, key) =>
{
    return ProcessResources.GetCStepProcess();
});

// Register our processes
builder.Services.AddSingleton<DaprKernelProcessFactory2>();

builder.Services.AddControllers().AddJsonOptions(options =>
{
    options.JsonSerializerOptions.TypeInfoResolver = new ProcessStateTypeResolver<KickoffStep>();
});

var app = builder.Build();

app.MapControllers();
app.MapActorsHandlers();
app.Run();
