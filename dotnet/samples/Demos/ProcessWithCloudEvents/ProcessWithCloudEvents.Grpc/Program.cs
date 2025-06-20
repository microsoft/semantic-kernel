// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using OpenAI;
using ProcessWithCloudEvents.Grpc.Clients;
using ProcessWithCloudEvents.Grpc.Extensions;
using ProcessWithCloudEvents.Grpc.Services;
using ProcessWithCloudEvents.Processes;
using ProcessWithCloudEvents.SharedComponents.Options;

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

// Setup for using Agent Steps in SK Process
var openAIClient = OpenAIAssistantAgent.CreateOpenAIClient(new ApiKeyCredential(openAIOptions.ApiKey));
builder.Services.AddSingleton<OpenAIClient>(openAIClient);
builder.Services.AddTransient<AgentFactory, OpenAIAssistantAgentFactory>();

// Grpc setup
builder.Services.AddSingleton<DocumentGenerationService>();
builder.Services.AddSingleton<TeacherStudentInteractionService>();
// Injecting SK Process custom grpc client IExternalKernelProcessMessageChannel implementation
// TODO: Add similar keyed singleton approach to support multiple grpc clients, for now uncomment/use only one grpc client at the time
builder.Services.AddSingleton<IExternalKernelProcessMessageChannel, DocumentGenerationGrpcClient>();
//builder.Services.AddSingleton<IExternalKernelProcessMessageChannel, TeacherStudentInteractionGrpcClient>();

// Configure Dapr
builder.Services.AddDaprKernelProcesses();
builder.Services.AddActors(static options =>
{
    // Register the actors required to run Processes
    options.AddProcessActors();
});

// Register the processes we want to run
builder.Services.AddKeyedSingleton<KernelProcess>(DocumentGenerationProcess.Key, (sp, key) =>
{
    return DocumentGenerationProcess.CreateProcessBuilder().Build();
});
builder.Services.AddKeyedSingleton<KernelProcess>(TeacherStudentProcess.Key, (sp, key) =>
{
    return TeacherStudentProcess.CreateProcessBuilder().Build();
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
app.MapGrpcService<TeacherStudentInteractionService>().EnableGrpcWeb().RequireCors("AllowAll");

// Dapr actors related mapping
app.MapActorsHandlers();
app.Run();
