// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;
using OpenAI;
using ProcessWithCloudEvents.Grpc.Clients;
using ProcessWithCloudEvents.Grpc.Extensions;
using ProcessWithCloudEvents.Grpc.LocalRuntime.Services;
using ProcessWithCloudEvents.Processes;
using ProcessWithCloudEvents.SharedComponents.Options;
using ProcessWithCloudEvents.SharedComponents.Storage;

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

// Since we have multiple grpc clients, we need to register them as keyed singletons so then we can access them respetively in each service by key
builder.Services.AddKeyedSingleton<IExternalKernelProcessMessageChannel>(DocumentGenerationGrpcClient.Key, (sp, key) =>
{
    return new DocumentGenerationGrpcClient();
});
builder.Services.AddKeyedSingleton<IExternalKernelProcessMessageChannel>(TeacherStudentInteractionGrpcClient.Key, (sp, key) =>
{
    return new TeacherStudentInteractionGrpcClient();
});

// Configuring Processes to be used in this App
builder.Services.AddSingleton<IReadOnlyDictionary<string, KernelProcess>>(sp =>
{
    var processes = new Dictionary<string, KernelProcess>
    {
        { DocumentGenerationProcess.Key, DocumentGenerationProcess.CreateProcessBuilder().Build() },
        { TeacherStudentProcess.Key, TeacherStudentProcess.CreateProcessBuilder().Build() }
    };
    return processes;
});

// Registering storage used for persisting process state with Local Runtime
string tempDirectoryPath = Path.Combine(Path.GetTempPath(), "MySKProcessStorage");
var storageInstance = new JsonFileStorage(tempDirectoryPath);
builder.Services.AddSingleton<IProcessStorageConnector>(storageInstance);

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

app.Run();
