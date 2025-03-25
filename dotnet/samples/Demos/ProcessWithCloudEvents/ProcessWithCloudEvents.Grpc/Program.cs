// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using ProcessWithCloudEvents.Grpc.Services;
using ProcessWithCloudEvents.Grpc.Clients;

var builder = WebApplication.CreateBuilder(args);

var config = new ConfigurationBuilder()
    .AddUserSecrets<Program>()
    .AddEnvironmentVariables()
    .Build();

// Configure logging
builder.Services.AddLogging((logging) =>
{
    logging.AddConsole();
    logging.AddDebug();
});

// Configure the Kernel with DI. This is required for dependency injection to work with processes.
builder.Services.AddKernel();

//var openAIOptions = config.GetValid<OpenAIOptions>(OpenAIOptions.SectionName);
//builder.Services.AddOpenAIChatCompletion(openAIOptions.ChatModelId, openAIOptions.ApiKey);
builder.Services.AddSingleton<DocumentGenerationService>();
// Injecting SK Process custom grpc client IExternalKernelProcessMessageChannel implementation
builder.Services.AddSingleton<IExternalKernelProcessMessageChannel, DocumentGenerationGrpcClient>();

// Configure Dapr
builder.Services.AddActors(static options =>
{
    // Register the actors required to run Processes
    options.AddProcessActors();
});

// Add grpc related services.
builder.Services.AddGrpc();
builder.Services.AddGrpcReflection();

var app = builder.Build();

// Grpc services mapping
app.MapGrpcReflectionService();
app.MapGrpcService<DocumentGenerationService>();

// Dapr actors related mapping
app.MapActorsHandlers();
app.Run();
