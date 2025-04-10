// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using ProcessWithCloudEvents.Grpc.Clients;
using ProcessWithCloudEvents.Grpc.Extensions;
using ProcessWithCloudEvents.Grpc.Options;
using ProcessWithCloudEvents.Grpc.Services;

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

var openAIOptions = config.GetValid<OpenAIOptions>(OpenAIOptions.SectionName);

// Configure the Kernel with DI. This is required for dependency injection to work with processes.
builder.Services.AddKernel();
builder.Services.AddOpenAIChatCompletion(openAIOptions.ChatModelId, openAIOptions.ApiKey);

builder.Services.AddSingleton<DocumentGenerationService>();
// Injecting SK Process custom grpc client IExternalKernelProcessMessageChannel implementation
builder.Services.AddSingleton<IExternalKernelProcessMessageChannel, DocumentGenerationGrpcClient>();

// Configure Dapr
builder.Services.AddActors(static options =>
{
    // Register the actors required to run Processes
    options.AddProcessActors();
});

// Enabling CORS for grpc-web when using webApp as client, remove if not needed
builder.Services.AddCors(o => o.AddPolicy("AllowAll", builder =>
{
    builder.AllowAnyOrigin()
            .AllowAnyMethod()
            .AllowAnyHeader();
}));

// Add grpc related services.
builder.Services.AddGrpc();
builder.Services.AddGrpcReflection();

var app = builder.Build();

app.UseCors();

// Grpc services mapping
// Enabling grpc-web, remove if not needed
app.UseGrpcWeb();
// Enabling CORS for grpc-web, remove if not needed
app.MapGrpcReflectionService().RequireCors("AllowAll");
app.MapGrpcService<DocumentGenerationService>().EnableGrpcWeb().RequireCors("AllowAll");

// Dapr actors related mapping
app.MapActorsHandlers();
app.Run();
